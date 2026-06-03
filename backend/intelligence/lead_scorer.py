"""
Lead scoring and tiering (Omnichannel.pdf Section 12.5).
"""
from __future__ import annotations
from backend.schemas.session import Session


def score_lead(session: Session) -> tuple[int, str]:
  """Returns (score 0-100, tier: hot|warm|cold)."""
  score = 0
  pct = session.field_completion_pct
  score += int(pct * 0.5)

  if session.summary_generated:
    score += 20
  if session.attachments:
    score += 15
  if session.extracted_fields.get("budget_range"):
    score += 10
  if session.extracted_fields.get("timeline"):
    score += 5

  timeline = str(session.extracted_fields.get("timeline", "")).lower()
  if any(w in timeline for w in ("asap", "urgent", "immediately", "this month", "next month")):
    score += 10

  score = min(100, max(0, score))
  if score >= 75:
    tier = "hot"
  elif score >= 45:
    tier = "warm"
  else:
    tier = "cold"
  return score, tier


def apply_lead_score(session: Session) -> Session:
  score, tier = score_lead(session)
  session.lead_score = score
  session.lead_tier = tier
  return session
