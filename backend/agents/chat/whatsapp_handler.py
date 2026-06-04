"""
TatvaOps – WhatsApp Webhook Handler (Twilio)
AVA routing + specialized consultants + media uploads.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks

from backend.config import get_settings
from backend.schemas.session import Session, ConversationStage
from backend.intelligence.conversation_controller import get_controller
from backend.intelligence import hybrid_flow
from backend.intelligence import edit_flow
from backend.intelligence import stage_engine as se
from backend.intelligence.nova_router import get_service_selection_outbound_step
from backend.storage.redis_store import get_session, save_session, delete_session
from backend.storage import supabase_store
from backend.storage.media_store import save_attachment
from backend.agents.chat.twilio_client import (
    enrich_whatsapp_mcq_step,
    send_whatsapp_message,
    send_whatsapp_flow,
    twiml_response,
)
from backend.agents.chat.whatsapp_interactive import build_inbound_user_message, parse_list_selection_id
from backend.utils.logger import log_event

router = APIRouter()
_settings = get_settings()


def _normalize_restart_command(message: str) -> str:
    return (message or "").strip().upper().replace(" ", "")


def _is_restart_command(message: str) -> bool:
    return _normalize_restart_command(message) == "RESTART45"


async def _handle_restart45(session_id: str, phone_number: str) -> str:
    """Clear session and return AVA welcome (dev reset)."""
    await delete_session(session_id)
    await log_event("SESSION_RESET", session_id=session_id, data={"reason": "RESTART45"})
    new_session = Session(
        session_id=session_id,
        phone_number=phone_number,
        channel="whatsapp",
        conversation_stage=ConversationStage.ROUTING,
        flow_state={"current_stage": "ava_intro", "completed_stages": [], "pending_fields": []},
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )
    await save_session(new_session)
    return "Session reset.\n\n" + hybrid_flow.first_client_message()


def _twilio_validation_url(request: Request) -> str:
    """URL Twilio signed — must match the webhook URL in Console (incl. query string)."""
    url = f"{_settings.base_url.rstrip('/')}{request.scope['path']}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return url


def _validate_twilio_signature(request: Request, form_params: dict[str, str]) -> None:
    """Validate Twilio signature. BASE_URL must match the URL set in Twilio Console."""
    token = _settings.twilio_auth_token
    if not token or token in ("your_twilio_auth_token", ""):
        return
    if _settings.environment == "development":
        return
    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    url = _twilio_validation_url(request)
    validator = RequestValidator(token)
    is_valid = validator.validate(url, form_params, signature)
    if not is_valid:
        print(f"[WhatsApp] Invalid Twilio signature for URL {url}")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
):
    # Twilio signs every POST field — pass the full form body, not a hand-picked subset.
    raw_form = await request.form()
    form_params = {k: str(v) for k, v in raw_form.items()}

    From = form_params.get("From", "")
    Body = form_params.get("Body", "")
    ButtonText = form_params.get("ButtonText")
    ButtonPayload = form_params.get("ButtonPayload")
    ListId = form_params.get("ListId")
    ListTitle = form_params.get("ListTitle")
    InteractiveData = form_params.get("InteractiveData")
    try:
        NumMedia = int(form_params.get("NumMedia") or 0)
    except ValueError:
        NumMedia = 0
    MediaUrl0 = form_params.get("MediaUrl0")
    MediaContentType0 = form_params.get("MediaContentType0")

    if not From:
        raise HTTPException(status_code=400, detail="Missing From")

    _validate_twilio_signature(request, form_params)

    phone_number = From
    resolved_list_id = parse_list_selection_id(
        list_id=ListId or "",
        button_payload=ButtonPayload or "",
        interactive_data=InteractiveData or "",
    )
    user_message = build_inbound_user_message(
        body=Body or "",
        button_text=ButtonText or "",
        list_title=ListTitle or "",
        list_id=ListId or resolved_list_id,
        button_payload=ButtonPayload or "",
        interactive_data=InteractiveData or "",
    )
    session_id = f"wa_{phone_number}"

    client_ip = request.client.host if request.client else "unknown"
    print(f"[WhatsApp] INBOUND ip={client_ip} from={From} body={user_message!r}")

    # RESTART45 — reply in TwiML immediately (does not depend on outbound Twilio API / tunnel follow-up)
    if _is_restart_command(user_message):
        if _settings.environment != "development":
            deny = "RESTART45 is only available when ENVIRONMENT=development."
            print(f"[WhatsApp] RESTART45 blocked (env={_settings.environment})")
            return Response(content=twiml_response(deny), media_type="application/xml")
        reset_msg = await _handle_restart45(session_id, phone_number)
        print(f"[WhatsApp] RESTART45 reset OK for {From}")
        return Response(content=twiml_response(reset_msg), media_type="application/xml")

    background_tasks.add_task(
        handle_whatsapp_message_bg,
        session_id,
        phone_number,
        user_message,
        NumMedia,
        MediaUrl0,
        MediaContentType0 or "",
        ButtonText or "",
        ButtonPayload or "",
        resolved_list_id,
    )

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


async def handle_whatsapp_message_bg(
    session_id: str,
    phone_number: str,
    user_message: str,
    num_media: int = 0,
    media_url: Optional[str] = None,
    media_content_type: str = "",
    button_text: str = "",
    button_payload: str = "",
    list_id: str = "",
):
    try:
        await _handle_whatsapp_message_impl(
            session_id, phone_number, user_message, num_media, media_url,
            media_content_type, button_text, button_payload, list_id,
        )
    except Exception as e:
        import traceback
        print(f"[WhatsApp] Background handler error: {e}")
        traceback.print_exc()
        await log_event("API_ERROR", session_id=session_id,
                        data={"error": str(e), "phase": "whatsapp_handler_bg"})


async def _handle_whatsapp_message_impl(
    session_id: str,
    phone_number: str,
    user_message: str,
    num_media: int = 0,
    media_url: Optional[str] = None,
    media_content_type: str = "",
    button_text: str = "",
    button_payload: str = "",
    list_id: str = "",
):
    session = await get_session(session_id)

    if session is None:
        session = Session(
            session_id=session_id,
            phone_number=phone_number,
            channel="whatsapp",
            conversation_stage=ConversationStage.ROUTING,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
        )
        await log_event("SESSION_START", session_id=session_id,
                        data={"phone": phone_number, "channel": "whatsapp"})
        await save_session(session)
        if not user_message and num_media == 0:
            await send_whatsapp_message(to=phone_number, body=hybrid_flow.first_client_message())
            return

    # Media upload handling (stage 9 — attachments, or edit-details file update)
    if num_media > 0 and media_url:
        meta = await save_attachment(session, media_url, media_content_type)
        if meta:
            hybrid_flow.init_flow(session)
            ack = f"Thank you! I received your file ({meta.file_name})."
            if edit_flow.awaiting_file_upload(session):
                reply, outbound_step, _handled = edit_flow.complete_file_upload(session)
                await save_session(session)
                await supabase_store.upsert_session_log(session)
                await send_whatsapp_message(to=phone_number, body=ack)
                await send_whatsapp_flow(to=phone_number, body=reply, step=outbound_step)
                return
            if hybrid_flow.pending_file_upload(session):
                follow_up = hybrid_flow.complete_attachment_upload(session)
                await save_session(session)
                await supabase_store.upsert_session_log(session)
                await send_whatsapp_message(to=phone_number, body=f"{ack}\n\n{follow_up}")
                return
            session.mark_field_complete("has_attachments", True)
            await save_session(session)
            await send_whatsapp_message(
                to=phone_number,
                body=f"{ack} Our team will review it with your enquiry.",
            )
            return

    if not user_message:
        return

    if se.fs_current_stage(session) == "service_selection":
        print(
            f"[WhatsApp] service_selection inbound "
            f"list_id={list_id!r} body={user_message!r} payload={button_payload!r}"
        )

    controller = get_controller()
    try:
        agent_response = await controller.process_message(
            session=session,
            user_message=user_message,
            channel="whatsapp",
            button_text=button_text or None,
            button_payload=button_payload or None,
            list_id=list_id or None,
        )
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        await log_event("API_ERROR", session_id=session_id,
                        data={"error": str(e), "phase": "whatsapp_handler"})
        fallback = "Could you give me just a moment? I'm pulling your details together."
        await save_session(session)
        await send_whatsapp_message(to=phone_number, body=fallback)
        return

    await save_session(agent_response.session)
    await supabase_store.upsert_session_log(agent_response.session)

    if agent_response.summary_generated and agent_response.session.summary:
        await supabase_store.save_enquiry(agent_response.session)
        try:
            from backend.schemas.summary import ProjectSummary
            summary_obj = ProjectSummary.model_validate(agent_response.session.summary)
            await supabase_store.save_summary(summary_obj, phone_number=phone_number)
        except Exception as e:
            print(f"[WhatsApp] summary save error: {e}")

        confirmation = (agent_response.text or "").strip()
        if confirmation:
            await send_whatsapp_message(to=phone_number, body=confirmation)
        await log_event(
            "CONVERSATION_ENDED",
            session_id=session_id,
            data={"reason": "enquiry_submitted", "channel": "whatsapp"},
        )
        return

    reply = (agent_response.text or "").strip()
    if not reply:
        print(f"[WhatsApp] Empty reply for message={user_message!r}")
        reply = "Thanks — could you repeat that? Please continue with the current step."

    session_out = agent_response.session
    if edit_flow.is_active(session_out):
        outbound_step = edit_flow.get_outbound_step(session_out)
    else:
        outbound_step = hybrid_flow.get_current_step(session_out)
        if outbound_step is None and se.fs_current_stage(session_out) == "service_selection":
            outbound_step = get_service_selection_outbound_step(session_out)
            uses_list = outbound_step.get("twilio_content_sid") or outbound_step.get("use_dynamic_list")
            if not uses_list:
                menu_body = hybrid_flow.format_mcq_message(outbound_step)
                if menu_body not in reply:
                    reply = f"{reply}\n\n{menu_body}".strip() if reply else menu_body
    outbound_step = enrich_whatsapp_mcq_step(outbound_step)
    uses_interactive_list = (
        outbound_step
        and outbound_step.get("type") == "mcq"
        and (
            outbound_step.get("twilio_content_sid")
            or outbound_step.get("use_dynamic_list")
        )
    )
    if uses_interactive_list:
        # Send transition text first, then the list-picker body (like contact-time step).
        prompt_text = str(outbound_step.get("prompt", "")).strip()
        list_prompt = str(outbound_step.get("twilio_list_prompt", "")).strip()
        if reply:
            cleaned = reply
            for chunk in (prompt_text, list_prompt):
                if chunk:
                    cleaned = cleaned.replace(chunk, "").strip()
            if cleaned:
                await send_whatsapp_message(to=phone_number, body=cleaned)
        reply = list_prompt or prompt_text or "Please choose one option."
    await send_whatsapp_flow(
        to=phone_number,
        body=reply,
        step=outbound_step,
    )


@router.get("/webhook/whatsapp/health")
async def whatsapp_webhook_health():
    """Quick check that BASE_URL/tunnel points at this server."""
    return {
        "ok": True,
        "environment": _settings.environment,
        "base_url": _settings.base_url,
        "restart_command": "RESTART45 (development only)",
    }
