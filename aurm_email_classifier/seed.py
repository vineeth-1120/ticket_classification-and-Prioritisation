from app.database import SessionLocal, engine
from app.models import Base, Email, Classification
from datetime import datetime, timedelta
import os

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Only seed if empty
existing = db.query(Classification).first()
if existing:
    print("Database already has data. Skipping seed.")
    db.close()
    exit(0)

samples = [
    {
        "email_id": "seed_001",
        "sender": "rajesh.sharma@greenvalley.com",
        "title": "Locker not opening with my key",
        "body": "Hi, I've been trying to open my locker for 30 minutes. The key turns but nothing happens. I'm at Green Valley Society, locker A-204. Please help urgently.",
        "category": "Access Issue", "priority": "P2", "confidence": 0.65,
        "tags": ["access", "key", "locker"], "routed_to": "Field Operations", "response_hours": 4
    },
    {
        "email_id": "seed_002",
        "sender": "priya.verma@gmail.com",
        "title": "Charged twice this month",
        "body": "Hi Aurm team, I noticed my credit card was charged twice for the locker rental this month. The amounts are ₹500 each on 15th and 16th July. Please refund the duplicate charge.",
        "category": "Billing/Payment", "priority": "P1", "confidence": 0.65,
        "tags": ["billing", "payment"], "routed_to": "Finance Team", "response_hours": 24
    },
    {
        "email_id": "seed_003",
        "sender": "amit.kumar@sunshine.com",
        "title": "Want to rent a safe deposit locker",
        "body": "Hello, I recently moved into Sunshine Apartments and I am interested in renting a safe deposit locker. Are there any available? What are the sizes and prices?",
        "category": "Booking/Availability", "priority": "P2", "confidence": 0.65,
        "tags": ["booking", "availability"], "routed_to": "Sales Team", "response_hours": 24
    },
    {
        "email_id": "seed_004",
        "sender": "sneha.patel@palmgrove.com",
        "title": "URGENT: Locker appears tampered",
        "body": "I came to my locker today and the door looks like someone tried to break into it. There are scratch marks around the lock. I am very worried about my jewelry inside. Please check immediately.",
        "category": "Damage/Loss", "priority": "P0", "confidence": 0.6,
        "tags": ["security", "urgent"], "routed_to": "Security Team + Manager", "response_hours": 1
    },
    {
        "email_id": "seed_005",
        "sender": "vikram.rao@gmail.com",
        "title": "What are the visiting hours?",
        "body": "Hi, I am planning to visit my locker this weekend. Could you please tell me what are the operating hours for the locker room? Also, do I need to carry any ID proof?",
        "category": "General Inquiry", "priority": "P3", "confidence": 0.5,
        "tags": ["general", "hours"], "routed_to": "Customer Support", "response_hours": 72
    },
    {
        "email_id": "seed_006",
        "sender": "neha.gupta@yahoo.com",
        "title": "Complaint about rude staff behavior",
        "body": "I visited the locker facility yesterday and the staff member on duty was extremely rude to me. He refused to help and spoke disrespectfully. I want to escalate this to the manager immediately.",
        "category": "Complaint/Escalation", "priority": "P1", "confidence": 0.6,
        "tags": ["complaint", "escalation"], "routed_to": "Customer Support Manager", "response_hours": 4
    },
    {
        "email_id": "seed_007",
        "sender": "rahul.mehta@outlook.com",
        "title": "Request to terminate locker rental",
        "body": "Hi, I am moving to another city next month and would like to terminate my locker rental. Please let me know the process for vacating and getting my security deposit back.",
        "category": "Closure/Termination", "priority": "P2", "confidence": 0.65,
        "tags": ["closure", "termination"], "routed_to": "Operations Team", "response_hours": 48
    }
]

for idx, s in enumerate(samples):
    email = Email(
        email_id=s["email_id"],
        sender=s["sender"],
        title=s["title"],
        body=s["body"],
        cleaned_body=s["body"],
        received_at=datetime.utcnow() - timedelta(days=7-idx, hours=idx),
        language="en"
    )
    db.add(email)
    db.flush()

    classification = Classification(
        email_id=email.id,
        category=s["category"],
        priority=s["priority"],
        confidence=s["confidence"],
        summary=f"Auto-classified as {s['category']} via rule-based fallback.",
        suggested_action=f"Assign to {s['routed_to']}.",
        estimated_response_time_hours=s["response_hours"],
        tags=s["tags"],
        routed_to=s["routed_to"],
        sla_deadline=datetime.utcnow() + timedelta(hours=s["response_hours"]),
        status="classified",
        needs_human_review=False,
        model_version="fallback-v1"
    )
    db.add(classification)

db.commit()
db.close()
print(f"Successfully seeded {len(samples)} sample emails with classifications.")
