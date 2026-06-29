import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Base class for SQLAlchemy models
Base = declarative_base()

# Attempt to connect to PostgreSQL. If connection fails, fallback to SQLite.
_engine = None
_SessionLocal = None
is_sqlite_fallback = False

def get_engine():
    global _engine, is_sqlite_fallback
    if _engine is not None:
        return _engine

    db_url = settings.database_url
    print(f"Attempting connection to PostgreSQL at {db_url}...")
    try:
        # Short timeout for PostgreSQL connection test to prevent long hangs at startup
        engine = create_engine(
            db_url,
            connect_args={"connect_timeout": 3} if db_url.startswith("postgresql") else {}
        )
        # Test connection
        with engine.connect() as conn:
            print("Successfully connected to PostgreSQL database.")
        _engine = engine
        is_sqlite_fallback = False
    except Exception as e:
        print(f"Warning: Failed to connect to PostgreSQL ({e}). Falling back to local SQLite.")
        sqlite_db_path = os.path.abspath(os.path.join(settings.STORAGE_DIR, "dcpr_db.sqlite"))
        print(f"SQLite DB Path: {sqlite_db_path}")
        # Use forward slashes for SQLite connection URI in SQLAlchemy (critical on Windows to avoid escape issues)
        clean_sqlite_path = sqlite_db_path.replace("\\", "/")
        sqlite_url = f"sqlite:///{clean_sqlite_path}"
        _engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        is_sqlite_fallback = True

    return _engine

def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal
    
    engine = get_engine()
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

def init_db():
    """Initializes tables using SQLAlchemy metadata."""
    engine = get_engine()
    # Import models here to register them with Base
    from app.db import models
    print("Creating relational database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("Relational database initialized.")

# FastAPI dependency
def get_db():
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
