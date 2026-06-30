import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.postgres import init_db, get_sessionmaker
from app.db.neo4j_conn import neo4j_db
from app.routers import documents, calculator, ask, graph, health, rag
from app.services.db_service import DBService

app = FastAPI(
    title="DCPR Knowledge Platform API",
    description="Production-grade API for Development Control & Promotion Regulations zoning compliance.",
    version="1.0.0"
)

# CORS: restrict to configured origins in production
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(calculator.router)
app.include_router(ask.router)
app.include_router(graph.router)
app.include_router(rag.router)


@app.on_event("startup")
def on_startup():
    print("=== DCPR Platform Startup Initialization ===")
    
    # 1. Initialize relational database tables
    try:
        init_db()
    except Exception as db_err:
        print(f"Error during Relational DB table setup: {db_err}")

    # 2. Verify and connect to Graph database
    try:
        neo4j_db.connect()
    except Exception as g_err:
        print(f"Error connecting to Neo4j graph: {g_err}")

    # 3. Create default user and seed initial knowledge package if database is empty
    try:
        SessionLocal = get_sessionmaker()
        with SessionLocal() as db:
            # Seed default user
            user = DBService.get_or_create_default_user(db)
            print(f"Verified default user session: {user.email}")
            
            # Check if we should seed default entities (Mumbai-DCPR Scheme 33(9))
            from app.db import models
            entity_count = db.query(models.KnowledgeEntity).count()
            if entity_count == 0:
                print("Relational database is empty. Attempting to seed from prebuilt YAML schemas...")
                seed_default_knowledge(db)
            else:
                print(f"Database contains {entity_count} knowledge entities. Seeding skipped.")
    except Exception as seed_err:
        print(f"Warning: Failed to seed default records on startup: {seed_err}")
        import traceback
        traceback.print_exc()

    # 4. Auto-start and pre-warm Ollama Qwen model in background (non-blocking)
    import threading, subprocess, urllib.request, json
    def _warmup_ollama():
        # Check if Ollama service is reachable, start if offline
        try:
            urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)
            print("[Startup] Ollama service verified active on port 11434.")
        except Exception:
            print("[Startup] Ollama offline. Auto-launching 'ollama serve' process...")
            try:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time; time.sleep(3)
            except Exception as launch_err:
                print(f"[Startup] Could not auto-launch Ollama: {launch_err}")

        # Pre-warm model in memory
        try:
            payload = json.dumps({
                "model": settings.OLLAMA_MODEL,
                "prompt": "warmup",
                "stream": False,
                "options": {"num_predict": 1}
            }).encode("utf-8")
            req = urllib.request.Request(
                settings.OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                print(f"[Startup] Ollama model '{settings.OLLAMA_MODEL}' pre-warmed and ready.")
        except Exception as warm_err:
            print(f"[Startup] Model pre-warm notice: {warm_err}")
    threading.Thread(target=_warmup_ollama, daemon=True).start()

    print("=== DCPR Platform Ready ===")


def seed_default_knowledge(db):
    """Seeds relational schema from the prebuilt YAML package if available."""
    import yaml
    from datetime import date
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    seed_yaml_path = os.path.join(project_root, "knowledge", "schemes", "33-9.yaml")
    
    if not os.path.exists(seed_yaml_path):
        print(f"Prebuilt scheme file not found at {seed_yaml_path}. Skipping database pre-seed.")
        return
        
    try:
        with open(seed_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        print(f"Loading seed data from {seed_yaml_path}...")
        
        from app.db import models
        # Create a document and version placeholder for seeding
        file_id = None
        user = DBService.get_or_create_default_user(db)
        
        # Find if there's any file
        uploaded_file = db.query(models.UploadedFile).first()
        if uploaded_file:
            file_id = uploaded_file.id

            
        doc = DBService.create_document(
            db,
            title="Mumbai DCPR 2034 - Precompiled Scheme 33(9)",
            doc_type="DCPR",
            file_id=file_id,
            user_id=user.id
        )
        
        version = DBService.create_document_version(
            db,
            doc_id=doc.id,
            tag="v1.0",
            start_date=date(2018, 12, 7)
        )
        
        # Process and save package entities
        from app.services.ingestion_service import IngestionService
        entities = IngestionService._map_package_to_entities(data)
        saved_count = DBService.save_knowledge_entities(db, version.id, entities)
        
        DBService.update_version_status(db, version.id, "COMPLETED")
        print(f"Successfully seeded {saved_count} knowledge entities into database.")
        
    except Exception as e:
        db.rollback()
        print(f"Warning: Failed to parse seed YAML: {e}")


@app.get("/")
def read_root():
    from app.routers.health import health_check
    return health_check()
