import threading
from datetime import datetime

class ProgressTracker:
    """
    Thread-safe in-memory progress store for real-time tracking of PDF ingestion.
    Keyed by version_id.
    """
    _lock = threading.Lock()
    _progress_store = {}

    @classmethod
    def update(cls, version_id: str, stage: str, percent: int, pages_done: int = 0, total_pages: int = 0, error: str = None):
        with cls._lock:
            cls._progress_store[version_id] = {
                "version_id": version_id,
                "stage": stage,
                "percent": min(max(percent, 0), 100),
                "pages_done": pages_done,
                "total_pages": total_pages,
                "error": error,
                "updated_at": datetime.utcnow().isoformat()
            }

    @classmethod
    def get(cls, version_id: str) -> dict:
        with cls._lock:
            return cls._progress_store.get(version_id, {
                "version_id": version_id,
                "stage": "Initializing...",
                "percent": 0,
                "pages_done": 0,
                "total_pages": 0,
                "error": None,
                "updated_at": datetime.utcnow().isoformat()
            })

    @classmethod
    def clear(cls, version_id: str):
        with cls._lock:
            if version_id in cls._progress_store:
                del cls._progress_store[version_id]
