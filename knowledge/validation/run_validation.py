import os
import sys
import json

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge.rule_engine import RuleEngine
from knowledge.validation.validation_engine import CalculationValidator
from knowledge.validation.validation_reporter import ValidationReporter

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    contract_path = os.path.join(base_dir, "knowledge", "graphs", "rule_engine_contract.json")
    validation_dir = os.path.join(base_dir, "knowledge", "validation")
    
    print("=== DCPR CALCULATION VALIDATION LAYER ===")
    print(f"Loading contract: {contract_path}")
    
    if not os.path.exists(contract_path):
        print(f"Error: Contract JSON not found at: {contract_path}")
        sys.exit(1)
        
    with open(contract_path, "r", encoding="utf-8") as f:
        contract_data = json.load(f)
        
    # Instantiate engine and validator
    engine = RuleEngine(contract_data)
    validator = CalculationValidator()
    reporter = ValidationReporter(base_output_path=os.path.join(base_dir, "knowledge"))
    
    # 5 test scenarios matching Phase 5 requirements
    scenarios = {
        "Scenario 1: Cluster Area = 5500 (Eligibility Failure)": {
            "gross_cluster_area": 5500, # below 6000 threshold
            "access_road_width": 18,
            "certified_admissible_rehabilitation_bua": 12000,
            "weighted_land_rate": 30000,
            "construction_rate": 20000,
            "fsi_base_area": 5000
        },
        "Scenario 2: Road Width = 12 (Road Access Failure)": {
            "gross_cluster_area": 8000,
            "access_road_width": 12, # below 18m threshold
            "certified_admissible_rehabilitation_bua": 12000,
            "weighted_land_rate": 30000,
            "construction_rate": 20000,
            "fsi_base_area": 5000
        },
        "Scenario 3: Valid Inputs (Successful Calculation)": {
            "gross_cluster_area": 8000,
            "access_road_width": 18,
            "certified_admissible_rehabilitation_bua": 12000,
            "weighted_land_rate": 30000,
            "construction_rate": 20000,
            "fsi_base_area": 5000
        },
        "Scenario 4: Negative Values (Validation Failure)": {
            "gross_cluster_area": -5000, # negative value
            "access_road_width": 18,
            "certified_admissible_rehabilitation_bua": 12000,
            "weighted_land_rate": 30000,
            "construction_rate": 20000,
            "fsi_base_area": 5000
        },
        "Scenario 5: Missing Inputs (Validation Failure)": {
            "access_road_width": 18,
            "certified_admissible_rehabilitation_bua": 12000,
            "weighted_land_rate": 30000,
            "construction_rate": 20000,
            "fsi_base_area": 5000
            # missing gross_cluster_area
        }
    }
    
    val_results = {}
    print("\nRunning and validating scenarios...")
    for s_name, user_inputs in scenarios.items():
        print(f"\nEvaluating {s_name}...")
        # 1. Run engine
        exec_out = engine.evaluate("33(9)", user_inputs)
        # 2. Audit output
        audit_res = validator.validate(contract_data, "33(9)", user_inputs, exec_out)
        val_results[s_name] = audit_res
        print(f"  Rule Engine Status: {exec_out['eligibility']}")
        print(f"  Validator Audit Status: {audit_res['validation_status']} (Warnings: {len(audit_res['warnings'])})")
        for w in audit_res["warnings"]:
            print(f"    - [WARNING] {w}")

    # 3. Write reports
    print("\nWriting validation report and summary...")
    reporter.write_reports(val_results)
    print("\nValidation Layer run completed successfully!")

if __name__ == "__main__":
    main()
