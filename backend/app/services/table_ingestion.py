from typing import List, Dict, Any

class PurposeSummarizedTablePipeline:
    """
    Extracts multi-page tables, attaches operational purpose summaries, and chunks text cleanly.
    """

    @classmethod
    def _generate_functional_purpose_summary(cls, md_table: str) -> str:
        lines = [l.strip() for l in md_table.split("\n") if "|" in l]
        if len(lines) >= 2:
            headers = [h.strip() for h in lines[0].split("|") if h.strip()]
            return f"Statutory matrix table computing parameters ({', '.join(headers[:4])}) to establish permissible caps and multipliers."
        return "Numerical calculation table defining regulatory thresholds and incentive rates."

    @classmethod
    def process_pdf_with_purpose_tables(cls, pdf_path: str) -> List[Dict[str, Any]]:
        processed_chunks = []
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    text = page.extract_text() or ""

                    for t in tables:
                        md_lines = []
                        for row in t:
                            clean_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
                            md_lines.append("| " + " | ".join(clean_row) + " |")
                        
                        if md_lines:
                            md_table = "\n".join(md_lines)
                            purpose_summary = cls._generate_functional_purpose_summary(md_table)
                            
                            processed_chunks.append({
                                "text": f"### 📊 REGULATORY TABLE SUMMARY\n**Purpose:** {purpose_summary}\n\n{md_table}",
                                "is_table": True,
                                "table_summary": purpose_summary,
                                "page": page_idx,
                                "section": "Statutory Calculation Matrix"
                            })

                    if text.strip():
                        processed_chunks.append({
                            "text": text.strip(),
                            "is_table": False,
                            "page": page_idx,
                            "section": "Statutory Regulations"
                        })
        except ImportError:
            print("[TablePipeline] Install pdfplumber or docling for table extraction.")
            
        return processed_chunks
