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


def test_post_submit_message_intent():
    assert _is_post_submit_polite_reply("Thank you")
    assert not _is_new_enquiry_intent("Thank you")
    assert _is_new_enquiry_intent("Hello")
    assert _is_new_enquiry_intent("Hi there")


@pytest.mark.asyncio
async def test_first_whatsapp_message_shows_ava_intro():
    session = Session(
        session_id="wa_whatsapp:+919999999999",
        phone_number="whatsapp:+919999999999",
        channel="whatsapp",
        conversation_stage=ConversationStage.ROUTING,
    )
    controller = ConversationController()
    resp = await controller.process_message(session, "Hiii", channel="whatsapp")
    assert "I'm AVA" in resp.text
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
    assert "I'm AVA" not in resp.text
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
