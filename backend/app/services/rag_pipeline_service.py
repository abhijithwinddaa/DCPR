import os
import sys
import traceback
from sqlalchemy.orm import Session

from app.services.db_service import DBService
from app.services.vector_service import vector_service
from app.services.pdf_chunker import PDFChunker
from app.services.progress_tracker import ProgressTracker

# Add workspace root directory (4 levels up) to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from knowledge.pipeline.ingestor import Ingestor

class RagPipelineService:
    """
    Orchestrates generic RAG ingestion for document versions of any size.
    """

    @staticmethod
    def process_pdf_rag(db: Session, version_id: str, document_id: str, file_path: str) -> bool:
        """
        Runs full PDF extraction, intelligent text chunking, and ChromaDB vector indexing.
        """
        try:
            print(f"[RagPipelineService] Starting RAG processing for version {version_id}...")
            DBService.update_version_status(db, version_id, "PROCESSING")
            ProgressTracker.update(version_id, "Initializing extraction...", 5)

            # 1. Extract raw page structures using existing Ingestor
            release_id = f"rag:{version_id}"
            ingestor = Ingestor(file_path, release_id)
            ProgressTracker.update(version_id, "Extracting PDF layout & text...", 15)
            
            # ingest(None) extracts ALL pages automatically
            page_docs = ingestor.ingest(page_numbers=None)
            total_pages = len(page_docs)
            if not page_docs:
                raise ValueError("PDF text extraction returned no valid pages.")

            ProgressTracker.update(version_id, f"Extracted {total_pages} pages. Chunking text...", 40, total_pages=total_pages)

            # 2. Split into 1000-token semantic chunks
            chunker = PDFChunker()
            chunks = chunker.chunk(page_docs)
            total_chunks = len(chunks)

            ProgressTracker.update(version_id, f"Generated {total_chunks} chunks. Embedding into ChromaDB...", 60, total_pages=total_pages)

            # 3. Embed and store vectors in ChromaDB
            vector_service.add_chunks(version_id=version_id, document_id=document_id, chunks=chunks)

            # 4. Update status to COMPLETED
            ProgressTracker.update(version_id, "RAG indexing complete!", 100, pages_done=total_pages, total_pages=total_pages)
            DBService.update_version_status(db, version_id, "COMPLETED")
            print(f"[RagPipelineService] RAG ingestion completed successfully for version {version_id} ({total_chunks} chunks indexed).")
            return True

        except Exception as e:
            err_trace = traceback.format_exc()
            print(f"[RagPipelineService] RAG Ingestion failed: {e}\n{err_trace}")
            ProgressTracker.update(version_id, f"Failed: {str(e)}", 0, error=str(e))
            DBService.update_version_status(db, version_id, "FAILED", error_log=f"{e}\n{err_trace}")
            return False

    @staticmethod
    def process_pdf_rag_background(version_id: str, document_id: str, file_path: str):
        """Background worker wrapper with dedicated DB session."""
        from app.db.postgres import get_sessionmaker
        SessionLocal = get_sessionmaker()
        db = SessionLocal()
        try:
            RagPipelineService.process_pdf_rag(db, version_id, document_id, file_path)
        finally:
            db.close()

    @staticmethod
    def process_pdf_hybrid_background(version_id: str, document_id: str, file_path: str, page_range_str: str = "188-197"):
        """Background worker wrapper running both RAG vector indexing and Neo4j Graph compilation."""
        from app.db.postgres import get_sessionmaker
        from app.services.ingestion_service import IngestionService
        SessionLocal = get_sessionmaker()
        db = SessionLocal()
        try:
            print(f"[HybridPipeline] Initiating unified RAG + Neo4j Graph processing for version {version_id}...")
            # 1. Run RAG Vector Indexing
            rag_success = RagPipelineService.process_pdf_rag(db, version_id, document_id, file_path)
            
            # 2. Run Neo4j Graph Compilation
            print(f"[HybridPipeline] RAG phase complete. Compiling Neo4j knowledge graph...")
            graph_success = IngestionService.process_pdf(db, version_id, file_path, page_range_str)
            
            print(f"[HybridPipeline] Fully completed unified ingestion for version {version_id} (RAG: {rag_success}, Graph: {graph_success}).")
        except Exception as e:
            print(f"[HybridPipeline] Unified processing failed: {e}")
        finally:
            db.close()
