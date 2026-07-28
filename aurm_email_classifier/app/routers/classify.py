from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .. import schemas, models
from ..database import get_db
from ..services.preprocessor import preprocess_email
from ..services.classifier import classify_email_with_llm
from ..services.router_service import determine_routing_and_sla

router = APIRouter(
    prefix="/classify",
    tags=["Classification"]
)

@router.post("/", response_model=schemas.ClassifyResponse)
def classify_email(request: schemas.ClassifyRequest, db: Session = Depends(get_db)):
    # 1. Check for duplicate email_id
    existing_email = db.query(models.Email).filter(models.Email.email_id == request.email_id).first()
    
    if existing_email and existing_email.classification:
        # Return cached classification
        cls = existing_email.classification
        return schemas.ClassifyResponse(
            email_id=existing_email.email_id,
            classification_id=cls.id,
            category=cls.category,
            priority=cls.priority,
            confidence=cls.confidence,
            summary=cls.summary,
            suggested_action=cls.suggested_action,
            estimated_response_time_hours=cls.estimated_response_time_hours,
            tags=cls.tags,
            routed_to=cls.routed_to,
            sla_deadline=cls.sla_deadline,
            status=cls.status,
            needs_human_review=cls.needs_human_review,
            language=existing_email.language
        )
        
    # 2. Preprocess body
    prep_data = preprocess_email(request.body)
    cleaned_body = prep_data["cleaned_body"]
    language = prep_data["language"]
    
    # 3. Call OpenAI for classification
    llm_result = classify_email_with_llm(request.title, cleaned_body)
    
    # 4. Determine routing and SLA
    routing_info = determine_routing_and_sla(
        category=llm_result["category"],
        priority=llm_result["priority"],
        received_at=request.received_at
    )
    
    # 5. Save Email + Classification to database
    db_email = models.Email(
        email_id=request.email_id,
        sender=request.sender,
        title=request.title,
        body=request.body,
        cleaned_body=cleaned_body,
        received_at=request.received_at,
        language=language
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    
    db_classification = models.Classification(
        email_id=db_email.id,
        category=llm_result["category"],
        priority=llm_result["priority"],
        confidence=llm_result.get("confidence", 0.0),
        summary=llm_result.get("summary", ""),
        suggested_action=llm_result.get("suggested_action", ""),
        estimated_response_time_hours=routing_info["estimated_response_time_hours"],
        tags=llm_result.get("tags", []),
        routed_to=routing_info["routed_to"],
        sla_deadline=routing_info["sla_deadline"],
        status="pending_review" if llm_result.get("needs_human_review") else "classified",
        needs_human_review=llm_result.get("needs_human_review", False)
    )
    
    db.add(db_classification)
    db.commit()
    db.refresh(db_classification)
    
    # 6. Return structured response
    return schemas.ClassifyResponse(
        email_id=db_email.email_id,
        classification_id=db_classification.id,
        category=db_classification.category,
        priority=db_classification.priority,
        confidence=db_classification.confidence,
        summary=db_classification.summary,
        suggested_action=db_classification.suggested_action,
        estimated_response_time_hours=db_classification.estimated_response_time_hours,
        tags=db_classification.tags,
        routed_to=db_classification.routed_to,
        sla_deadline=db_classification.sla_deadline,
        status=db_classification.status,
        needs_human_review=db_classification.needs_human_review,
        language=db_email.language
    )
