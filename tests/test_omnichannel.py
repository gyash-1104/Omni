"""Omnichannel platform tests."""
import pytest

from backend.schemas.service import ServiceCategory
from backend.schemas.session import Session, ConversationStage
from backend.intelligence.nova_router import detect_service, SERVICE_MENU_PROMPT
from backend.intelligence import hybrid_flow
from backend.intelligence import stage_engine as se
from backend.intelligence.lead_scorer import score_lead
from backend.intelligence.conversation_controller import ConversationController
from backend.agents.chat.whatsapp_handler import _is_new_enquiry_intent, _is_post_submit_polite_reply
from backend.utils.session_idle import (
    is_session_idle_expired,
    idle_timeout_notice,
    should_prepend_idle_notice,
    is_greeting_message,
)
from datetime import datetime, timedelta


def test_session_idle_expired_after_five_minutes():
    session = Session(
        session_id="wa_test",
        phone_number="whatsapp:+91999",
        channel="whatsapp",
        conversation_stage=ConversationStage.DETAIL_COLLECTION,
        last_active=datetime.utcnow() - timedelta(minutes=6),
    )
    assert is_session_idle_expired(session) is True


def test_submitted_session_not_idle_expired():
    session = Session(
        session_id="wa_test",
        phone_number="whatsapp:+91999",
        channel="whatsapp",
        conversation_stage=ConversationStage.SUMMARY_GENERATED,
        summary_generated=True,
        last_active=datetime.utcnow() - timedelta(hours=2),
    )
    assert is_session_idle_expired(session) is False


def test_idle_timeout_notice_text():
    assert "5 minutes" in idle_timeout_notice()


def test_greeting_after_idle_does_not_show_timeout_banner():
    session = Session(
        session_id="wa_test",
        phone_number="whatsapp:+91999",
        channel="whatsapp",
        conversation_stage=ConversationStage.DETAIL_COLLECTION,
        flow_state={"current_stage": "client_details"},
        turn_count=2,
        last_active=datetime.utcnow() - timedelta(minutes=10),
    )
    assert is_greeting_message("hello") is True
    assert should_prepend_idle_notice(session, "hello") is False


def test_mid_flow_answer_after_idle_shows_timeout_banner():
    session = Session(
        session_id="wa_test",
        phone_number="whatsapp:+91999",
        channel="whatsapp",
        conversation_stage=ConversationStage.DETAIL_COLLECTION,
        flow_state={"current_stage": "client_details"},
        turn_count=2,
        last_active=datetime.utcnow() - timedelta(minutes=10),
    )
    assert should_prepend_idle_notice(session, "Rahul Sharma") is True


def test_stale_intro_session_hello_no_timeout_banner():
    session = Session(
        session_id="wa_test",
        phone_number="whatsapp:+91999",
        channel="whatsapp",
        conversation_stage=ConversationStage.ROUTING,
        flow_state={"current_stage": "ava_intro"},
        last_active=datetime.utcnow() - timedelta(hours=1),
    )
    assert should_prepend_idle_notice(session, "hello") is False


def test_post_submit_message_intent():
    assert _is_post_submit_polite_reply("Thank you")
    assert not _is_new_enquiry_intent("Thank you")
    assert _is_new_enquiry_intent("Hello")
    assert _is_new_enquiry_intent("Hi there")


@pytest.mark.asyncio
async def test_first_whatsapp_message_shows_eva_intro():
    session = Session(
        session_id="wa_whatsapp:+919999999999",
        phone_number="whatsapp:+919999999999",
        channel="whatsapp",
        conversation_stage=ConversationStage.ROUTING,
    )
    controller = ConversationController()
    resp = await controller.process_message(session, "Hiii", channel="whatsapp")
    assert "I'm EVA" in resp.text
    assert "What is your full name?" in resp.text
    assert session.extracted_fields.get("client_name") != "Hiii"


@pytest.mark.asyncio
async def test_thank_you_after_submit_does_not_restart_flow():
    session = Session(
        session_id="wa_whatsapp:+919999999999",
        phone_number="whatsapp:+919999999999",
        channel="whatsapp",
        conversation_stage=ConversationStage.SUMMARY_GENERATED,
        summary_generated=True,
    )
    controller = ConversationController()
    resp = await controller.process_message(session, "Thank you", channel="whatsapp")
    assert "I'm EVA" not in resp.text
    assert "You're welcome" in resp.text
    assert session.summary_generated is True


def test_nova_detect_service_by_number():
    assert detect_service("2") == ServiceCategory.HOME_INTERIORS
    assert detect_service("5") == ServiceCategory.SOLAR


def test_stage_order_strict():
    assert se.STAGE_ORDER.index("client_details") < se.STAGE_ORDER.index("service_selection")
    assert se.STAGE_ORDER.index("project_overview") < se.STAGE_ORDER.index("timeline")
    assert se.STAGE_ORDER.index("attachments") < se.STAGE_ORDER.index("final_review")


def test_client_stage_steps_only_client_fields():
    session = Session(session_id="t", phone_number="+1", conversation_stage=ConversationStage.ROUTING)
    se.start_client_stage(session)
    steps = hybrid_flow._steps_in_current_stage(session)
    assert all(s["stage"] == "client_details" for s in steps)
    assert steps[0]["field"] == "client_name"


def test_no_sqft_in_technical_stage():
    session = Session(
        session_id="t", phone_number="+1",
        service_category=ServiceCategory.PAINTING_WATERPROOFING,
        conversation_stage=ConversationStage.DETAIL_COLLECTION,
        active_consultant="manjunath",
    )
    se.on_service_selected(session, ServiceCategory.PAINTING_WATERPROOFING)
    session.flow_state["current_stage"] = "technical_specs"
    steps = hybrid_flow._steps_in_current_stage(session)
    fields = [s["field"] for s in steps]
    assert "overview_property_size" not in fields
    assert "tech_room_configuration" in fields


def test_farm_infrastructure_four_option_mcq_uses_generic_template(monkeypatch):
    from backend.intelligence.qualification_builder import _service_questionnaire_steps
    monkeypatch.setenv("TWILIO_WHATSAPP_INTERACTIVE_CONTENT_SID", "HXgeneric4optiontemplate")
    from backend.config import get_settings
    get_settings.cache_clear()

    steps = _service_questionnaire_steps(ServiceCategory.FARM_INFRASTRUCTURE)
    q2 = next(s for s in steps if s["field"] == "service_q2")
    assert q2["twilio_content_sid"] == "HXgeneric4optiontemplate"
    assert q2["twilio_list_slots"] == 4
    assert "HXca88741e7bfefea27eead2c2e5cbc456" not in str(q2["twilio_content_sid"])


def test_farm_infrastructure_mcq_uses_whatsapp_list_template():
    from backend.intelligence.qualification_builder import _service_questionnaire_steps
    from backend.agents.chat.twilio_client import mcq_uses_interactive_delivery

    steps = _service_questionnaire_steps(ServiceCategory.FARM_INFRASTRUCTURE)
    q1 = next(s for s in steps if s["field"] == "service_q1")
    assert q1["twilio_content_sid"] == "HX02f90dcded88254d350a15410e5527ff"
    assert q1.get("require_content_variables") is True
    assert mcq_uses_interactive_delivery(q1) is True


def test_preferred_contact_time_uses_whatsapp_list_template():
    from backend.intelligence.qualification_builder import build_client_details_steps
    from backend.agents.chat.twilio_client import mcq_uses_interactive_delivery

    step = next(s for s in build_client_details_steps() if s["field"] == "preferred_contact_time")
    assert "(only if Needed)" in step["prompt"]
    assert step["twilio_content_sid"] == "HX4e36328276831fc79aa5feb83f0b86a4"
    assert step.get("require_content_variables") is True
    assert step.get("twilio_list_prompt") == step["prompt"]
    assert mcq_uses_interactive_delivery(step) is True


def test_mcq_in_current_stage_only():
    session = Session(
        session_id="t", phone_number="+1",
        service_category=ServiceCategory.ELECTRICAL,
        conversation_stage=ConversationStage.DETAIL_COLLECTION,
        active_consultant="vivek",
    )
    se.start_client_stage(session)
    for f in ["client_name", "city", "property_location", "preferred_contact_time"]:
        session.mark_field_complete(f, "x")
    session.mark_field_complete("phone_number", "+1")
    se.mark_stage_complete(session, "client_details")
    se.on_service_selected(session, ServiceCategory.ELECTRICAL)
    session.flow_state["current_stage"] = "project_overview"
    step = hybrid_flow.get_current_step(session)
    assert step is not None
    assert step["stage"] == "project_overview"


def test_lead_scorer():
    session = Session(
        session_id="test",
        phone_number="+1",
        service_category=ServiceCategory.HOME_INTERIORS,
        conversation_stage=ConversationStage.SUMMARY_GENERATED,
        summary_generated=True,
    )
    session.completed_fields = se.required_fields_for_summary()
    score, tier = score_lead(session)
    assert 0 <= score <= 100
    assert tier in ("hot", "warm", "cold")


def test_service_menu_prompt():
    assert "1." in SERVICE_MENU_PROMPT
