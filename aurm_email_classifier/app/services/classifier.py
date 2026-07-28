import json
import logging
from openai import OpenAI
from pydantic import BaseModel
from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an expert customer support triage system for Aurm, a company that provides safe deposit lockers in residential societies across India.

Your job is to classify incoming customer emails into categories, assign priorities, and suggest actions.

## CATEGORIES
1. Access Issue — Customer cannot open/close locker, key problems, biometric failure, lock jammed
2. Billing/Payment — Payment failures, invoice questions, refund requests, double charges
3. Booking/Availability — Want to rent locker, waitlist, upgrade/downgrade size, new society inquiry
4. Damage/Loss — Locker damaged, suspected tampering, contents compromised, break-in
5. General Inquiry — How-to questions, policy doubts, KYC updates, visiting hours
6. Complaint/Escalation — Dissatisfied with service, rude staff, demand to speak to manager
7. Closure/Termination — Want to end rental, retrieve deposit, vacate locker

## PRIORITY RULES
- P0 (Critical): Security breach, damage/loss, break-in suspected, customer locked out and distressed
- P1 (High): Billing disputes, complaints/escalations, repeated failures
- P2 (Medium): Access issues, booking requests, KYC updates
- P3 (Low): General inquiries, policy questions, non-urgent how-to

## OUTPUT FORMAT
Return ONLY valid JSON. No markdown, no explanation. Format:
{
  "category": "<one of the 7 categories>",
  "priority": "<P0|P1|P2|P3>",
  "confidence": <float 0.0-1.0>,
  "summary": "<2-3 sentence summary>",
  "suggested_action": "<specific next step>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"],
  "sentiment": "<positive|neutral|negative|frustrated|angry>",
  "urgency_signals": ["<detected urgency keyword or phrase>"]
}

## RULES
- If the email mentions "tampered", "broken into", "stolen", "missing" → category Damage/Loss, priority P0
- If the email mentions "charged twice", "refund", "wrong amount" → category Billing/Payment
- If the email mentions "not opening", "key stuck", "forgot combination" → category Access Issue
- If the customer sounds angry, frustrated, or uses ALL CAPS → boost priority by one level
- Detect language of email and note it mentally, but respond in English
- If email is in Hinglish or Hindi, understand context and classify accordingly
"""

def rule_based_classify(cleaned_body: str, title: str):
    text = (title + " " + cleaned_body).lower()
    
    # P0 / Critical signals
    if any(word in text for word in ["tampered", "broken into", "stolen", "missing", "theft", "robbed"]):
        return {
            "category": "Damage/Loss",
            "priority": "P0",
            "confidence": 0.6,
            "summary": "Potential security incident detected via keyword matching.",
            "suggested_action": "Escalate to Security Team immediately.",
            "estimated_response_time_hours": 1,
            "tags": ["security", "urgent"],
            "sentiment": "negative",
            "urgency_signals": ["security concern"]
        }
    
    # Access Issue
    if any(word in text for word in ["not opening", "won't open", "stuck", "key broke", "key stuck", "forgot", "can't access", "cannot open", "locked out", "jam", "handle broken"]):
        return {
            "category": "Access Issue",
            "priority": "P2",
            "confidence": 0.65,
            "summary": "Customer reports difficulty accessing their locker.",
            "suggested_action": "Assign to on-site technician.",
            "estimated_response_time_hours": 4,
            "tags": ["access", "key", "locker"],
            "sentiment": "negative",
            "urgency_signals": ["access problem"]
        }
    
    # Billing
    if any(word in text for word in ["charged", "payment", "refund", "invoice", "bill", "double charge", "amount", "paid", "transaction", "failed payment", "deducted"]):
        return {
            "category": "Billing/Payment",
            "priority": "P1",
            "confidence": 0.65,
            "summary": "Customer inquiry related to payment or charges.",
            "suggested_action": "Assign to Finance Team.",
            "estimated_response_time_hours": 24,
            "tags": ["billing", "payment"],
            "sentiment": "neutral",
            "urgency_signals": ["billing concern"]
        }
    
    # Closure
    if any(word in text for word in ["close", "terminate", "vacate", "end rental", "stop", "cancel", "withdraw", "deposit back"]):
        return {
            "category": "Closure/Termination",
            "priority": "P2",
            "confidence": 0.65,
            "summary": "Customer wishes to end their locker rental.",
            "suggested_action": "Assign to Operations Team.",
            "estimated_response_time_hours": 48,
            "tags": ["closure", "termination"],
            "sentiment": "neutral",
            "urgency_signals": ["termination request"]
        }
    
    # Booking
    if any(word in text for word in ["rent", "book", "available", "waitlist", "upgrade", "downsize", "larger", "smaller", "new locker", "want a locker"]):
        return {
            "category": "Booking/Availability",
            "priority": "P2",
            "confidence": 0.65,
            "summary": "Customer interested in renting or changing locker.",
            "suggested_action": "Assign to Sales Team.",
            "estimated_response_time_hours": 24,
            "tags": ["booking", "availability"],
            "sentiment": "neutral",
            "urgency_signals": ["booking request"]
        }
    
    # Complaint
    if any(word in text for word in ["rude", "complaint", "escalate", "manager", "supervisor", "worst", "terrible", "pathetic", "angry", "frustrated"]) or "!" in text:
        return {
            "category": "Complaint/Escalation",
            "priority": "P1",
            "confidence": 0.6,
            "summary": "Customer expressing dissatisfaction with service.",
            "suggested_action": "Assign to Customer Support Manager.",
            "estimated_response_time_hours": 4,
            "tags": ["complaint", "escalation"],
            "sentiment": "frustrated",
            "urgency_signals": ["dissatisfaction"]
        }
    
    # Default: General Inquiry
    return {
        "category": "General Inquiry",
        "priority": "P3",
        "confidence": 0.5,
        "summary": "General inquiry requiring manual review.",
        "suggested_action": "Review manually and assign appropriately.",
        "estimated_response_time_hours": 72,
        "tags": ["general"],
        "sentiment": "neutral",
        "urgency_signals": []
    }

def classify_email_with_llm(title: str, cleaned_body: str) -> dict:
    """Classify the email using OpenAI. Falls back to rules if it fails."""
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.warning("OpenAI API key missing. Using fallback classifier.")
        return rule_based_classify(cleaned_body, title)
        
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"Title: {title}\nBody: {cleaned_body}"
    
    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0,
            max_tokens=500
        )
        
        result_str = response.choices[0].message.content
        result_json = json.loads(result_str)
        
        # Determine if human review is needed
        confidence = result_json.get("confidence", 0.0)
        result_json["needs_human_review"] = confidence < 0.75
        
        return result_json
        
    except Exception as e:
        logger.error(f"OpenAI API call failed - Type: {type(e).__name__}, Message: {str(e)}")
        return rule_based_classify(cleaned_body, title)
