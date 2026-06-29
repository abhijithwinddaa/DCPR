import sys
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.postgres import get_db
from app.services.db_service import DBService
from app.services.rule_engine_service import RuleEngineService

# Add workspace root directory (4 levels up) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from knowledge.validation.validation_engine import CalculationValidator

router = APIRouter(prefix="/calculate", tags=["calculator"])

class CalculationRequest(BaseModel):
    scheme_uri: str # e.g. "dcpr:scheme:33-9"
    inputs: dict   # key-value inputs e.g. gross_cluster_area, access_road_width, etc.

@router.post("")
def run_calculation(request: CalculationRequest, db: Session = Depends(get_db)):
    """
    Executes the deterministic Rule Engine, runs the validation audits layer,
    persists audit logs in the DB, and returns the final answers and traces.
    """
    # 1. Fetch default user for authorization link
    user = DBService.get_or_create_default_user(db)

    # 2. Run Rule Engine calculation
    try:
        engine_outputs = RuleEngineService.evaluate(request.scheme_uri, request.inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule Engine execution failed: {e}")

    # 3. Run Calculation Validation audits
    contract_data = RuleEngineService.get_contract_data()
    validator = CalculationValidator()
    
    # Extract citation from scheme_uri e.g. 'dcpr:scheme:33-9' -> '33(9)'
    scheme_citation = request.scheme_uri.split(":")[-1].replace("-", "(")
    if "(" in scheme_citation and not scheme_citation.endswith(")"):
        scheme_citation += ")"
    
    try:
        validation_results = validator.validate(
            contract_data=contract_data,
            scheme_id=scheme_citation,
            user_inputs=request.inputs,
            execution_output=engine_outputs
        )
    except Exception as e:
        print(f"Warning: Calculation Validation failed: {e}")
        validation_results = {
            "validation_status": "FAIL",
            "warnings": [f"Validator crashed: {e}"]
        }

    # Enrich output payload with validator details
    engine_outputs["validator_status"] = validation_results.get("validation_status", "FAIL")
    engine_outputs["validation_warnings"] = validation_results.get("warnings", [])

    # 4. Save calculations & step trace audits to database
    try:
        saved_calc = DBService.save_calculation(
            db,
            scheme_uri=request.scheme_uri,
            inputs=request.inputs,
            outputs=engine_outputs,
            user_id=user.id
        )
        
        # Include calculation ID in the response for NL questions link
        engine_outputs["calculation_id"] = saved_calc.id
        
        return engine_outputs
    except Exception as e:
        import traceback
        print(f"Failed to persist calculation: {e}\n{traceback.format_exc()}")
        # Still return results even if saving history failed
        engine_outputs["calculation_id"] = None
        return engine_outputs


@router.get("/history")
def get_calculations_history(limit: int = 15, db: Session = Depends(get_db)):
    """Fetches list of recently executed calculation runs."""
    calcs = DBService.get_calculation_history(db, limit)
    results = []
    for c in calcs:
        results.append({
            "calculation_id": c.id,
            "scheme_uri": c.scheme_uri,
            "input_parameters": c.input_parameters,
            "output_results": c.output_results,
            "validator_status": c.validator_status,
            "validation_warnings": c.validation_warnings,
            "created_at": c.created_at
        })
    return results
