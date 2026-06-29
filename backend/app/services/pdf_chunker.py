import re
from app.core.config import settings

class PDFChunker:
    """
    Splits pre-extracted document page structures into semantic, metadata-tagged text chunks.
    Target chunk size: ~1000 tokens (~4000 chars), overlap: ~100 tokens (~400 chars).
    """

    def __init__(self, target_chars: int = 4000, overlap_chars: int = 400):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def chunk(self, page_docs: list[dict]) -> list[dict]:
        if not page_docs:
            return []

        # 1. Strip repetitive headers/footers across pages
        cleaned_pages = self._strip_headers_footers(page_docs)

        # 2. Extract linear stream of structural elements (paragraphs, headings, tables)
        elements = self._extract_elements(cleaned_pages)

        # 3. Assemble elements into overlapping chunks while maintaining section context and table integrity
        chunks = self._build_chunks(elements)
        return chunks

    def _strip_headers_footers(self, page_docs: list[dict]) -> list[dict]:
        """Detects and removes lines repeated across 3+ consecutive pages."""
        if len(page_docs) < 3:
            return page_docs

        line_counts = {}
        for p in page_docs:
            lines = set(p.get("raw_text", "").splitlines())
            for line in lines:
                clean_l = line.strip()
                if len(clean_l) > 10 and not clean_l.isdigit():
                    line_counts[clean_l] = line_counts.get(clean_l, 0) + 1

        repeated_lines = {l for l, count in line_counts.items() if count >= max(3, len(page_docs) * 0.4)}

        cleaned_pages = []
        for p in page_docs:
            p_copy = dict(p)
            raw_text = p.get("raw_text", "")
            if repeated_lines and raw_text:
                filtered_lines = [l for l in raw_text.splitlines() if l.strip() not in repeated_lines]
                p_copy["raw_text"] = "\n".join(filtered_lines)
            cleaned_pages.append(p_copy)

        return cleaned_pages

    def _extract_elements(self, page_docs: list[dict]) -> list[dict]:
        """Flattens page structures into a chronological sequence of text elements."""
        elements = []
        current_section = "General Regulations"

        for p_idx, p in enumerate(page_docs):
            page_num = p.get("pdf_page_number", p_idx + 1)
            blocks = p.get("blocks", [])
            tables = p.get("tables", [])

            # Process block elements
            if blocks:
                for b in blocks:
                    b_type = b.get("type", "paragraph")
                    text = b.get("text", "").strip()
                    if not text or len(text) < 5:
                        continue

                    # Heading detection & section update
                    if b_type == "heading" or self._is_heading_pattern(text):
                        current_section = text[:100]
                        elements.append({
                            "type": "heading",
                            "text": text,
                            "page": page_num,
                            "section": current_section
                        })
                    else:
                        elements.append({
                            "type": "paragraph",
                            "text": text,
                            "page": page_num,
                            "section": current_section
                        })
            else:
                # Fallback if block parser did not extract blocks but raw_text exists
                raw_text = p.get("raw_text", "").strip()
                if raw_text:
                    paragraphs = [para.strip() for para in raw_text.split("\n\n") if para.strip()]
                    for para in paragraphs:
                        if self._is_heading_pattern(para):
                            current_section = para[:100]
                            elements.append({
                                "type": "heading",
                                "text": para,
                                "page": page_num,
                                "section": current_section
                            })
                        else:
                            elements.append({
                                "type": "paragraph",
                                "text": para,
                                "page": page_num,
                                "section": current_section
                            })

            # Process table elements (keep tables intact as single elements)
            for t in tables:
                table_str = self._format_table_as_string(t)
                if table_str.strip():
                    elements.append({
                        "type": "table",
                        "text": table_str,
                        "page": page_num,
                        "section": current_section
                    })

        # Cross-page paragraph continuation merge
        merged_elements = []
        for el in elements:
            if (merged_elements and 
                merged_elements[-1]["type"] == "paragraph" and 
                el["type"] == "paragraph" and 
                not merged_elements[-1]["text"].endswith((".", ":", ";", "?", "!")) and 
                el["text"][0].islower()):
                # Merge paragraphs across page boundary
                merged_elements[-1]["text"] += " " + el["text"]
            else:
                merged_elements.append(el)

        return merged_elements

    def _build_chunks(self, elements: list[dict]) -> list[dict]:
        """Groups elements into target_chars chunks with overlap."""
        chunks = []
        curr_chunk_text = ""
        curr_page = 1
        curr_section = "General"
        chunk_idx = 0

        for el in elements:
            text = el["text"]
            page = el["page"]
            section = el["section"]

            if not curr_chunk_text:
                curr_chunk_text = text
                curr_page = page
                curr_section = section
            elif len(curr_chunk_text) + len(text) <= self.target_chars:
                curr_chunk_text += "\n\n" + text
            else:
                # Flush current chunk
                chunks.append({
                    "chunk_idx": chunk_idx,
                    "text": curr_chunk_text,
                    "page": curr_page,
                    "section": curr_section,
                    "char_count": len(curr_chunk_text)
                })
                chunk_idx += 1

                # Start next chunk with overlap from end of current chunk
                overlap_text = curr_chunk_text[-self.overlap_chars:] if len(curr_chunk_text) > self.overlap_chars else ""
                curr_chunk_text = (overlap_text + "\n\n" + text).strip()
                curr_page = page
                curr_section = section

        if curr_chunk_text.strip():
            chunks.append({
                "chunk_idx": chunk_idx,
                "text": curr_chunk_text,
                "page": curr_page,
                "section": curr_section,
                "char_count": len(curr_chunk_text)
            })

        return chunks

    def _is_heading_pattern(self, text: str) -> bool:
        pattern = r"^(Regulation|\d+[\(\-]\d+\)?|Table|Appendix|Clause|Section|Part|Scheme)\b"
        return bool(re.search(pattern, text, re.IGNORECASE)) and len(text) < 120

    def _format_table_as_string(self, table_grid: list) -> str:
        rows = []
        for row in table_grid:
            if isinstance(row, list):
                clean_cells = [str(cell).replace('\n', ' ').strip() for cell in row if cell is not None]
                if any(clean_cells):
                    rows.append(" | ".join(clean_cells))
        return "\n".join(rows)
