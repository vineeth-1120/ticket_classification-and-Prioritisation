import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .database import engine, Base, get_db
from .routers import classify, feedback

app = FastAPI(
    title="Aurm Email Classifier API",
    description="Automated email classification and triage system for Aurm safe deposit lockers.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(classify.router)
app.include_router(feedback.router)

@app.get("/health", response_model=schemas.HealthResponse, tags=["System"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/classifications/{classification_id}", tags=["Classification"])
def get_classification(classification_id: int, db: Session = Depends(get_db)):
    db_classification = db.query(models.Classification).filter(models.Classification.id == classification_id).first()
    if not db_classification:
        raise HTTPException(status_code=404, detail="Classification not found")
        
    return {
        "classification": db_classification,
        "email": db_classification.email
    }

@app.get("/stats", response_model=schemas.StatsResponse, tags=["System"])
def get_stats(db: Session = Depends(get_db)):
    total_classified = db.query(models.Classification).count()
    
    # By category
    category_counts = db.query(models.Classification.category, func.count(models.Classification.id)).group_by(models.Classification.category).all()
    by_category = {cat: count for cat, count in category_counts if cat}
    
    # By priority
    priority_counts = db.query(models.Classification.priority, func.count(models.Classification.id)).group_by(models.Classification.priority).all()
    by_priority = {pri: count for pri, count in priority_counts if pri}
    
    # Avg confidence
    avg_confidence = db.query(func.avg(models.Classification.confidence)).scalar() or 0.0
    
    # Pending human review
    pending_count = db.query(models.Classification).filter(models.Classification.needs_human_review == True).count()
    
    return schemas.StatsResponse(
        total_classified=total_classified,
        by_category=by_category,
        by_priority=by_priority,
        avg_confidence=round(avg_confidence, 2),
        pending_human_review_count=pending_count
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
