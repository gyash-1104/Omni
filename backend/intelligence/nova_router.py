"""
EVA receptionist: service menu, intent detection, consultant handoff.
"""
from __future__ import annotations
import re
from typing import Optional, Tuple

from backend.schemas.service import (
    ServiceCategory,
    SERVICE_MENU,
    SERVICE_WHATSAPP_LABELS,
    SERVICE_MORE_VALUE,
    SERVICE_MORE_LABEL,
    WHATSAPP_SERVICE_LIST_ROWS,
    CONSULTANT_IDS,
)
from backend.schemas.session import Session, ConversationStage, MessageRole
from backend.intelligence.consultants.registry import get_opening_message, get_service_label
from backend.intelligence.consultants.personas import PERSONAS

EVA_WELCOME = """Hi 👋

I'm EVA, your TatvaOps assistant.

TatvaOps helps homeowners build, renovate, and upgrade their homes with trusted experts, transparent workflows, and real-time project support.

I’ll guide you step-by-step and connect you with the right specialist for your project ✨"""

def _build_service_menu_prompt() -> str:
    lines = ["Which TatvaOps service do you need?", ""]
    for num, _cat, label, _consultant in SERVICE_MENU:
        lines.append(f"• {label}")
    lines.extend(["", "Reply with the service name or number (1–11) from the list."])
    return "\n".join(lines)


SERVICE_MENU_PROMPT = _build_service_menu_prompt()

# Keywords / numbers -> service
_ROUTE_MAP: list[tuple[re.Pattern, ServiceCategory]] = []
for num, cat, label, _consultant in SERVICE_MENU:
    keywords = [str(num), label.lower()]
    if cat == ServiceCategory.HOME_INTERIORS:
        keywords.extend(["interior", "interiors", "home interior", "aadhya"])
    elif cat == ServiceCategory.RESIDENTIAL_CONSTRUCTION:
        keywords.extend(["construction", "build", "house", "aravind"])
    elif cat == ServiceCategory.PAINTING_WATERPROOFING:
        keywords.extend(["paint", "painting", "waterproof", "waterproofing", "manjunath"])
    elif cat == ServiceCategory.ELECTRICAL:
        keywords.extend(["electrical", "electric", "wiring", "vivek"])
    elif cat == ServiceCategory.PLUMBING:
        keywords.extend(["plumbing", "plumber", "leak", "pipe", "suresh"])
    elif cat == ServiceCategory.SOLAR:
        keywords.extend(["solar", "solar services", "rooftop", "panel", "kavya"])
    elif cat == ServiceCategory.HOME_AUTOMATION:
        keywords.extend(["automation", "smart home", "iot", "riya"])
    elif cat == ServiceCategory.EVENT_MANAGEMENT:
        keywords.extend(["event", "wedding", "party", "corporate event", "meera"])
    elif cat == ServiceCategory.PROPERTY_DEVELOPMENT:
        keywords.extend(["property development", "developer", "layout", "jd", "jv", "vikram"])
    elif cat == ServiceCategory.FARM_INFRASTRUCTURE:
        keywords.extend(
            ["farm infrastructure", "farm setup", "farm infrastructure setup", "polyhouse", "greenhouse", "livestock", "anil"]
        )
    elif cat == ServiceCategory.IRRIGATION_AUTOMATION:
        keywords.extend(["irrigation", "drip", "sprinkler", "fertigation", "deepak"])
    pattern = re.compile("|".join(re.escape(k) for k in keywords), re.I)
    _ROUTE_MAP.append((pattern, cat))


def is_service_more_choice(user_message: str) -> bool:
    """Match list tap id, payload, or visible row title for *View more*."""
    raw = (user_message or "").strip().lower()
    if not raw:
        return False
    normalized = raw.replace("-", "_").replace(" ", "_")
    if SERVICE_MORE_VALUE in normalized or normalized.endswith("service_more"):
        return True
    # Visible WhatsApp row title when ListId is not forwarded
    plain = raw.replace("➡️", "").replace("→", "").strip()
    if "view more" in plain:
        return True
    more_label = SERVICE_MORE_LABEL.lower().strip()
    if more_label and more_label in plain:
        return True
    # Legacy label from older sessions
    if "more" in plain and ("6" in plain or "11" in plain):
        return True
    return False


def is_service_more_selection(
    *,
    list_id: str = "",
    button_payload: str = "",
    button_text: str = "",
    user_message: str = "",
) -> bool:
    for part in (list_id, button_payload, button_text, user_message):
        if part and is_service_more_choice(part):
            return True
    return False


def _service_list_options(rows: list[tuple]) -> list[dict]:
    return [
        {
            "label": SERVICE_WHATSAPP_LABELS.get(cat, label),
            "whatsapp_label": SERVICE_WHATSAPP_LABELS.get(cat, label),
            "value": cat.value,
        }
        for _num, cat, label, _consultant in rows
    ]


def detect_service(user_message: str) -> Optional[ServiceCategory]:
    text = user_message.strip().lower()
    if not text:
        return None
    if is_service_more_choice(text):
        return None
    # Twilio list-picker IDs can arrive like "nova__home_interiors"
    if "__" in text and not text.startswith(SERVICE_MORE_VALUE):
        text = text.split("__", 1)[-1]
    slug = text.replace("-", "_").replace(" ", "_")
    if slug == SERVICE_MORE_VALUE or slug.endswith("service_more"):
        return None
    for cat in ServiceCategory:
        if slug == cat.value:
            return cat
    text = text.replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(SERVICE_MENU):
            return SERVICE_MENU[idx][1]
    for pattern, category in _ROUTE_MAP:
        if pattern.search(text):
            return category
    return None


def get_consultant_display_name(category: ServiceCategory) -> str:
    for _n, cat, _label, name in SERVICE_MENU:
        if cat == category:
            return name
    return "our specialist"


def _attach_service_list_sid(step: dict) -> dict:
    from backend.config import get_settings

    cfg = get_settings()
    sid = (cfg.twilio_service_selection_content_sid or "").strip()
    if sid:
        step["twilio_content_sid"] = sid
    return step


def _service_page1_count() -> int:
    """Rows on page 1: (list capacity − 1) for *More*, e.g. 5 + More when capacity is 6."""
    return max(1, WHATSAPP_SERVICE_LIST_ROWS - 1)


def service_selection_page1_step() -> dict:
    """First list: services 1–5 + *View more* (fits 6-row Twilio template)."""
    rows = SERVICE_MENU[:_service_page1_count()]
    options = _service_list_options(rows)
    options.append({"label": SERVICE_MORE_LABEL, "whatsapp_label": SERVICE_MORE_LABEL, "value": SERVICE_MORE_VALUE})
    step: dict = {
        "id": "service_selection_p1",
        "stage": "service_selection",
        "type": "mcq",
        "field": "service_category",
        "prompt": (
            "Great — your details are saved.\n\n"
            "Which TatvaOps service do you need?"
        ),
        "twilio_list_prompt": "Choose your service",
        "options": options,
        "use_dynamic_list": True,
        "require_content_variables": True,
        "twilio_list_slots": WHATSAPP_SERVICE_LIST_ROWS,
    }
    return _attach_service_list_sid(step)


def service_selection_page2_step() -> dict:
    """Second list: services 6–11 (six rows)."""
    rows = SERVICE_MENU[_service_page1_count():]
    options = _service_list_options(rows)
    step: dict = {
        "id": "service_selection_p2",
        "stage": "service_selection",
        "type": "mcq",
        "field": "service_category",
        "prompt": "Choose your service (6–11) from the list below.",
        "twilio_list_prompt": "Services 6–11",
        "options": options,
        "use_dynamic_list": True,
        "require_content_variables": True,
        "twilio_list_slots": WHATSAPP_SERVICE_LIST_ROWS,
    }
    return _attach_service_list_sid(step)


def get_service_selection_outbound_step(session) -> dict:
    page = int((session.flow_state or {}).get("service_list_page") or 1)
    if page >= 2:
        return service_selection_page2_step()
    return service_selection_page1_step()


def service_selection_step() -> dict:
    return service_selection_page1_step()


def edit_service_selection_step() -> dict:
    """
    Service picker during Edit Details — plain-text bullets only.
    Must not use field=service_category or the EVA welcome Twilio template is sent.
    """
    return {
        "id": "edit_service_selection",
        "type": "mcq",
        "field": "__edit_service__",
        "prompt": "Please choose the updated TatvaOps service:",
        "options": _service_list_options(list(SERVICE_MENU)),
    }


def handle_eva_turn(session: Session, user_message: str) -> Tuple[str, bool]:
    """
    Process a message while in EVA routing stage.
    Returns (response_text, routed_to_consultant).
    """
    if session.conversation_stage != ConversationStage.ROUTING:
        return "", False

    category = detect_service(user_message)
    if category is None:
        has_assistant = any(
            m.role == MessageRole.ASSISTANT for m in session.conversation_history
        )
        if not has_assistant:
            return EVA_WELCOME, False
        return (
            "I didn't quite catch which service you need. "
            "Please reply with a number from 1 to 11, or the service name "
            "(e.g. Home Interiors, Solar, Electrical).",
            False,
        )

    consultant_id = CONSULTANT_IDS[category]
    consultant_name = get_consultant_display_name(category)
    service_label = get_service_label(category)

    session.service_category = category
    session.active_consultant = consultant_id
    session.conversation_stage = ConversationStage.DISCOVERY
    session.extracted_fields["service_category"] = category.value

    handoff = (
        f"Perfect ✨\n"
        f"I'm connecting you with {consultant_name}, our {service_label} specialist.\n\n"
        f"{get_opening_message(consultant_id)}"
    )
    session.add_message(MessageRole.ASSISTANT, handoff)
    return handoff, True


def needs_eva(session: Session) -> bool:
    return (
        session.active_consultant is None
        or session.conversation_stage == ConversationStage.ROUTING
    )
