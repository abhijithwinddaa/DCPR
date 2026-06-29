import os
import sys
import argparse
import json

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.rule_engine import RuleEngine
from knowledge.validation.validation_engine import CalculationValidator
from knowledge.validation.validation_reporter import ValidationReporter
from knowledge.reasoning.reasoning_engine import QwenReasoningEngine

def parse_args():
    parser = argparse.ArgumentParser(description="DCPR Knowledge Engine Final Demo")
    parser.add_argument("--area", type=float, default=8000, help="Gross cluster area in sq. m (default: 8000)")
    parser.add_argument("--road", type=float, default=18, help="Access road width in meters (default: 18)")
    parser.add_argument("--land-rate", type=float, default=30000, help="Weighted land rate in INR/sq. m (default: 30000)")
    parser.add_argument("--construction-rate", type=float, default=20000, help="ASR standard construction rate (default: 20000)")
    parser.add_argument("--rehab-bua", type=float, default=12000, help="Certified rehabilitation BUA in sq. m (default: 12000)")
    parser.add_argument("--base-area", type=float, default=5000, help="FSI base area in sq. m (default: 5000)")
    parser.add_argument("--test-all", action="store_true", help="Run the full 5 scenario validation test suite")
    parser.add_argument("--question", type=str, default="Why is applicable FSI 4.44?", help="Natural language question for explanation")
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    contract_path = os.path.join(base_dir, "knowledge", "graphs", "rule_engine_contract.json")
    
    if not os.path.exists(contract_path):
        print(f"Error: Contract JSON not found at: {contract_path}. Please run run_graph_builder.py first.")
        sys.exit(1)
        
    with open(contract_path, "r", encoding="utf-8") as f:
        contract_data = json.load(f)

    engine = RuleEngine(contract_data)
    validator = CalculationValidator()
    reasoning = QwenReasoningEngine()

    if args.test_all:
        print("=== RUNNING ALL TEST SCENARIOS (PHASE 5/6 SUITE) ===")
        # Run the standard validation suite (which also updates execution and validation reports)
        import subprocess
        subprocess.run(["python", "knowledge/validation/run_validation.py"], cwd=base_dir)
        sys.exit(0)

    # Compile user inputs
    user_inputs = {
        "gross_cluster_area": args.area,
        "access_road_width": args.road,
        "certified_admissible_rehabilitation_bua": args.rehab_bua,
        "weighted_land_rate": args.land_rate,
        "construction_rate": args.construction_rate,
        "fsi_base_area": args.base_area
    }

    print("=== DCPR KNOWLEDGE ENGINE DEMONSTRATION ===")
    print("INPUTS:")
    for k, v in user_inputs.items():
        print(f"  - {k}: {v}")
    print("===========================================\n")

    # 1. Run Rule Engine
    print("Step 1: Running Deterministic Rule Engine...")
    exec_out = engine.evaluate("33(9)", user_inputs)
    print(f"  Eligibility Result:  **{exec_out['eligibility']}**")
    print(f"  Applicable FSI:      **{exec_out['applicable_fsi']:.2f}**")
    print(f"  Maximum BUA:         **{exec_out['maximum_bua']:.2f} sq. m**")
    
    # Resolve balance BUA from trace
    balance_bua = 0.0
    for step in exec_out["rule_trace"]:
        if step.get("rule_id") == "dcpr:33-9:balance-bua":
            balance_bua = step.get("result", 0.0)
    print(f"  Balance Free-sale BUA: **{balance_bua:.2f} sq. m**\n")

    # 2. Run independent validator
    print("Step 2: Auditing with Independent Validator Layer...")
    val_out = validator.validate(contract_data, "33(9)", user_inputs, exec_out)
    print(f"  Validator Status:    **{val_out['validation_status']}**")
    print(f"  Formula math check:  **{val_out['formula_validation']}**")
    print(f"  Table lookup check:  **{val_out['table_validation']}**")
    print(f"  Warnings Flagged:     {len(val_out['warnings'])}")
    for w in val_out["warnings"]:
        print(f"    - [WARNING] {w}")
    print("")

    # 3. Query Qwen Reasoning Layer
    print("Step 3: Compiling Natural Language Explanation...")
    context_data = {
        "user_inputs": user_inputs,
        "execution_output": exec_out,
        "validation_output": val_out
    }
    explanation = reasoning.explain(args.question, context_data)
    print(explanation)
    print("\n" + "=" * 43)

    # 4. Display complete Rule Audit Trace
    print("\nStep 4: Displaying Rule Audit Trace Ledger...")
    print("| Step | Rule ID | Type | Result | Status | Message |")
    print("|---|---|---|---|---|---|")
    for trace in exec_out["rule_trace"]:
        print(f"| {trace['step']} | `{trace['rule_id']}` | {trace['type']} | `{trace.get('result')}` | **{trace['status']}** | {trace.get('message', '')} |")

if __name__ == "__main__":
    main()
