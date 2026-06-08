"""
Session idle timeout — end in-progress chats after inactivity.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from backend.config import get_settings
from backend.schemas.session import Session, ConversationStage


def idle_timeout_minutes() -> int:
    return get_settings().session_idle_timeout_minutes


def is_session_idle_expired(session: Session) -> bool:
    """In-progress sessions expire after SESSION_IDLE_TIMEOUT_MINUTES without a message."""
    if session.summary_generated or session.conversation_stage == ConversationStage.SUMMARY_GENERATED:
        return False
    minutes = idle_timeout_minutes()
    if minutes <= 0:
        return False
    return datetime.utcnow() - session.last_active > timedelta(minutes=minutes)


def idle_timeout_notice() -> str:
    mins = idle_timeout_minutes()
    return (
        f"This chat ended after {mins} minutes of inactivity. "
        "Let's start fresh.\n\n"
    )


async def start_fresh_session(
    session_id: str,
    phone_number: str,
    *,
    channel: str = "whatsapp",
    reason: str,
) -> Session:
    """Delete stored state and persist a new empty session."""
    from backend.storage.redis_store import delete_session, save_session
    from backend.utils.logger import log_event

    await delete_session(session_id)
    await log_event(
        "SESSION_RESET",
        session_id=session_id,
        data={"reason": reason, "channel": channel},
    )
    new_session = Session(
        session_id=session_id,
        phone_number=phone_number,
        channel=channel,
        conversation_stage=ConversationStage.ROUTING,
        flow_state={"current_stage": "ava_intro", "completed_stages": [], "pending_fields": []},
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )
    await save_session(new_session)
    return new_session
