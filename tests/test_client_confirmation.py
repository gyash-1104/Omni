"""Client-facing confirmation message tests."""
from datetime import datetime

from backend.schemas.summary import ProjectSummary


def test_client_confirmation_excludes_internal_summary_fields():
    summary = ProjectSummary(
        session_id="wa_test",
        generated_at=datetime.utcnow(),
        next_step="Call client tomorrow at 8 PM",
        project_overview="3BHK interior renovation in Bengaluru with modular kitchen.",
        scope_of_work=["Modular kitchen", "Living room false ceiling"],
        client_requirements="Minimal Japandi style with ample storage.",
        technical_specs="1200 sqft · 3BHK",
        timeline="3 months from April 2026",
        special_considerations="Vastu compliance required.",
        estimated_scope="Budget: ₹15L",
        design_direction="Japandi-inspired minimal home.",
        execution_readiness="Possession expected next month.",
        enquiry_snapshot={
            "service_category": "home_interiors",
            "property_location": "whitefield",
            "city": "bengaluru",
            "assigned_consultant": "aadhya",
        },
    )

    text = summary.client_confirmation_text()

    assert "TatvaOps" in text
    assert "Your enquiry has been successfully received" in text
    assert "Building Better. Together." in text
    assert "Overview" not in text
    assert "Scope" not in text
    assert "Requirements" not in text
    assert "Specs" not in text
    assert "Timeline" not in text
    assert "Budget" not in text
    assert "Japandi" not in text
    assert "Aadhya" in text
    assert "Interiors" in text
    assert "Whitefield" in text
