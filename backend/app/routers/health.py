from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
import app.db.postgres as pg
from app.db.neo4j_conn import neo4j_db
from app.services.rule_engine_service import RuleEngineService

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    """
    Returns the operational status of all platform dependencies.
    Used by monitoring, startup scripts, and the frontend status indicator.
    """
    # --- Database status ---
    db_status = "connected"
    db_type = "postgresql"
    try:
        engine = pg.get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        if pg.is_sqlite_fallback:
            db_type = "sqlite (fallback)"
            db_status = "degraded (fallback)"
    except Exception as e:
        db_status = f"error: {e}"
        db_type = "unknown"

    # --- Neo4j / Graph status ---
    graph_status = "connected"
    graph_type = "neo4j"
    try:
        neo4j_db.connect()
        if neo4j_db.use_fallback:
            graph_type = "networkx (fallback)"
            graph_status = "degraded (fallback)"
    except Exception as e:
        graph_status = f"error: {e}"
        graph_type = "unknown"

    # --- Ollama status ---
    ollama_status = "connected"
    ollama_model = settings.OLLAMA_MODEL
    try:
        import urllib.request, json
        req = urllib.request.Request(settings.OLLAMA_URL.replace("/api/generate", "/api/tags"))
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            models = [m["name"] for m in data.get("models", [])]
            if settings.OLLAMA_MODEL not in models:
                ollama_status = f"model '{settings.OLLAMA_MODEL}' not found"
    except Exception as e:
        ollama_status = f"offline ({e})"

    # --- Rule Engine contract ---
    contract_status = "loaded"
    try:
        contract = RuleEngineService.get_contract_data()
        scheme_count = len(contract)
        if scheme_count == 0:
            contract_status = "empty (no schemes loaded)"
    except Exception as e:
        contract_status = f"error: {e}"
        scheme_count = 0

    return {
        "status": "online",
        "service": "DCPR Knowledge Platform Backend",
        "version": "1.0.0",
        "dependencies": {
            "database": {
                "status": db_status,
                "type": db_type
            },
            "graph": {
                "status": graph_status,
                "type": graph_type,
                "node_count": len(neo4j_db.nx_graph.nodes) if neo4j_db.nx_graph else 0
            },
            "ollama": {
                "status": ollama_status,
                "model": ollama_model
            },
            "rule_engine": {
                "status": contract_status,
                "schemes_loaded": scheme_count
            }
        }
    }
