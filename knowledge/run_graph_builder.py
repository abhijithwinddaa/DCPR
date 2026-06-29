import os
import sys
import argparse
import json

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.graph_builder.generator import GraphGenerator
from knowledge.graph_builder.loader import GraphLoader
from knowledge.graph_builder.validator import GraphValidator
from knowledge.graph_builder.reporter import GraphReporter
from knowledge.graph_builder import set_active_graph

def parse_args():
    parser = argparse.ArgumentParser(description="DCPR Graph Builder Pipeline")
    parser.add_argument("--input", type=str, default="knowledge", help="Input knowledge directory")
    parser.add_argument("--output", type=str, default="knowledge", help="Output base directory")
    return parser.parse_args()

def generate_rule_engine_contract(G, scheme_id):
    """
    Constructs the exact Rule Engine data contract structure for a scheme.
    """
    citation = G.nodes[scheme_id].get("citation", scheme_id.split(":")[-1])
    contract = {
        "scheme_id": citation,
        "scheme_uri": scheme_id,
        "conditions": [],
        "formulae": [],
        "tables": [],
        "definitions": [],
        "references": [],
        "inputs": [],
        "outputs": [],
        "facts": []
    }
    
    # Collect direct children
    for v in G.successors(scheme_id):
        if v not in G:
            continue
        label = G.nodes[v].get("label")
        properties = {k: val for k, val in G.nodes[v].items() if k != "label"}
        properties["id"] = v
        
        if label == "Condition":
            contract["conditions"].append(properties)
        elif label == "Formula":
            contract["formulae"].append(properties)
            # Find lookup tables connected to this formula
            for fv in G.successors(v):
                if fv in G and G.nodes[fv].get("label") == "Table":
                    t_props = {tk: tv for tk, tv in G.nodes[fv].items() if tk != "label"}
                    t_props["id"] = fv
                    if t_props not in contract["tables"]:
                        contract["tables"].append(t_props)
        elif label == "Table":
            if properties not in contract["tables"]:
                contract["tables"].append(properties)
        elif label == "Definition":
            contract["definitions"].append(properties)
        elif label == "Reference":
            contract["references"].append(properties)
        elif label == "InputParameter":
            contract["inputs"].append(properties)
        elif label == "OutputParameter":
            contract["outputs"].append(properties)
        elif label == "Fact":
            contract["facts"].append(properties)
            
    return contract

def main():
    args = parse_args()
    print("=== DCPR GRAPH BUILDER PIPELINE ===")
    print(f"Input Directory:  {args.input}")
    print(f"Output Directory: {args.output}")
    print("===================================\n")

    # 1. Extract elements from YAML packages
    print("Step 1: Extracting nodes & edges from YAML packages...")
    generator = GraphGenerator(input_dir=args.input)
    nodes, relationships, metadata = generator.extract()
    print(f"Extracted {len(nodes)} nodes and {len(relationships)} relationships.\n")

    # 2. Build NetworkX graph
    print("Step 2: Building Local NetworkX Directed Graph...")
    loader = GraphLoader(base_output_path=args.output)
    G = loader.load(nodes, relationships, metadata)
    # Set as global active graph for traversal utilities
    set_active_graph(G)
    print(f"Graph loaded. Node count: {G.number_of_nodes()}, Edge count: {G.number_of_edges()}\n")

    # 3. Validate Graph topology and health
    print("Step 3: Validating Graph topology & references...")
    validator = GraphValidator()
    val_summary = validator.validate(G)
    print(f"Validation complete: {len(val_summary['broken_references'])} broken references, "
          f"{len(val_summary['cycles'])} circular dependencies detected.\n")

    # 4. Generate Reports
    print("Step 4: Running traversal queries and generating reports...")
    reporter = GraphReporter(base_output_path=args.output)
    reporter.generate_reports(G, val_summary)
    print("Reports generated successfully.\n")

    # 5. Export Graph formats
    print("Step 5: Exporting GraphML, JSON, and Cypher script...")
    exported_paths = loader.export(G, metadata)
    print("Exports complete.\n")

    # 6. Generate Rule Engine Contract JSON
    print("Step 6: Generating Rule Engine Contract...")
    contracts = {}
    schemes = [n for n in G.nodes() if G.nodes[n].get("label") == "Scheme"]
    for scheme_id in schemes:
        citation = G.nodes[scheme_id].get("citation", scheme_id)
        contracts[citation] = generate_rule_engine_contract(G, scheme_id)
        
    contract_path = os.path.join(args.output, "graphs", "rule_engine_contract.json")
    os.makedirs(os.path.dirname(contract_path), exist_ok=True)
    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contracts, f, indent=2, sort_keys=False)
    print(f"Rule Engine contract exported to: {contract_path}\n")

    # 7. Print results of traversal functions to demonstrate success criteria
    print("=== Verification of Traversal Utilities ===")
    from knowledge.graph_builder import (
        get_direct_dependencies,
        get_transitive_dependencies,
        get_dependency_tree,
        get_impacted_entities
    )
    scheme_33_9 = "dcpr:scheme:33-9"
    reg_52 = "dcpr:regulation:52"
    
    print(f"\n1. Direct Dependencies of Scheme 33(9):")
    for d in get_direct_dependencies(scheme_33_9):
        print(f"  - [{d['relationship']}] -> {d['id']} ({d['label']})")
        
    print(f"\n2. Transitive Dependencies of Scheme 33(9):")
    for d in get_transitive_dependencies(scheme_33_9):
        print(f"  - {d['id']} ({d['label']})")
        
    print(f"\n3. Impacted Entities if Regulation 52 changes:")
    for imp in get_impacted_entities(reg_52):
        print(f"  - {imp['id']} ({imp['label']}) via {imp['relationship']}")
        
    print("\nGraph Builder execution completed successfully!")

if __name__ == "__main__":
    main()
