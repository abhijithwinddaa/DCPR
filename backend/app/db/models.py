import uuid
from sqlalchemy import Column, String, BigInteger, Integer, Boolean, Date, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.postgres import Base

# Helper to get JSON type compatible with both SQLite and Postgres
def get_json_type():
    # In SQLAlchemy, JSON will automatically map to JSONB on Postgres and TEXT JSON on SQLite
    return JSON

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="PLANNER") # ADMIN, ARCHITECT, PLANNER, REGULATOR
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents = relationship("Document", back_populates="uploader")
    calculations = relationship("Calculation", back_populates="user")
    questions = relationship("Question", back_populates="user")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    storage_bucket = Column(String(100), nullable=False)
    storage_path = Column(String(512), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    sha256_checksum = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="file")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False) # DCPR, CIRCULAR, AMENDMENT, NOTIFICATION, ORDER
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship("User", back_populates="documents")
    file = relationship("UploadedFile", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    version_tag = Column(String(50), nullable=False)
    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date)
    processing_status = Column(String(50), default="PENDING") # PENDING, PROCESSING, FAILED, COMPLETED
    error_log = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="versions")
    entities = relationship("KnowledgeEntity", back_populates="version", cascade="all, delete-orphan")
    amendments = relationship("Amendment", back_populates="version", cascade="all, delete-orphan")

class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"))
    entity_uri = Column(String(255), unique=True, nullable=False)
    entity_label = Column(String(50), nullable=False) # SCHEME, REGULATION, FACT, FORMULA, TABLE, DEFINITION
    normalized_citation = Column(String(255), nullable=False)
    entity_data = Column(get_json_type(), nullable=False)
    effective_period_start = Column(Date, nullable=False)
    effective_period_end = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DocumentVersion", back_populates="entities")

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    scheme_uri = Column(String(255), nullable=False)
    input_parameters = Column(get_json_type(), nullable=False)
    output_results = Column(get_json_type(), nullable=False)
    validator_status = Column(String(50), nullable=False) # PASS, FAIL
    validation_warnings = Column(get_json_type())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="calculations")
    audit_logs = relationship("AuditLog", back_populates="calculation", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="calculation")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    calculation_id = Column(String(36), ForeignKey("calculations.id", ondelete="CASCADE"))
    trace_step = Column(Integer, nullable=False)
    rule_id = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)
    result_value = Column(String(255))
    status = Column(String(50), nullable=False)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    calculation = relationship("Calculation", back_populates="audit_logs")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    calculation_id = Column(String(36), ForeignKey("calculations.id", ondelete="SET NULL"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    question_text = Column(Text, nullable=False)
    explanation_text = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)
    was_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    calculation = relationship("Calculation", back_populates="questions")
    user = relationship("User", back_populates="questions")

class Amendment(Base):
    __tablename__ = "amendments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    amendment_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"))
    target_entity_uri = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False) # ADDED, REMOVED, MODIFIED
    diff_data = Column(get_json_type())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    version = relationship("DocumentVersion", back_populates="amendments")
