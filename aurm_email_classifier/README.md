# Aurm Email Classifier API

An automated email classification and triage system for Aurm, an intelligent safe deposit locker service. The API uses a Large Language Model (`gpt-4o-mini`) via zero-shot classification to read incoming emails, classify them, estimate SLAs, and assign them to the correct internal teams.

## Problem Statement
Aurm's Ops team manually reads and replies to customer emails. This is time-consuming, prone to human error, and delays critical issues (like security breaches or access issues) from being handled promptly. By automating classification and priority assignment, Aurm can scale its customer support operations efficiently while meeting stringent SLAs.

## Design Decisions

1. **Category Definitions (7 classes):** Based on standard residential vault operations. Separating critical issues (Damage/Loss) from operational ones (Access/Billing) is crucial for accurate routing.
2. **P0-P3 Priority System:** Provides clear SLA deadlines. P0 indicates high-stakes physical security threats, overriding standard category SLAs.
3. **LLM over Traditional ML:** A zero-shot LLM requires no prior training data to start working, understands nuanced urgency, handles colloquialisms (Hinglish, poor grammar), and provides clear summarization along with classification. 
4. **SQLite + SQLAlchemy:** Provides zero setup friction for demonstration and testing, while SQLAlchemy ORM allows for a seamless transition to a production PostgreSQL database later.
5. **Fallback Mechanism:** Implemented a robust keyword-matching fallback system to gracefully handle OpenAI API outages or rate limits, preventing total system failure.

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

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open `http://localhost:8000/docs` in your browser to view the interactive API documentation.

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
  "language": "en"
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

### `GET /stats`
Returns aggregate statistics (e.g., total classified, count by category/priority).

### `GET /health`
Returns system status.

### `GET /classifications/{classification_id}`
Returns full details of a specific classification and its associated email.

## Category Definitions

| Category | Real-World Examples |
|----------|---------------------|
| **Access Issue** | "Key is stuck", "Biometric not recognizing fingerprint", "Door jammed" |
| **Billing/Payment** | "Charged twice for this month", "Invoice missing", "Refund my deposit" |
| **Booking/Availability** | "Want to upgrade to a larger locker", "Is there a waitlist at Green Valley?" |
| **Damage/Loss** | "My locker looks tampered with", "Something is missing from my box" |
| **General Inquiry** | "What are the visiting hours?", "Do I need to update my KYC?" |
| **Complaint/Escalation** | "Your staff was very rude", "I want to speak to a manager immediately" |
| **Closure/Termination** | "I am moving out and want to surrender my locker", "Close my account" |

## Post-Classification Flow

1. **Email Received** → Webhook hits `/classify`
2. **Preprocessing** → Strips HTML, signatures, detects language.
3. **Classification** → LLM predicts category, priority, and extracts details.
4. **Routing** → System determines target team (e.g., Field Ops, Security) and calculates SLA deadline based on priority and category rules.
5. **Human Review (Optional)** → If LLM confidence < 0.75, routed to a human triage queue (`needs_human_review=True`).
6. **Integration (Next Steps)** → A background worker or webhook integration reads the classification and creates a ticket in a CRM (Zendesk/Freshdesk) or pings a Slack channel.

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
