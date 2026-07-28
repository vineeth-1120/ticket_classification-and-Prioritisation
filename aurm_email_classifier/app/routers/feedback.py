from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)

@router.post("/", response_model=schemas.FeedbackResponse)
def submit_feedback(request: schemas.FeedbackRequest, db: Session = Depends(get_db)):
    
    # 1. Verify classification exists
    db_classification = db.query(models.Classification).filter(models.Classification.id == request.classification_id).first()
    
    if not db_classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classification with ID {request.classification_id} not found"
        )
        
    # 2. Save Feedback
    db_feedback = models.Feedback(
        classification_id=request.classification_id,
        corrected_category=request.corrected_category,
        corrected_priority=request.corrected_priority,
        notes=request.notes,
        agent_id=request.agent_id
    )
    
    db.add(db_feedback)
    
    # 3. Update Classification if corrections provided
    if request.corrected_category:
        db_classification.category = request.corrected_category
    if request.corrected_priority:
        db_classification.priority = request.corrected_priority
        
    db_classification.status = "reviewed"
    db_classification.needs_human_review = False
    
    db.commit()
    
    return schemas.FeedbackResponse(
        status="success",
        message="Feedback saved successfully and classification updated."
    )
