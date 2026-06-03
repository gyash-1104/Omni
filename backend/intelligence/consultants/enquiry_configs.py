"""
Per-service primary/secondary fields and question hints.
"""
from __future__ import annotations
from backend.schemas.service import ServiceCategory

COMMON_PRIMARY = ["client_name", "city", "property_type", "budget_range", "timeline"]

ENQUIRY_CONFIG: dict[ServiceCategory, dict] = {
    ServiceCategory.HOME_INTERIORS: {
        "primary": [
            "client_name", "property_type", "city", "service_type",
            "area_sqft", "configuration", "rooms_to_design", "budget_range", "timeline",
        ],
        "secondary": [
            "design_style", "possession_status", "pooja_room", "vastu_importance",
            "kids", "pets", "floor_number",
        ],
        "hints": {
            "client_name": "Warmly ask for their name.",
            "property_type": "Ask if this is an apartment, villa, or independent house.",
            "city": "Ask which city or area the property is in.",
            "service_type": "Ask if they want full-home design, partial rooms, or renovation.",
            "area_sqft": "Ask approximate home size in square feet.",
            "configuration": "Ask BHK configuration (e.g. 2BHK, 3BHK).",
            "rooms_to_design": "Ask which rooms they want designed.",
            "budget_range": "Gently ask for a rough budget range.",
            "timeline": "Ask expected timeline or possession date.",
            "design_style": "Ask preferred interior style.",
        },
    },
    ServiceCategory.RESIDENTIAL_CONSTRUCTION: {
        "primary": [
            "client_name", "city", "property_type", "plot_size", "floors_planned",
            "construction_type", "budget_range", "timeline",
        ],
        "secondary": ["builder_preference", "parking_requirement", "vastu_importance"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask project city or locality.",
            "property_type": "Ask if plot, villa, or independent house construction.",
            "plot_size": "Ask plot dimensions or area.",
            "floors_planned": "Ask how many floors they plan to build.",
            "construction_type": "Ask if new build or extension/renovation.",
            "budget_range": "Ask approximate construction budget range.",
            "timeline": "Ask when they want to start construction.",
        },
    },
    ServiceCategory.PAINTING_WATERPROOFING: {
        "primary": [
            "client_name", "city", "property_type", "area_sqft",
            "scope_type", "surface_condition", "budget_range", "timeline",
        ],
        "secondary": ["exterior_included", "waterproofing_zones"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask city of the property.",
            "property_type": "Ask apartment, villa, or commercial.",
            "area_sqft": "Ask approximate area to be painted.",
            "scope_type": "Ask interior, exterior, or both.",
            "surface_condition": "Ask if surfaces are new or need repair.",
            "budget_range": "Ask rough budget range.",
            "timeline": "Ask when they need work completed.",
        },
    },
    ServiceCategory.ELECTRICAL: {
        "primary": [
            "client_name", "city", "property_type", "service_scope",
            "wiring_type", "budget_range", "timeline",
        ],
        "secondary": ["smart_devices", "backup_power"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask city of the property.",
            "property_type": "Ask property type.",
            "service_scope": "Ask new wiring, rewiring, or maintenance.",
            "wiring_type": "Ask residential or commercial scale.",
            "budget_range": "Ask approximate budget.",
            "timeline": "Ask preferred start timeline.",
        },
    },
    ServiceCategory.SOLAR: {
        "primary": [
            "client_name", "city", "property_type", "roof_area",
            "monthly_units", "budget_range", "timeline",
        ],
        "secondary": ["subsidy_interest", "battery_backup"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask installation city.",
            "property_type": "Ask independent house, villa, or apartment.",
            "roof_area": "Ask approximate roof area available.",
            "monthly_units": "Ask average monthly electricity units or bill.",
            "budget_range": "Ask investment budget range.",
            "timeline": "Ask when they want installation.",
        },
    },
    ServiceCategory.HOME_AUTOMATION: {
        "primary": [
            "client_name", "city", "property_type", "area_sqft",
            "automation_scope", "budget_range", "timeline",
        ],
        "secondary": ["security_priority", "voice_assistant"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask city of the home.",
            "property_type": "Ask apartment or villa.",
            "area_sqft": "Ask home size.",
            "automation_scope": "Ask lighting, security, climate, or full home.",
            "budget_range": "Ask budget range.",
            "timeline": "Ask project timeline.",
        },
    },
    ServiceCategory.PLUMBING: {
        "primary": [
            "client_name", "city", "property_type", "service_scope",
            "urgency", "budget_range", "timeline",
        ],
        "secondary": ["fixture_type", "water_source"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask city of the property.",
            "property_type": "Ask property type.",
            "service_scope": "Ask installation, leak repair, or fixtures.",
            "urgency": "Ask how urgent the issue is.",
            "budget_range": "Ask approximate budget.",
            "timeline": "Ask preferred timeline.",
        },
    },
    ServiceCategory.EVENT_MANAGEMENT: {
        "primary": [
            "client_name", "city", "event_type", "guest_count",
            "services_needed", "event_date", "budget_range",
        ],
        "secondary": ["venue_status", "theme_style"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask event city or location.",
            "event_type": "Ask wedding, corporate, or private event.",
            "guest_count": "Ask approximate guest count.",
            "services_needed": "Ask full management or specific services.",
            "event_date": "Ask preferred event date or month.",
            "budget_range": "Ask event budget range.",
        },
    },
    ServiceCategory.PROPERTY_DEVELOPMENT: {
        "primary": [
            "client_name", "city", "development_type", "project_stage",
            "investment_scale", "timeline",
        ],
        "secondary": ["land_size", "zoning_status"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask project location.",
            "development_type": "Ask residential, commercial, or mixed-use.",
            "project_stage": "Ask land, planning, or execution stage.",
            "investment_scale": "Ask expected investment scale.",
            "timeline": "Ask project timeline.",
        },
    },
    ServiceCategory.FARM_INFRASTRUCTURE: {
        "primary": [
            "client_name", "city", "infrastructure_type", "land_area",
            "utilities_available", "timeline",
        ],
        "secondary": ["crop_livestock_type"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask farm location.",
            "infrastructure_type": "Ask polyhouse, storage, or livestock shed.",
            "land_area": "Ask land area in acres.",
            "utilities_available": "Ask power and water availability.",
            "timeline": "Ask expected start timeline.",
        },
    },
    ServiceCategory.IRRIGATION_AUTOMATION: {
        "primary": [
            "client_name", "city", "irrigation_type", "crop_area",
            "water_source", "automation_level", "timeline",
        ],
        "secondary": ["current_system"],
        "hints": {
            "client_name": "Ask for their name.",
            "city": "Ask farm location.",
            "irrigation_type": "Ask drip, sprinkler, or smart system.",
            "crop_area": "Ask crops or areas to irrigate.",
            "water_source": "Ask borewell, canal, or other source.",
            "automation_level": "Ask manual vs automated requirements.",
            "timeline": "Ask installation timeline.",
        },
    },
}
