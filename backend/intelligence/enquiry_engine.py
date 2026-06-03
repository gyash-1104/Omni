"""
Dynamic enquiry engine — delegates to per-service registry config.
"""
from __future__ import annotations
from backend.schemas.session import Session
from backend.intelligence.consultants import registry


class EnquiryEngine:
    def get_next_fields(self, session: Session) -> list[str]:
        return registry.get_next_fields(session)

    def is_complete(self, session: Session) -> bool:
        return registry.is_enquiry_complete(session)

    def build_task_instruction(self, session: Session) -> str:
        return registry.build_task_instruction(session)


_engine: EnquiryEngine | None = None


def get_enquiry_engine() -> EnquiryEngine:
    global _engine
    if _engine is None:
        _engine = EnquiryEngine()
    return _engine
