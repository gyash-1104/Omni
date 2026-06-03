# TatvaOps AI Omnichannel Lead Qualification System
**Nova + 6 Specialized Consultants · WhatsApp + Voice · Krsna Admin**

TatvaOps omnichannel platform (per `Omnichannel.pdf`): **Nova** greets customers and routes to specialized AI consultants (Aravind, Aadhya, Manjunath, Vivek, Kavya, Riya). Hybrid **MCQ + descriptive + file upload** flows qualify leads; **Gemini** powers conversation and summaries; **Krsna** admin monitors operations.

---

## Architecture

```
WhatsApp / Voice (Twilio / Vapi)
        ↓
Nova (routing menu 1-6)
        ↓
Specialized Consultant (6 services)
        ↓
Hybrid Flow (MCQ + descriptive + files)
        ↓
ConversationController + Gemini
        ↓
StructuredExtractor → EnquiryEngine
        ↓
SummaryGenerator + LeadScorer
        ↓
Upstash Redis + Supabase + Krsna Admin
```

### Services

| # | Service | Consultant |
|---|---------|------------|
| 1 | Residential Construction | Aravind Narayanan |
| 2 | Home Interiors | Aadhya |
| 3 | Painting & Waterproofing | Manjunath Gowda |
| 4 | Electrical Services | Vivek Shetty |
| 5 | Solar Rooftop | Kavya Nair |
| 6 | Home Automation | Riya Mehta |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key
- (Optional for full live testing): Twilio, Vapi, ElevenLabs, Upstash, Supabase accounts

---

## Quick Start

### 1. Clone & Setup

```bash
cd aadhya
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

### 4. Build & run the admin UI

```bash
cd admin-ui
npm install
npm run dev        # Development: http://localhost:5173/krsna
# OR
npm run build      # Production build → backend serves at /krsna
```

---

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | WhatsApp |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | WhatsApp |
| `TWILIO_WHATSAPP_FROM` | Twilio sandbox number | WhatsApp |
| `VAPI_API_KEY` | Vapi API key | Voice |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID | Voice |
| `UPSTASH_REDIS_REST_URL` | Upstash REST URL | Recommended |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash token | Recommended |
| `SUPABASE_URL` | Supabase project URL | Recommended |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Recommended |
| `ADMIN_PASSWORD` | Admin panel password | ✅ |
| `ADMIN_API_KEY` | Admin API key header | ✅ |

> **Without Redis/Supabase**: System falls back to in-memory storage (data lost on restart).

---

## Webhooks Setup

### WhatsApp (Twilio Sandbox)
1. Go to Twilio Console → Messaging → WhatsApp Sandbox
2. Set webhook URL: `https://your-domain/webhook/whatsapp`
3. Method: HTTP POST
4. Send "join [sandbox-keyword]" to the Twilio number on WhatsApp
5. Text the number — Aadhya will respond!

### Voice (Vapi)
1. Create a Vapi assistant at [vapi.ai](https://vapi.ai)
2. Set the server URL to: `https://your-domain/webhook/vapi`
3. Set transcriber: Deepgram · `nova-2` · `en-IN`
4. Set voice: ElevenLabs with your preferred voice ID
5. Assign a phone number to the assistant

---

## Admin Panel — /krsna

Access at: `http://localhost:8000/krsna`  
(or `http://localhost:5173/krsna` in dev mode)

**Login**: Use `ADMIN_PASSWORD` from your `.env`

| Section | Path | Description |
|---|---|---|
| Dashboard | `/krsna/dashboard` | Stats + charts |
| Sessions | `/krsna/sessions` | All active conversations |
| Session Detail | `/krsna/sessions/:id` | Chat + AI thinking trace |
| Enquiries | `/krsna/enquiries` | Structured field data |
| Summaries | `/krsna/summaries` | Generated project summaries |
| Logs | `/krsna/logs` | Structured event logs |
| Files | `/krsna/files` | WhatsApp uploads (floor plans, photos) |
| System | `/krsna/system` | API health + live feed |

---

## Supabase Schema

Run in Supabase SQL editor:

1. Base tables: `SCHEMA_SQL` in `backend/storage/supabase_store.py`
2. Omnichannel extensions: `scripts/omnichannel_schema.sql`
3. Create Storage bucket **`enquiry-files`** (public or signed URLs)

---

## Deployment (Railway / Render)

### Railway
```bash
railway login
railway init
railway up
```

Set all `.env` variables in Railway dashboard.

**Build command**: `pip install -r requirements.txt && cd admin-ui && npm install && npm run build`  
**Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Render
- Runtime: Python 3.11
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Add all env vars in Render dashboard

---

## Testing Locally (Simulated Webhooks)

```bash
# Test WhatsApp webhook
curl -X POST http://localhost:8000/webhook/whatsapp \
  -d "From=whatsapp%3A%2B919876543210&Body=Hi+I+need+interior+design+help"

# Test Vapi webhook
curl -X POST http://localhost:8000/webhook/vapi \
  -H "Content-Type: application/json" \
  -d '{"message":{"type":"transcript","role":"user","transcript":"I have a 3BHK villa in Bengaluru"},"call":{"id":"test_001","customer":{"number":"+919876543210"}}}'

# Admin API
curl http://localhost:8000/admin/dashboard \
  -H "X-Admin-Key: your_admin_api_key"

# Admin login
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"your_admin_password"}'
```

---

## Project Structure

```
aadhya/
├── backend/
│   ├── main.py                      # FastAPI app entry
│   ├── config.py                    # Pydantic settings
│   ├── agents/
│   │   ├── chat/whatsapp_handler.py # Twilio webhook
│   │   └── voice/vapi_handler.py    # Vapi webhook
│   ├── intelligence/
│   │   ├── persona.py               # Aadhya system prompts
│   │   ├── gemini_engine.py         # Gemini API wrapper
│   │   ├── conversation_controller.py # Orchestration
│   │   ├── enquiry_engine.py        # Priority field engine
│   │   └── extractor.py             # Structured extraction
│   ├── schemas/                     # Pydantic models
│   ├── summarizer/                  # Summary generator
│   ├── storage/                     # Redis + Supabase
│   ├── admin/                       # Admin API endpoints
│   └── utils/                       # Logger + retry
├── admin-ui/                        # React + Tailwind SPA
└── examples/                        # Sample conversations
```

---

*Built with ❤️ for TatvaOps · Powered by Google Gemini*
