from datetime import date, datetime
from sqlalchemy.orm import Session
from app.db import models

class DBService:
    """
    Handles persistence of metadata, files, documents, CKM entities,
    zoning calculations, audit logs, and questions.
    """
    
    @staticmethod
    def get_or_create_default_user(db: Session) -> models.User:
        """Retrieves or creates a default PLANNER user for single-user environment."""
        user = db.query(models.User).filter_by(email="planner@dcpr.local").first()
        if not user:
            user = models.User(
                email="planner@dcpr.local",
                full_name="Default Planner",
                role="PLANNER"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def save_uploaded_file(db: Session, file_name: str, size: int, mime_type: str, sha256: str, path: str, storage_bucket: str = "local-pdfs") -> models.UploadedFile:
        """Saves file storage metadata. Checks for existing hash first."""
        existing = db.query(models.UploadedFile).filter_by(sha256_checksum=sha256).first()
        if existing:
            return existing
        
        uploaded = models.UploadedFile(
            storage_bucket=storage_bucket,
            storage_path=path,
            file_name=file_name,
            file_size_bytes=size,
            mime_type=mime_type,
            sha256_checksum=sha256
        )
        db.add(uploaded)
        db.commit()
        db.refresh(uploaded)
        return uploaded

    @staticmethod
    def create_document(db: Session, title: str, doc_type: str, file_id: str, user_id: str) -> models.Document:
        """Creates a document record."""
        doc = models.Document(
            title=title,
            document_type=doc_type,
            uploaded_by=user_id,
            file_id=file_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def create_document_version(db: Session, doc_id: str, tag: str, start_date: date) -> models.DocumentVersion:
        """Creates a new document version lineage row."""
        version = models.DocumentVersion(
            document_id=doc_id,
            version_tag=tag,
            effective_start_date=start_date,
            processing_status="PENDING"
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def update_version_status(db: Session, version_id: str, status: str, error_log: str = None) -> models.DocumentVersion:
        """Updates the document processing status and error log."""
        version = db.query(models.DocumentVersion).filter_by(id=version_id).first()
        if version:
            version.processing_status = status
            if error_log:
                version.error_log = error_log
            db.commit()
            db.refresh(version)
        return version

    @staticmethod
    def save_knowledge_entities(db: Session, version_id: str, entities_list: list) -> int:
        """
        Saves a list of CKM entity dictionaries in the relational schema.
        Overwrites entities with matching entity_uri.
        """
        count = 0
        for ent in entities_list:
            uri = ent.get("entity_uri")
            
            # Check if entity already exists
            existing = db.query(models.KnowledgeEntity).filter_by(entity_uri=uri).first()
            if existing:
                existing.version_id = version_id
                existing.entity_label = ent.get("entity_label")
                existing.normalized_citation = ent.get("normalized_citation")
                existing.entity_data = ent.get("entity_data")
                existing.effective_period_start = ent.get("effective_period_start", date(2018, 12, 7))
                existing.effective_period_end = ent.get("effective_period_end")
            else:
                new_entity = models.KnowledgeEntity(
                    version_id=version_id,
                    entity_uri=uri,
                    entity_label=ent.get("entity_label"),
                    normalized_citation=ent.get("normalized_citation"),
                    entity_data=ent.get("entity_data"),
                    effective_period_start=ent.get("effective_period_start", date(2018, 12, 7)),
                    effective_period_end=ent.get("effective_period_end")
                )
                db.add(new_entity)
            count += 1
        db.commit()
        return count

    @staticmethod
    def get_knowledge_entity_by_uri(db: Session, uri: str) -> models.KnowledgeEntity:
        """Fetches a specific canonical knowledge entity by its URI."""
        return db.query(models.KnowledgeEntity).filter_by(entity_uri=uri).first()

    @staticmethod
    def get_entities_by_label(db: Session, label: str) -> list[models.KnowledgeEntity]:
        """Fetches all entities matching a classification label (e.g. SCHEME, TABLE)."""
        return db.query(models.KnowledgeEntity).filter_by(entity_label=label).all()

    @staticmethod
    def save_calculation(db: Session, scheme_uri: str, inputs: dict, outputs: dict, user_id: str = None) -> models.Calculation:
        """
        Persists a zoning calculation run and inserts the full step trace
        into the audit_logs table.
        """
        validator_status = "PASS" if outputs.get("eligibility") == "ELIGIBLE" else "FAIL"
        
        calc = models.Calculation(
            user_id=user_id,
            scheme_uri=scheme_uri,
            input_parameters=inputs,
            output_results=outputs,
            validator_status=validator_status,
            validation_warnings=outputs.get("constraints", [])
        )
        db.add(calc)
        db.commit()
        db.refresh(calc)
        
        # Save audit logs for the calculation steps
        trace = outputs.get("rule_trace", [])
        for step in trace:
            audit = models.AuditLog(
                calculation_id=calc.id,
                trace_step=step.get("step"),
                rule_id=step.get("rule_id"),
                rule_type=step.get("type"),
                result_value=str(step.get("result")),
                status=step.get("status"),
                message=step.get("message")
            )
            db.add(audit)
        
        db.commit()
        return calc

    @staticmethod
    def save_question(db: Session, calc_id: str, question: str, answer: str, model: str, was_fallback: bool, user_id: str = None) -> models.Question:
        """Persists a Q&A session fact."""
        q = models.Question(
            calculation_id=calc_id,
            user_id=user_id,
            question_text=question,
            explanation_text=answer,
            model_name=model,
            was_fallback=was_fallback
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        return q

    @staticmethod
    def get_calculation_history(db: Session, limit: int = 20) -> list[models.Calculation]:
        """Fetches the latest calculations order by date."""
        return db.query(models.Calculation).order_by(models.Calculation.created_at.desc()).limit(limit).all()
