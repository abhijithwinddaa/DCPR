import os
import hashlib
from datetime import datetime
from knowledge.pipeline.docling_adapter import DoclingAdapter

class Ingestor:
    """
    Ingestor class to manage PDF registration, checksumming,
    and delegation to the DoclingAdapter.
    """
    def __init__(self, pdf_path, release_id):
        self.pdf_path = pdf_path
        self.release_id = release_id
        self.doc_version_id = "dcpr2034:compilation:2018-12-07:dtp-copy"  # Default source mapping
        self.adapter = DoclingAdapter()

    def get_file_sha256(self):
        """Calculates the SHA-256 checksum of the PDF file."""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"Source PDF not found at: {self.pdf_path}")
        
        sha256_hash = hashlib.sha256()
        with open(self.pdf_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def ingest(self, page_numbers=None):
        """
        Ingests the PDF, computes metadata and hash, and extracts page contents.
        Returns a list of structured PageDocument-like dictionaries.
        """
        print(f"Verifying source file: {self.pdf_path}")
        file_hash = self.get_file_sha256()
        print(f"SHA-256 Checksum: {file_hash}")

        # Basic source document metadata
        source_metadata = {
            "document_version_id": self.doc_version_id,
            "instrument_id": "dcpr:instrument:2034",
            "title": "Development Control and Promotion Regulation 2034",
            "document_type": "CONSOLIDATED_COMPILATION",
            "authority": "Maharashtra Directorate of Town Planning",
            "sha256": file_hash,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "page_count": 300,  # approximate or can query PDF
            "legal_currency": "UNVERIFIED"
        }

        raw_pages = self.adapter.extract_pages(self.pdf_path, page_numbers)
        page_docs = []

        for p in raw_pages:
            # We map physical pages to estimated printed page numbers.
            # In DCPR 2034, physical page 188 corresponds to printed page 171.
            # Thus, offset is (physical page - 17). Let's calculate a dynamic printed page label.
            printed_label = str(p["page_number"] - 17) if p["page_number"] > 17 else str(p["page_number"])

            page_docs.append({
                "document_version_id": self.doc_version_id,
                "pdf_page_number": p["page_number"],
                "printed_page_label": printed_label,
                "classification": "BORN_DIGITAL",
                "width": 612,
                "height": 792,
                "raw_text": p["raw_text"],
                "blocks": p["blocks"],
                "tables": p["tables"],
                "source_metadata": source_metadata
            })

        print(f"Successfully ingested {len(page_docs)} page(s).")
        return page_docs
