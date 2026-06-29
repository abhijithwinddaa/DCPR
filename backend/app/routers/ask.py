from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.db.postgres import get_db
from app.db import models
from app.services.db_service import DBService
from app.services.reasoning_service import ReasoningService

router = APIRouter(prefix="/ask", tags=["ask"])

class AskRequest(BaseModel):
    question: str
    calculation_id: str | None = None

@router.post("")
def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """
    Coordinates calculation inputs & traces or general graph queries to local Ollama (Qwen)
    to compile natural language explanations.
    """
    # 1. Fetch calculation context from database if calculation_id is provided and not empty
    calc = None
    if request.calculation_id:
        calc = db.query(models.Calculation).filter_by(id=request.calculation_id).first()

    # 2. Get default user for link metadata
    user = DBService.get_or_create_default_user(db)

    # 3. Construct context parameters
    inputs = {}
    outputs = {}
    validation_status = {}
    
    if calc:
        inputs = calc.input_parameters
        outputs = calc.output_results
        validation_status = {
            "validation_status": calc.validator_status,
            "warnings": calc.validation_warnings
        }

    # 4. Generate explainability text
    try:
        explanation = ReasoningService.explain(
            question=request.question,
            inputs=inputs,
            outputs=outputs,
            validation_status=validation_status,
            calculation_id=request.calculation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning service execution failed: {e}")

    # Detect if explanation is fallback text
    was_fallback = "Ollama Qwen model is currently offline" in explanation or "fallback" in explanation.lower()

    # 5. Persist question and explanation history
    try:
        DBService.save_question(
            db,
            calc_id=calc.id if calc else None,
            question=request.question,
            answer=explanation,
            model=settings.OLLAMA_MODEL,
            was_fallback=was_fallback,
            user_id=user.id
        )
    except Exception as e:
        print(f"Warning: Failed to save question history: {e}")

    return {
        "question": request.question,
        "explanation": explanation,
        "was_fallback": was_fallback,
        "model": settings.OLLAMA_MODEL
    }

