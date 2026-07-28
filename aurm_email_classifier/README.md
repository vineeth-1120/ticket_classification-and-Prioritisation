# Aurm Email Classifier API

Automated email classification and triage system for Aurm — a safe deposit locker service for residential societies in India.

## Problem Statement

Aurm's Operations team manually reads, replies to, and tracks every customer email. As the company scales to more societies and residents, this linear effort does not scale. This API automates the **triage layer**: reading, classifying, prioritizing, and routing incoming customer emails so the right team handles the right issue at the right priority.

## Solution Overview

A FastAPI backend that receives email details via JSON, classifies the query into business-relevant categories, assigns priority and SLA, and routes to the appropriate team. The system includes:

- **LLM-powered classification** (OpenAI GPT-4o-mini) with zero-shot prompting
- **Rule-based fallback** when the LLM is unavailable, ensuring 100% uptime
- **Agent feedback loop** to capture corrections for continuous improvement
- **Analytics dashboard** via `/stats` for Operations leadership

## Categories & Priorities

| Category | Description | Priority | Example |
|----------|-------------|----------|---------|
| **Access Issue** | Cannot open/close locker, key problems, lock jammed | P2 | "My key broke inside the lock" |
| **Billing/Payment** | Payment failures, invoice questions, refund requests | P1 | "I was charged twice this month" |
| **Booking/Availability** | Want to rent, waitlist, upgrade/downgrade | P2 | "Is there a larger locker available?" |
| **Damage/Loss** | Locker damaged, suspected tampering, break-in | **P0** | "The locker door seems tampered with" |
| **General Inquiry** | How-to questions, policy doubts, KYC updates | P3 | "What are the visiting hours?" |
| **Complaint/Escalation** | Dissatisfied with service, demand manager | P1 | "Your staff was rude to me yesterday" |
| **Closure/Termination** | Want to end rental, retrieve deposit | P2 | "I want to vacate my locker" |

### Priority Logic
- **P0 (Critical, 1hr SLA)**: Security incidents — immediate human attention
- **P1 (High, 4-24hr SLA)**: Billing disputes and complaints — financial/reputational risk
- **P2 (Medium, 4-48hr SLA)**: Access, booking, closure — operational tasks
- **P3 (Low, 72hr SLA)**: General inquiries — informational responses

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| API Framework | FastAPI (Python) | Modern, async-ready, auto-generated Swagger docs |
| Database | SQLite + SQLAlchemy | Zero-config, portable, easy to swap to PostgreSQL later |
| Classification | OpenAI GPT-4o-mini | Zero-shot, fast to iterate, handles Hinglish/Hindi context |
| Fallback | Keyword-based rules | Ensures 100% classification uptime when LLM fails |
| Validation | Pydantic | Type-safe request/response models |

## Setup Instructions

### Prerequisites
- Python 3.11+

### Installation
1. Clone the repository and navigate to the project directory:
   ```bash
   cd aurm_email_classifier
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to add your `OPENAI_API_KEY`. If left empty, a rule-based fallback will be used.*

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Open `http://localhost:8000/docs` in your browser to view the interactive API documentation.

### Quick Setup with Makefile (Windows)
```bash
make setup    # Creates venv, installs deps, copies .env.example
make run      # Starts the server
make seed     # Seeds sample data
make test     # Runs tests
make clean    # Removes venv and cache
```

## API Documentation

### `POST /classify`
Classifies an incoming email, calculates SLA, saves to the database, and returns the result.

**Request Body**
```json
{
  "email_id": "msg_12345",
  "sender": "rajesh.sharma@gmail.com",
  "title": "Locker not opening with my key",
  "body": "Hi, I've been trying to open my locker for 30 minutes...",
  "received_at": "2026-07-27T14:30:00+05:30"
}
```

**Response Body**
```json
{
  "email_id": "msg_12345",
  "classification_id": 1,
  "category": "Access Issue",
  "priority": "P2",
  "confidence": 0.94,
  "summary": "Customer reports locker not opening despite key turning.",
  "suggested_action": "Assign to on-site technician",
  "estimated_response_time_hours": 4,
  "tags": ["key", "access"],
  "routed_to": "Field Operations",
  "sla_deadline": "2026-07-27T18:30:00Z",
  "status": "classified",
  "needs_human_review": false,
  "language": "en",
  "feedback": []
}
```

### `POST /feedback`
Allows human agents to correct classification errors, updating the database.

**Request Body**
```json
{
  "classification_id": 1,
  "corrected_category": "Damage/Loss",
  "corrected_priority": "P1",
  "notes": "Customer later mentioned lock tampered",
  "agent_id": "agent_007"
}
```

### `GET /classifications/{classification_id}`
Returns full details of a specific classification, its associated email, and any linked feedback records.

### `GET /stats`
Returns aggregate statistics (total classified, count by category/priority, avg confidence, pending human review).

### `GET /health`
Returns system status.

## Post-Classification Flow

1. **Email Received** → Webhook hits `/classify`
2. **Preprocessing** → Strips HTML, signatures, detects language.
3. **Classification** → LLM predicts category, priority, and extracts details. Falls back to keyword rules if LLM unavailable.
4. **Routing** → System determines target team (e.g., Field Ops, Security) and calculates SLA deadline based on priority and category rules.
5. **Human Review (Optional)** → If LLM confidence < 0.75, routed to a human triage queue (`needs_human_review=True`).
6. **Agent Feedback** → Agents submit corrections via `/feedback`, linked to the original classification for continuous improvement.

## Data Strategy for Continuous Improvement
Every manual correction submitted via `/feedback` is saved to the database and linked to the original email classification. This dataset will be periodically exported to fine-tune a smaller, cheaper, and faster model (e.g., `gpt-3.5-turbo` or an open-source model) to reduce classification costs over time.

## Roadmap & Next Steps
- **Webhook Integrations**: Push notifications directly to Slack or Zendesk upon classification.
- **Multi-language Auto-Responses**: Generate automatic preliminary replies based on the detected language and category.
- **Batch Processing**: An endpoint to backfill historical emails.
- **Fine-Tuning**: Use accumulated feedback data to train a specialized local model.
- **Real-Time Dashboard**: Build a frontend React app to monitor category volumes and SLA breaches.
- **Duplicate Detection**: Use fuzzy matching for rapid follow-ups on the same issue.
- **PII Redaction**: Pre-process emails to obscure phone numbers and names before sending to the LLM.
