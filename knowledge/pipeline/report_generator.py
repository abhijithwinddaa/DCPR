import os
import yaml
from jsonschema import Draft202012Validator

class ReportGenerator:
    """
    ReportGenerator runs schema validation, collects reference metrics,
    and writes validation and reference reports in Markdown.
    """
    def __init__(self, base_output_path="knowledge"):
        self.base_path = base_output_path
        self.reports_dir = os.path.join(self.base_path, "reports")

    def _ensure_dirs(self):
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, package_dict, exported_paths):
        """Generates schema validation and reference resolution reports."""
        self._ensure_dirs()
        
        # Load the schema
        schema_path = os.path.join("knowledge", "schemas", "canonical-knowledge-model.schema.yaml")
        val_errors = []
        
        if os.path.exists(schema_path):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                
                # Convert dates to strings for jsonschema validation
                def serialize_dates(data):
                    import datetime
                    if isinstance(data, dict):
                        return {k: serialize_dates(v) for k, v in data.items()}
                    elif isinstance(data, list):
                        return [serialize_dates(x) for x in data]
                    elif isinstance(data, (datetime.date, datetime.datetime)):
                        return data.isoformat()
                    return data
                
                target_serialized = serialize_dates(package_dict)
                validator = Draft202012Validator(schema)
                val_errors = list(validator.iter_errors(target_serialized))
            except Exception as e:
                val_errors = [f"Failed to run schema validation: {e}"]
        else:
            val_errors = [f"Schema file not found at: {schema_path}"]

        # Write Validation Report
        self._write_validation_report(val_errors, exported_paths)

        # Write Reference Report
        self._write_reference_report(package_dict["references"])

    def _write_validation_report(self, val_errors, exported_paths):
        report_path = os.path.join(self.reports_dir, "validation_report.md")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Ingestion Pipeline Validation Report\n\n")
            f.write(f"**Date:** {os.environ.get('CURRENT_TIME', '2026-06-20')}\n")
            
            if not val_errors:
                f.write("## Status: SUCCESS ✅\n\n")
                f.write("All generated YAML package files are fully compliant with `canonical-knowledge-model.schema.yaml`.\n\n")
            else:
                f.write("## Status: FAILED ❌\n\n")
                f.write(f"Encountered **{len(val_errors)}** validation error(s):\n\n")
                for i, err in enumerate(val_errors, 1):
                    if isinstance(err, str):
                        f.write(f"- {err}\n")
                    else:
                        path = " -> ".join([str(p) for p in err.path]) if err.path else "root"
                        f.write(f"### {i}. Error at path `{path}`\n")
                        f.write(f"- **Message:** {err.message}\n")
                        f.write(f"- **Validator:** `{err.validator}`\n\n")

            f.write("## Exported Files\n\n")
            for name, path in exported_paths.items():
                f.write(f"- **{name}:** [{os.path.basename(path)}](file:///{path.replace('\\', '/')})\n")

        print(f"Validation report written to: {report_path}")

    def _write_reference_report(self, references):
        report_path = os.path.join(self.reports_dir, "reference_report.md")
        
        resolved = [r for r in references if r["resolution_status"] == "RESOLVED"]
        external = [r for r in references if r["resolution_status"] == "EXTERNAL_UNMODELED"]
        unresolved = [r for r in references if r["resolution_status"] not in ("RESOLVED", "EXTERNAL_UNMODELED")]
        
        total = len(references)
        res_rate = ((len(resolved) + len(external)) / total * 100) if total > 0 else 100

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Cross-Reference Resolution Report\n\n")
            f.write("## Metrics Summary\n\n")
            f.write(f"- **Total References Found:** {total}\n")
            f.write(f"- **Local Resolved Links:** {len(resolved)}\n")
            f.write(f"- **External Unmodeled Links:** {len(external)}\n")
            f.write(f"- **Ambiguous/Unresolved Links:** {len(unresolved)}\n")
            f.write(f"- **Resolution Success Rate:** {res_rate:.2f}%\n\n")

            f.write("## Reference Resolution Details\n\n")
            f.write("| Reference ID | Mention Text | Target Citation | Resolved ID | Status |\n")
            f.write("|---|---|---|---|---|\n")
            
            for ref in references:
                t_id = ref["target_entity_id"] if ref["target_entity_id"] else "None"
                f.write(f"| `{ref['id']}` | \"{ref['mention_text']}\" | `{ref['normalized_target_citation']}` | `{t_id}` | **{ref['resolution_status']}** |\n")

        print(f"Reference report written to: {report_path}")
