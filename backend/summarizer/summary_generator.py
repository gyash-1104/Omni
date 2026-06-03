"""
Project Summary Generator — structured sections from qualification flow data.
Uses Gemini for narrative polish; fallbacks use collected extracted_fields.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from backend.schemas.session import Session
from backend.schemas.summary import ProjectSummary
from backend.intelligence.gemini_engine import get_gemini_engine
from backend.intelligence.qualification_builder import SECTION_TITLES
from backend.intelligence.display_labels import display_label, budget_field_for_service, prompt_to_client_label, _load_flow_steps
from backend.utils.logger import log_event


SECTION_FIELD_MAP = {
    "client_details": [
        "client_name", "phone_number", "city", "email", "property_location",
        "preferred_contact_time", "service_category", "assigned_consultant",
    ],
    "service_questionnaire": ["service_q1", "service_q2", "service_q3", "service_q4"],
    "attachments": ["attachments"],
}


SUMMARY_GENERATION_PROMPT = """
You are preparing a concise TatvaOps sales briefing note.

STRUCTURED ENQUIRY DATA (by section):
{enquiry_data}

ATTACHMENTS ON FILE: {attachment_summary}

Generate a concise, practical project summary for CRM handoff.
Avoid generic AI filler and avoid dramatic language.
Return ONLY valid JSON with these exact keys:

{{
  "next_step": "One clear sales follow-up action (include preferred contact time if known)",
  "project_overview": "1-2 short sentences with service, property, location, and budget/context",
  "scope_of_work": ["bullet", "items", "for", "TatvaOps", "execution"],
  "client_requirements": "Short paragraph: priorities and must-haves",
  "technical_specs": "Measurable specs: area, rooms, utilities, floor plan status",
  "timeline": "Start preference, completion expectation, urgency, milestones",
  "special_considerations": "Key constraints or considerations only",
  "attachments_summary": "List what was uploaded or note if skipped / pending",
  "estimated_scope": "Budget range and project scale in one line",
  "design_direction": "One short practical direction line",
  "execution_readiness": "One short readiness line"
}}
"""


class SummaryGenerator:

    def __init__(self):
        self.engine = get_gemini_engine()

    async def generate(self, session: Session) -> ProjectSummary:
        enquiry_data = self._format_sectioned_data(session)
        attachment_summary = self._format_attachments(session)
        prompt = SUMMARY_GENERATION_PROMPT.format(
            enquiry_data=enquiry_data,
            attachment_summary=attachment_summary,
        )

        raw = await self.engine.extract_json(
            session_id=session.session_id,
            extraction_prompt=prompt,
        )

        summary = ProjectSummary(
            session_id=session.session_id,
            generated_at=datetime.utcnow(),
            next_step=raw.get("next_step", self._default_next_step(session)),
            project_overview=raw.get("project_overview", self._build_fallback_overview(session)),
            scope_of_work=raw.get("scope_of_work", self._build_fallback_scope(session)),
            client_requirements=raw.get("client_requirements", self._build_fallback_requirements(session)),
            technical_specs=raw.get("technical_specs", self._build_technical_specs(session)),
            timeline=raw.get("timeline", self._build_fallback_timeline(session)),
            special_considerations=raw.get("special_considerations", self._build_special_notes(session)),
            attachments_summary=raw.get("attachments_summary", attachment_summary),
            estimated_scope=raw.get("estimated_scope", self._build_estimated_scope(session)),
            design_direction=raw.get("design_direction", "Tailored execution aligned with client preferences and site conditions."),
            execution_readiness=raw.get("execution_readiness", "Ready for internal review and client follow-up."),
            enquiry_snapshot=session.extracted_fields,
        )

        await log_event(
            "SUMMARY_GENERATED",
            session_id=session.session_id,
            data={"project_overview": summary.project_overview[:120]},
        )
        return summary

    def _format_sectioned_data(self, session: Session) -> str:
        ef = session.extracted_fields
        blocks: list[str] = []
        for section_key, fields in SECTION_FIELD_MAP.items():
            title = SECTION_TITLES.get(section_key, section_key)
            lines = [f"## {title}"]
            for f in fields:
                if f in ef and ef[f] not in ("", None):
                    val = ef[f]
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val)
                    lines.append(f"  {f}: {val}")
            if len(lines) > 1:
                blocks.append("\n".join(lines))
        return "\n\n".join(blocks) if blocks else "  (minimal data collected)"

    def _format_attachments(self, session: Session) -> str:
        if session.attachments:
            names = ", ".join(a.file_name for a in session.attachments)
            return f"{len(session.attachments)} file(s): {names}"
        ef = session.extracted_fields.get("attachments")
        if ef == "skipped":
            return "Client skipped uploads at qualification step."
        return "No files uploaded yet."

    def _default_next_step(self, session: Session) -> str:
        ef = session.extracted_fields
        name = ef.get("client_name", "client")
        when = ef.get("preferred_contact_time", "business hours")
        return f"Call {name} during {when} to confirm site visit and share quotation timeline."

    def _build_fallback_overview(self, session: Session) -> str:
        ef = session.extracted_fields
        parts = [
            ef.get("service_category", ""),
            ef.get("service_q1", ""),
            ef.get("service_q2", ""),
            ef.get("service_q3", ""),
        ]
        loc = ef.get("property_location") or ef.get("city", "")
        budget = ef.get("service_q4", "")
        core = " · ".join(p for p in parts if p)
        if loc:
            core += f" at {loc}"
        if budget:
            core += f". Budget: {budget}"
        return core or "Project overview to be confirmed with client."

    def _build_fallback_scope(self, session: Session) -> list[str]:
        ef = session.extracted_fields
        service_key = session.service_category.value if session.service_category else ""
        scope: list[str] = []
        for step in _load_flow_steps(service_key):
            field = str(step.get("field") or "")
            if field not in ("service_q1", "service_q2", "service_q3") or not ef.get(field):
                continue
            label = prompt_to_client_label(str(step.get("prompt") or field))
            val = display_label(field, ef[field], service_category=service_key)
            scope.append(f"{label}: {val}")
        return scope or ["Scope to be confirmed on site visit"]

    def _build_fallback_requirements(self, session: Session) -> str:
        ef = session.extracted_fields
        parts = []
        if ef.get("service_q4"):
            parts.append(f"Description: {ef['service_q4']}")
        return ". ".join(parts) if parts else "Client requirements captured during qualification."

    def _build_technical_specs(self, session: Session) -> str:
        ef = session.extracted_fields
        parts = [ef.get("service_q1", ""), ef.get("service_q2", ""), ef.get("service_q3", "")]
        return " · ".join(str(p) for p in parts if p) or "Technical specs pending site survey"

    def _build_fallback_timeline(self, session: Session) -> str:
        ef = session.extracted_fields
        parts = [ef.get("preferred_contact_time", ""), ef.get("service_q4", "")]
        return " → ".join(p for p in parts if p) or "Timeline to be confirmed"

    def _build_special_notes(self, session: Session) -> str:
        ef = session.extracted_fields
        parts = [ef.get("service_q4", "")]
        return "; ".join(str(p) for p in parts if p) or "No special considerations noted."

    def _build_estimated_scope(self, session: Session) -> str:
        ef = session.extracted_fields
        service_key = session.service_category.value if session.service_category else ""
        parts: list[str] = []
        budget_field = budget_field_for_service(service_key) if service_key else None
        if budget_field and ef.get(budget_field):
            parts.append(
                f"Budget/scale: {display_label(budget_field, ef[budget_field], service_category=service_key)}"
            )
        if ef.get("service_q4"):
            parts.append(f"Notes: {str(ef['service_q4'])[:80]}")
        if not parts:
            for field in ("service_q1", "service_q2", "service_q3"):
                if ef.get(field):
                    parts.append(
                        f"{display_label(field, ef[field], service_category=service_key)}"
                    )
        return " | ".join(parts) if parts else "Scale and budget to be confirmed on consultation"


_generator: Optional[SummaryGenerator] = None


def get_summary_generator() -> SummaryGenerator:
    global _generator
    if _generator is None:
        _generator = SummaryGenerator()
    return _generator
