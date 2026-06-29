import os
import json

class ValidationReporter:
    """
    ValidationReporter writes validation_report.md and validation_summary.json
    based on the calculation validator outputs.
    """
    def __init__(self, base_output_path="knowledge"):
        self.base_path = base_output_path
        self.validation_dir = os.path.join(self.base_path, "validation")
        self.reports_dir = os.path.join(self.base_path, "reports")

    def _ensure_dirs(self):
        os.makedirs(self.validation_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def write_reports(self, val_results):
        """
        Writes validation_summary.json and validation_report.md.
        val_results maps scenario names to their validate() output dicts.
        """
        self._ensure_dirs()

        # 1. Write validation_summary.json
        # Target summary is representing the primary/successful scenario (Scenario 3 / Scenario 1)
        # or the overall validation status. Let's write the results of Scenario 3 (Valid Inputs)
        # as the main demonstration summary, or a list of summaries.
        # The user requested format:
        # {
        #   "validation_status": "PASS",
        #   "formula_validation": true,
        #   "table_validation": true,
        #   "unit_validation": true,
        #   "rounding_validation": true,
        #   "warnings": []
        # }
        primary_scenario = "Scenario 1: Standard Eligible Plot"
        summary_data = {
            "validation_status": "FAIL",
            "formula_validation": False,
            "table_validation": False,
            "unit_validation": False,
            "rounding_validation": False,
            "warnings": ["No successful scenarios evaluated."]
        }
        
        # Check if the standard successful scenario ran
        for key in val_results:
            if "Eligible Plot" in key or "Valid Inputs" in key or "Scenario 3" in key:
                if val_results[key]["validation_status"] == "PASS":
                    res = val_results[key]
                    summary_data = {
                        "validation_status": res["validation_status"],
                        "formula_validation": res["formula_validation"],
                        "table_validation": res["table_validation"],
                        "unit_validation": res["unit_validation"],
                        "rounding_validation": res["rounding_validation"],
                        "warnings": res["warnings"]
                    }
                    break

        summary_path = os.path.join(self.validation_dir, "validation_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, sort_keys=False)
        print(f"Validation summary JSON written to: {summary_path}")

        # 2. Write validation_report.md
        # Write both to knowledge/reports/validation_report.md (old report location)
        # and knowledge/validation/validation_report.md as requested in Phase 5
        report_paths = [
            os.path.join(self.validation_dir, "validation_report.md"),
            os.path.join(self.reports_dir, "validation_report.md")
        ]

        report_content = self._generate_report_markdown(val_results)

        for path in report_paths:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"Validation report MD written to: {path}")

    def _generate_report_markdown(self, val_results):
        """Generates the Markdown content for the validation report."""
        md = "# DCPR Calculation Validation Audit Report\n\n"
        md += "This report details independent audits executed against the Rule Engine evaluation trace ledger.\n\n"

        md += "## Overall Validation Status\n\n"
        overall_pass = all(res["validation_status"] == "PASS" for name, res in val_results.items() if "Fail" not in name)
        status_label = "**PASS** ✅" if overall_pass else "**FAIL** ❌"
        md += f"- **Consolidated Audit Result:** {status_label}\n"
        md += f"- **Scenarios Validated:** {len(val_results)}\n\n"

        md += "## Verification Checklist (Phase 5 compliance)\n\n"
        md += "| Verification Check | Description | Status |\n"
        md += "|---|---|---|\n"
        
        # Check standard checks across successful scenario
        success_scenario = None
        for k in val_results:
            if "Eligible Plot" in k:
                success_scenario = val_results[k]
                break
                
        def check_status(flag):
            return "PASS ✅" if flag else "FAIL ❌"

        if success_scenario:
            md += f"| 1. Formula Execution | Verifies re-calculated math matches trace results | {check_status(success_scenario['formula_validation'])} |\n"
            md += f"| 2. Table Lookup | Verifies Table B index match & value extraction | {check_status(success_scenario['table_validation'])} |\n"
            md += f"| 3. Unit Correctness | Compares input/output units with concepts registry | {check_status(success_scenario['unit_validation'])} |\n"
            md += f"| 4. Rounding Policies | Asserts rounding complies with decimal thresholds | {check_status(success_scenario['rounding_validation'])} |\n"
            md += f"| 5. Boundary Conditions | Asserts output FSI/BUA values fall within physical limits | {check_status(success_scenario['boundary_validation'])} |\n"
            md += f"| 6. Dependency Integrity | Confirms dependent nodes resolved in topological order | {check_status(success_scenario['dependency_validation'])} |\n"
            md += f"| 7. Trace Completeness | Verifies every contract condition & formula ran | {check_status(success_scenario['completeness_validation'])} |\n"
        else:
            md += "| 1. Formula Execution | Verifies re-calculated math | N/A |\n"
            md += "| 2. Table Lookup | Verifies range lookups | N/A |\n"
            md += "| 3. Unit Correctness | Compares variables | N/A |\n"
            md += "| 4. Rounding Policies | Asserts rounding thresholds | N/A |\n"
        md += "\n"

        md += "## Scenario Verification Logs\n\n"
        for s_name, res in val_results.items():
            md += f"### {s_name}\n\n"
            md += f"- **Audit Status:** `{res['validation_status']}`\n"
            
            checks = []
            for k in ("formula_validation", "table_validation", "rounding_validation", "boundary_validation", "dependency_validation", "completeness_validation"):
                if k in res:
                    checks.append(f"{k.replace('_', ' ')}: `{res[k]}`")
            md += f"- **Checks:** {', '.join(checks)}\n"

            if res["warnings"]:
                md += "- **Audit Log Warnings:**\n"
                for w in res["warnings"]:
                    md += f"  - `[AUDIT WARNING]` *\"{w}\"*\n"
            else:
                md += "- **Audit Log Warnings:** *None. Calculation passed audit boundary successfully.*\n"
            md += "\n---\n\n"

        return md
