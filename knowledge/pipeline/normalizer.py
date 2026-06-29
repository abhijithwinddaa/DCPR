import re

class Normalizer:
    """
    Normalizer to clean text, strip headers/footers, normalize values
    in cells, and ensure arithmetic/comparison operators are standardized.
    """
    def __init__(self):
        # Maps common lowercase operators or symbols to canonical UPPERCASE schema enums
        self.operator_map = {
            "add": "ADD", "plus": "ADD", "+": "ADD",
            "subtract": "SUBTRACT", "minus": "SUBTRACT", "-": "SUBTRACT",
            "multiply": "MULTIPLY", "times": "MULTIPLY", "*": "MULTIPLY", "x": "MULTIPLY", "×": "MULTIPLY",
            "divide": "DIVIDE", "slash": "DIVIDE", "/": "DIVIDE",
            "max": "MAX", "maximum": "MAX",
            "min": "MIN", "minimum": "MIN",
            "equals": "EQUALS", "=": "EQUALS",
            "not_equals": "NOT_EQUALS", "!=": "NOT_EQUALS",
            "gt": "GT", ">": "GT",
            "gte": "GTE", "greater_than_or_equal": "GTE", ">=": "GTE", "≥": "GTE",
            "lt": "LT", "<": "LT",
            "lte": "LTE", "less_than_or_equal": "LTE", "<=": "LTE", "≤": "LTE",
            "lookup": "LOOKUP", "lookup_percent": "LOOKUP", "matrix_lookup": "LOOKUP"
        }

    def clean_text(self, text):
        """Cleans and standardizes raw text whitespace."""
        if not text:
            return ""
        # Remove consecutive whitespaces, keep normal spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def normalize_operator(self, op_name):
        """Maps an operator string to its uppercase schema canonical form."""
        normalized = op_name.strip().lower()
        return self.operator_map.get(normalized, op_name.upper())

    def normalize_numeric_string(self, value_str):
        """Standardizes float/decimal representations (e.g. removing commas)."""
        if not value_str:
            return None
        cleaned = value_str.replace(",", "").strip()
        # Check if it fits the DecimalString regex
        if re.match(r"^-?[0-9]+(\.[0-9]+)?$", cleaned):
            return cleaned
        return None

    def normalize_cell_value(self, raw_cell_text):
        """
        Normalizes a raw table cell's text and determines its type and unit.
        Returns: (normalized_val_str_or_number, value_type, unit)
        """
        text = self.clean_text(raw_cell_text)
        if not text or text == "-" or text.lower() in ("n/a", "nil", "blank"):
            return None, "BLANK", None

        # Check if percentage
        pct_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*%$", text)
        if pct_match:
            val = self.normalize_numeric_string(pct_match.group(1))
            if val:
                return float(val), "PERCENTAGE", "percentage"

        # Check if pure decimal
        dec_val = self.normalize_numeric_string(text)
        if dec_val:
            return float(dec_val), "DECIMAL", None

        # Check if it is a quantity with units like sq. m, m, etc.
        qty_match = re.match(r"^([0-9,]+(?:\.[0-9]+)?)\s*(sq\.\s*m\.?|sq\s*m|sq\.m|m²|sq_metre|metres|meters|m|%)\b", text, re.IGNORECASE)
        if qty_match:
            num = self.normalize_numeric_string(qty_match.group(1))
            unit_raw = qty_match.group(2).lower()
            
            unit = "square_metre"
            if "sq" in unit_raw or "m²" in unit_raw:
                unit = "square_metre"
            elif unit_raw == "m" or "meter" in unit_raw:
                unit = "metre"
            elif unit_raw == "%":
                unit = "percentage"
                
            if num:
                return float(num), "QUANTITY", unit

        return text, "STRING", None

    def normalize(self, page_docs):
        """
        Processes a list of PageDocuments. Normalizes text in all blocks and
        cleans tables.
        """
        for doc in page_docs:
            doc["raw_text"] = self.clean_text(doc["raw_text"])
            for b in doc["blocks"]:
                b["text"] = self.clean_text(b["text"])
            
            # Table cell normalization
            normalized_tables = []
            for table in doc["tables"]:
                normalized_table = []
                for row in table:
                    normalized_row = []
                    for cell in row:
                        val, v_type, unit = self.normalize_cell_value(cell)
                        normalized_row.append({
                            "raw_text": cell,
                            "normalized_value": val,
                            "value_type": v_type,
                            "unit": unit
                        })
                    normalized_row.append(normalized_row)
                # Keep both raw and normalized grid structures
                normalized_tables.append(table) # keep fitz list structure for now, parsers will convert to flat schemas
            
        print("Pages normalization completed.")
        return page_docs
