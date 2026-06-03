"""
TatvaOps service categories and consultant mapping (TatvaOps Enquiry Form).
"""
from __future__ import annotations
from enum import Enum


class ServiceCategory(str, Enum):
    RESIDENTIAL_CONSTRUCTION = "residential_construction"
    HOME_INTERIORS = "home_interiors"
    PAINTING_WATERPROOFING = "painting_waterproofing"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    SOLAR = "solar"
    HOME_AUTOMATION = "home_automation"
    EVENT_MANAGEMENT = "event_management"
    PROPERTY_DEVELOPMENT = "property_development"
    FARM_INFRASTRUCTURE = "farm_infrastructure"
    IRRIGATION_AUTOMATION = "irrigation_automation"


# Display order for WhatsApp / enquiry (1–11)
SERVICE_MENU = [
    (1, ServiceCategory.RESIDENTIAL_CONSTRUCTION, "🏗️ Residential Construction", "Aravind Narayanan"),
    (2, ServiceCategory.HOME_INTERIORS, "🛋️ Interiors", "Aadhya"),
    (3, ServiceCategory.PAINTING_WATERPROOFING, "🖌️ Painting", "Manjunath Gowda"),
    (4, ServiceCategory.ELECTRICAL, "⚡ Electrical Services", "Vivek Shetty"),
    (5, ServiceCategory.PLUMBING, "🔧 Plumbing Services", "Suresh Kumar"),
    (6, ServiceCategory.SOLAR, "☀️ Solar Services", "Kavya Nair"),
    (7, ServiceCategory.EVENT_MANAGEMENT, "🎪 Event Management", "Meera Iyer"),
    (8, ServiceCategory.PROPERTY_DEVELOPMENT, "🏢 Property Development", "Vikram Desai"),
    (9, ServiceCategory.HOME_AUTOMATION, "🏠 Home Automation", "Riya Mehta"),
    (10, ServiceCategory.FARM_INFRASTRUCTURE, "🌾 Farm Infrastructure Setup", "Anil Reddy"),
    (11, ServiceCategory.IRRIGATION_AUTOMATION, "💧 Irrigation Automation", "Deepak Patil"),
]

# Short labels for WhatsApp list rows (max 24 characters)
SERVICE_WHATSAPP_LABELS: dict[ServiceCategory, str] = {
    ServiceCategory.RESIDENTIAL_CONSTRUCTION: "🏗️ Residential Const.",
    ServiceCategory.HOME_INTERIORS: "🛋️ Interiors",
    ServiceCategory.PAINTING_WATERPROOFING: "🖌️ Painting",
    ServiceCategory.ELECTRICAL: "⚡ Electrical",
    ServiceCategory.PLUMBING: "🔧 Plumbing",
    ServiceCategory.SOLAR: "☀️ Solar Services",
    ServiceCategory.EVENT_MANAGEMENT: "🎪 Event Management",
    ServiceCategory.PROPERTY_DEVELOPMENT: "🏢 Property Dev.",
    ServiceCategory.HOME_AUTOMATION: "🏠 Home Automation",
    ServiceCategory.FARM_INFRASTRUCTURE: "🌾 Farm Setup",
    ServiceCategory.IRRIGATION_AUTOMATION: "💧 Irrigation",
}

# Must match Twilio list-picker row count in TWILIO_SERVICE_SELECTION_CONTENT_SID (current template: 6)
WHATSAPP_SERVICE_LIST_ROWS = 6

SERVICE_MORE_VALUE = "__service_more__"
SERVICE_MORE_LABEL = "View more"

CONSULTANT_IDS = {
    ServiceCategory.RESIDENTIAL_CONSTRUCTION: "aravind",
    ServiceCategory.HOME_INTERIORS: "aadhya",
    ServiceCategory.PAINTING_WATERPROOFING: "manjunath",
    ServiceCategory.ELECTRICAL: "vivek",
    ServiceCategory.PLUMBING: "suresh",
    ServiceCategory.SOLAR: "kavya",
    ServiceCategory.HOME_AUTOMATION: "riya",
    ServiceCategory.EVENT_MANAGEMENT: "meera",
    ServiceCategory.PROPERTY_DEVELOPMENT: "vikram",
    ServiceCategory.FARM_INFRASTRUCTURE: "anil",
    ServiceCategory.IRRIGATION_AUTOMATION: "deepak",
}
