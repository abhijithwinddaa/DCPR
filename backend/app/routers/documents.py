import os
import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.core.config import settings
from app.db.postgres import get_db
from app.services.db_service import DBService
from app.services.ingestion_service import IngestionService
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("DCPR"), # DCPR, CIRCULAR, AMENDMENT, NOTIFICATION, ORDER
    db: Session = Depends(get_db)
):
    """
    Saves uploaded PDF to local storage and registers document metadata.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Get default user for session authorization
    user = DBService.get_or_create_default_user(db)

    # 1. Read file and calculate checksum
    try:
        content = file.file.read()
        file_size = len(content)
        sha256 = hashlib.sha256(content).hexdigest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read upload stream: {e}")

    # 2. Save file to local storage directory
    storage_path = os.path.join(settings.STORAGE_DIR, f"{sha256}.pdf")
    try:
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file to local disk: {e}")

    # 3. Upload to Supabase Storage (optional)
    supabase_url = None
    if SupabaseService.is_available():
        supabase_url = SupabaseService.upload_pdf(
            bucket="dcpr-documents",
            file_name=file.filename,
            content=content,
            sha256=sha256
        )
        if supabase_url:
            print(f"[Supabase] Document uploaded: {supabase_url}")
        else:
            print("[Supabase] Upload skipped or failed (local copy saved).")

    # Reset stream for safety
    file.file.seek(0)

    # 4. Save database records
    try:
        remote_storage_path = supabase_url or storage_path
        remote_storage_bucket = "supabase" if supabase_url else "local-pdfs"
        uploaded_file = DBService.save_uploaded_file(
            db,
            file_name=file.filename,
            size=file_size,
            mime_type=file.content_type,
            sha256=sha256,
            path=remote_storage_path,
            storage_bucket=remote_storage_bucket
        )
        
        doc = DBService.create_document(
            db,
            title=title,
            doc_type=document_type,
            file_id=uploaded_file.id,
            user_id=user.id
        )

        version = DBService.create_document_version(
            db,
            doc_id=doc.id,
            tag="v1.0",
            start_date=date(2018, 12, 7)
        )

        return {
            "document_id": doc.id,
            "version_id": version.id,
            "file_name": file.filename,
            "processing_status": version.processing_status,
            "message": "File uploaded and registered successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database registration failed: {e}")


@router.post("/process")
def process_document(
    version_id: str,
    page_range: str = "188-197",
    mode: str = "rag",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Triggers either the RAG vector indexing pipeline or the deterministic CKM graph compilation pipeline.
    """
    from app.db import models
    from app.services.rag_pipeline_service import RagPipelineService

    # Check if version exists and is in pending/failed status
    version = db.query(models.DocumentVersion).filter_by(id=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")

    doc = db.query(models.Document).filter_by(id=version.document_id).first()
    uploaded_file = db.query(models.UploadedFile).filter_by(id=doc.file_id).first()
    file_path = uploaded_file.storage_path
    ver_id = version.id

    if mode == "dcpr":
        background_tasks.add_task(
            IngestionService.process_pdf_background,
            version_id=ver_id,
            file_path=file_path,
            page_range_str=page_range
        )
        msg = "Deterministic CKM layout extraction initiated."
    elif mode == "rag":
        background_tasks.add_task(
            RagPipelineService.process_pdf_rag_background,
            version_id=ver_id,
            document_id=doc.id,
            file_path=file_path
        )
        msg = "Full RAG document chunking & vector indexing initiated."
    else:
        # Hybrid mode (default): Automatically runs BOTH RAG vector indexing and Neo4j Graph compiling!
        background_tasks.add_task(
            RagPipelineService.process_pdf_hybrid_background,
            version_id=ver_id,
            document_id=doc.id,
            file_path=file_path,
            page_range_str=page_range
        )
        msg = "Unified Hybrid Ingestion initiated (RAG Vector Indexing + Neo4j Knowledge Graph)."

    # Pre-emptively update status to show processing has started/scheduled
    version.processing_status = "PROCESSING"
    db.commit()

    return {
        "version_id": version.id,
        "processing_status": "PROCESSING",
        "message": msg
    }


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    """Lists all uploaded documents with processing lineage details."""
    from app.db import models
    results = []
    docs = db.query(models.Document).all()
    for doc in docs:
        versions = db.query(models.DocumentVersion).filter_by(document_id=doc.id).all()
        for ver in versions:
            results.append({
                "document_id": doc.id,
                "version_id": ver.id,
                "title": doc.title,
                "type": doc.document_type,
                "version_tag": ver.version_tag,
                "processing_status": ver.processing_status,
                "error_log": ver.error_log,
                "created_at": ver.created_at
            })
    return results


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document, its versions, and its file record."""
    from app.db import models
    doc = db.query(models.Document).filter_by(id=document_id).first()
    if not doc:
        ver = db.query(models.DocumentVersion).filter_by(id=document_id).first()
        if ver:
            doc = db.query(models.Document).filter_by(id=ver.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Delete associated versions
    versions = db.query(models.DocumentVersion).filter_by(document_id=doc.id).all()
    for ver in versions:
        db.delete(ver)

    # 1b. Delete vector chunks in ChromaDB
    from app.services.vector_service import vector_service
    vector_service.delete_document_chunks(doc.id)

    # 2. Delete document
    db.delete(doc)

    # 3. Delete file if not referenced elsewhere
    uploaded_file = db.query(models.UploadedFile).filter_by(id=doc.file_id).first()
    if uploaded_file:
        other_ref = db.query(models.Document).filter(
            models.Document.file_id == uploaded_file.id,
            models.Document.id != doc.id
        ).first()
        if not other_ref:
            if os.path.exists(uploaded_file.storage_path):
                try:
                    os.remove(uploaded_file.storage_path)
                except Exception as e:
                    print(f"Warning: Failed to delete physical file: {e}")
            db.delete(uploaded_file)

    db.commit()
    return {"message": "Document deleted successfully."}

