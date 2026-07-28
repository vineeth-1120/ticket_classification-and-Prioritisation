from datetime import datetime, timedelta, timezone

ROUTING_TABLE = {
    "Access Issue": {"team": "Field Operations", "sla_hours": 4},
    "Billing/Payment": {"team": "Finance Team", "sla_hours": 24},
    "Booking/Availability": {"team": "Sales Team", "sla_hours": 24},
    "Damage/Loss": {"team": "Security Team + Manager", "sla_hours": 1},
    "General Inquiry": {"team": "Customer Support", "sla_hours": 72},
    "Complaint/Escalation": {"team": "Customer Support Manager", "sla_hours": 4},
    "Closure/Termination": {"team": "Operations Team", "sla_hours": 48}
}

def determine_routing_and_sla(category: str, priority: str, received_at: datetime) -> dict:
    """
    Determine the routing team and SLA deadline based on category and priority.
    """
    # Default fallback if category not found
    team = "Customer Support"
    sla_hours = 72
    
    if category in ROUTING_TABLE:
        team = ROUTING_TABLE[category]["team"]
        sla_hours = ROUTING_TABLE[category]["sla_hours"]
        
    # Priority override: P0 always gets SLA = 1 hour
    if priority == "P0":
        sla_hours = 1
        
    # Ensure received_at is timezone-aware for math, assuming naive is UTC if missing
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)
        
    sla_deadline = received_at + timedelta(hours=sla_hours)
    
    return {
        "routed_to": team,
        "estimated_response_time_hours": sla_hours,
        "sla_deadline": sla_deadline
    }
