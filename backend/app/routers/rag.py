from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.vector_service import vector_service
from app.services.progress_tracker import ProgressTracker
from app.services.reasoning_service import ReasoningService

router = APIRouter(prefix="", tags=["RAG Document Intelligence"])

class AskDocumentRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    top_k: Optional[int] = 5

@router.post("/ask-document")
async def ask_document(request: AskDocumentRequest):
    """
    Executes a document-scoped RAG Q&A query against the vector knowledge base using hybrid search.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = await ReasoningService.rag_explain_async(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        import traceback
        print(f"[RAG Router] Error handling /ask-document: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"RAG query execution failed: {e}")

@router.get("/documents/progress/{version_id}")
def get_processing_progress(version_id: str):
    """Returns real-time progress for background PDF ingestion pipelines."""
    return ProgressTracker.get(version_id)

@router.get("/rag/health")
def get_rag_health():
    """Returns vector storage statistics and health indicators."""
    return vector_service.stats()
