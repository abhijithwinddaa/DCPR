import os
import requests
from supabase import create_client
from app.core.config import settings

class SupabaseService:
    """Handles Supabase Storage operations for PDF uploads."""

    _client = None
    _headers = None
    _storage_url = None

    @classmethod
    def get_client(cls):
        if cls._client is None and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            cls._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            cls._headers = {
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            }
            cls._storage_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1"
        return cls._client

    @classmethod
    def is_available(cls) -> bool:
        return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY)

    @classmethod
    def _ensure_bucket(cls, bucket: str) -> bool:
        """Create bucket via REST API if it doesn't exist."""
        cls.get_client()
        if not cls._storage_url:
            return False
        try:
            # Check if bucket exists
            r = requests.get(f"{cls._storage_url}/bucket/{bucket}", headers=cls._headers)
            if r.status_code == 200:
                return True
            # Create bucket
            r = requests.post(
                f"{cls._storage_url}/bucket",
                headers={**cls._headers, "Content-Type": "application/json"},
                json={"name": bucket, "public": True}
            )
            if r.status_code in (200, 201):
                print(f"[SupabaseService] Created bucket '{bucket}'")
                return True
            print(f"[SupabaseService] Failed to create bucket '{bucket}': {r.text}")
            return False
        except Exception as e:
            print(f"[SupabaseService] Failed to ensure bucket '{bucket}' (offline fallback): {e}")
            return False


    @classmethod
    def upload_pdf(cls, bucket: str, file_name: str, content: bytes, sha256: str) -> str | None:
        """Uploads a PDF to Supabase Storage. Returns the public URL or None."""
        cls.get_client()
        if not cls._storage_url:
            return None
        if not cls._ensure_bucket(bucket):
            return None
        try:
            storage_path = f"dcpr/{sha256}/{file_name}"
            upload_url = f"{cls._storage_url}/object/{bucket}/{storage_path}"
            r = requests.post(
                upload_url,
                headers={**cls._headers, "Content-Type": "application/pdf"},
                data=content
            )
            if r.status_code not in (200, 201):
                # KeyError: already exists
                if r.status_code == 400 and "already exists" in r.text:
                    pass  # File exists, can still get URL
                else:
                    print(f"[SupabaseService] Upload returned {r.status_code}: {r.text}")
                    return None
            public_url = f"{cls._storage_url}/object/public/{bucket}/{storage_path}"
            print(f"[SupabaseService] Uploaded to {public_url}")
            return public_url
        except Exception as e:
            print(f"[SupabaseService] Upload failed: {e}")
            return None
