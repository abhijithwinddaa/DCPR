import os
import yaml
from datetime import datetime

class GraphGenerator:
    """
    GraphGenerator parses Canonical Knowledge Model YAML files (including stubs)
    and extracts structured nodes, relationships, and graph metadata.
    """
    def __init__(self, input_dir="knowledge"):
        self.input_dir = input_dir
        self.metadata = {
            "graph_schema_version": "1.0",
            "knowledge_model_version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generated_timestamp": datetime.utcnow().isoformat() + "Z",
            "source_hash": "ce8b6aff46d6c0e7d77998e8fb529667bbda70205cb23ab8444d65219f81b91a",
            "source_document_hash": "ce8b6aff46d6c0e7d77998e8fb529667bbda70205cb23ab8444d65219f81b91a"
        }

    def generate_stubs(self):
        """Generates mock/validation stubs for 33(7), 33(10), 33(11), and 58 if not present."""
        schemes_dir = os.path.join(self.input_dir, "schemes")
        os.makedirs(schemes_dir, exist_ok=True)
        
        stubs = {
            "33-7.yaml": {
                "schema_version": "dcpr-knowledge-model/v1",
                "package_metadata": {"package_id": "dcpr:package:33-7", "status": "DRAFT", "instrument_id": "dcpr:instrument:2034"},
                "entities": [{"id": "dcpr:scheme:33-7", "type": "SCHEME", "citation": "33(7)", "normalized_citation": "regulation:33:subregulation:7", "title": "Redevelopment of Cess Buildings under 33(7)", "semantic_links": {"reference_ids": ["ref:33-7-dep-52"]}}],
                "facts": [{"id": "dcpr:33-7:min-area", "concept_type_id": "concept:gross-cluster-area", "value": "1000"}],
                "formulae": [{"id": "dcpr:33-7:applicable-fsi", "formula_type": "RATIO", "expression": {"op": "MAX", "args": [{"kind": "LITERAL", "value": "3.0"}]}, "output_id": "applicable_fsi"}],
                "tables": [],
                "conditions": [{"id": "dcpr:33-7:area-check", "phase": "APPLICABILITY", "expression": {"op": "GTE", "args": [{"kind": "INPUT", "id": "gross_cluster_area"}, {"kind": "FACT", "id": "dcpr:33-7:min-area"}]}}],
                "inputs": [{"id": "input:gross_cluster_area", "name": "gross_cluster_area", "concept_type_id": "concept:gross-cluster-area", "value_type": "QUANTITY"}],
                "outputs": [{"id": "output:applicable_fsi", "name": "applicable_fsi", "concept_type_id": "concept:applicable-fsi", "value_type": "DECIMAL"}],
                "references": [{"id": "ref:33-7-dep-52", "from_entity_id": "dcpr:scheme:33-7", "mention_text": "depends on Regulation 52", "normalized_target_citation": "regulation:52", "target_entity_id": "dcpr:regulation:52", "reference_type": "DEPENDS_ON", "resolution_status": "RESOLVED"}]
            },
            "33-10.yaml": {
                "schema_version": "dcpr-knowledge-model/v1",
                "package_metadata": {"package_id": "dcpr:package:33-10", "status": "DRAFT", "instrument_id": "dcpr:instrument:2034"},
                "entities": [{"id": "dcpr:scheme:33-10", "type": "SCHEME", "citation": "33(10)", "normalized_citation": "regulation:33:subregulation:10", "title": "Slum Rehabilitation Scheme under 33(10)", "semantic_links": {"reference_ids": ["ref:33-10-dep-52"]}}],
                "facts": [],
                "formulae": [],
                "tables": [],
                "conditions": [],
                "inputs": [],
                "outputs": [],
                "references": [{"id": "ref:33-10-dep-52", "from_entity_id": "dcpr:scheme:33-10", "mention_text": "depends on Regulation 52", "normalized_target_citation": "regulation:52", "target_entity_id": "dcpr:regulation:52", "reference_type": "DEPENDS_ON", "resolution_status": "RESOLVED"}]
            },
            "33-11.yaml": {
                "schema_version": "dcpr-knowledge-model/v1",
                "package_metadata": {"package_id": "dcpr:package:33-11", "status": "DRAFT", "instrument_id": "dcpr:instrument:2034"},
                "entities": [{"id": "dcpr:scheme:33-11", "type": "SCHEME", "citation": "33(11)", "normalized_citation": "regulation:33:subregulation:11", "title": "Housing for Dishoused under 33(11)", "semantic_links": {"reference_ids": []}}],
                "facts": [],
                "formulae": [],
                "tables": [],
                "conditions": [],
                "inputs": [],
                "outputs": [],
                "references": []
            },
            "58.yaml": {
                "schema_version": "dcpr-knowledge-model/v1",
                "package_metadata": {"package_id": "dcpr:package:58", "status": "DRAFT", "instrument_id": "dcpr:instrument:2034"},
                "entities": [{"id": "dcpr:scheme:58", "type": "SCHEME", "citation": "58", "normalized_citation": "regulation:58", "title": "Development of Mill Lands under Regulation 58", "semantic_links": {"reference_ids": []}}],
                "facts": [],
                "formulae": [],
                "tables": [],
                "conditions": [],
                "inputs": [],
                "outputs": [],
                "references": []
            }
        }

        for fname, data in stubs.items():
            path = os.path.join(schemes_dir, fname)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                print(f"Created validation stub: {path}")

    def extract(self):
        """
        Loads all scheme and regulation YAML files.
        Returns: (nodes, relationships, metadata)
        """
        # Auto-create stubs
        self.generate_stubs()

        nodes = {}
        relationships = []

        # We also extract Regulation 52 which is a common dependency in stubs
        # to ensure it resolves and doesn't show as a broken link
        nodes["dcpr:regulation:52"] = {
            "id": "dcpr:regulation:52",
            "label": "Regulation",
            "properties": {
                "citation": "52",
                "title": "Transit Oriented Development (TOD) and Special Provisions",
                "modeling_status": "STUB"
            }
        }

        # Recursively search input directory for YAML files
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if not file.endswith((".yaml", ".yml")):
                    continue
                
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                except Exception as e:
                    print(f"Warning: Failed to load {path}: {e}")
                    continue

                if not isinstance(data, dict) or "schema_version" not in data:
                    continue

                # Process compiled or split package objects
                self._extract_from_dict(data, nodes, relationships)

        # Ensure Scheme 33(9)'s direct references are linked to external regulations
        # if they exist in reference mappings
        for ref_id, ref_node in list(nodes.items()):
            if ref_node["label"] == "Reference" and "target_entity_id" in ref_node["properties"]:
                target_id = ref_node["properties"]["target_entity_id"]
                if target_id:
                    # Create the target node as stub if missing
                    if target_id not in nodes:
                        nodes[target_id] = {
                            "id": target_id,
                            "label": "Regulation",
                            "properties": {
                                "title": f"External Regulation {target_id}",
                                "citation": target_id.split(":")[-1],
                                "modeling_status": "STUB"
                            }
                        }
                    # Link Reference -> REFERENCES -> Regulation
                    relationships.append({
                        "from": ref_id,
                        "to": target_id,
                        "type": "REFERENCES",
                        "properties": {}
                    })

        return list(nodes.values()), relationships, self.metadata

    def _extract_from_dict(self, data, nodes, relationships):
        """Helper to extract nodes/edges from loaded YAML dict structure."""
        
        # 1. Extract entities (Scheme / Regulation)
        entities = data.get("entities", [])
        # Fallback to single 'entity' block in older drafts
        if "entity" in data and isinstance(data["entity"], dict):
            entities = [data["entity"]]

        for ent in entities:
            ent_id = ent.get("id")
            if not ent_id:
                continue
            
            ent_type = ent.get("type", "REGULATION")
            label = "Scheme" if ent_type == "SCHEME" or "scheme" in ent_id else "Regulation"
            
            nodes[ent_id] = {
                "id": ent_id,
                "label": label,
                "properties": {
                    "citation": ent.get("citation", ""),
                    "title": ent.get("title", ""),
                    "modeling_status": ent.get("modeling_status", "MODELED_EXECUTABLE")
                }
            }

            # Link Scheme/Regulation to its sub-components
            self._link_sub_components(data, ent_id, nodes, relationships)

    def _link_sub_components(self, data, owner_id, nodes, relationships):
        """Helper to parse list segments and bind them to owner entity."""
        
        # 1. Definitions
        definitions = data.get("definitions", [])
        for d in definitions:
            d_id = d.get("id")
            if d_id:
                nodes[d_id] = {
                    "id": d_id,
                    "label": "Definition",
                    "properties": {"term": d.get("term", ""), "definition_text": d.get("definition_text", "")}
                }
                relationships.append({"from": owner_id, "to": d_id, "type": "RELATED_TO", "properties": {}})

        # 2. Conditions
        # Can be inline array (new schema) or nested object (old template)
        conditions = data.get("conditions", [])
        if isinstance(conditions, dict):
            # merge list from applicability, eligibility, constraints
            flat_conds = []
            for k in ("applicability", "eligibility", "constraints"):
                flat_conds.extend(conditions.get(k, []))
            conditions = flat_conds

        for c in conditions:
            c_id = c.get("id")
            if c_id:
                nodes[c_id] = {
                    "id": c_id,
                    "label": "Condition",
                    "properties": {
                        "phase": c.get("phase", "APPLICABILITY"),
                        "message": c.get("message", ""),
                        "expression": c.get("expression", {})
                    }
                }
                relationships.append({"from": owner_id, "to": c_id, "type": "HAS_CONDITION", "properties": {}})

                # If condition expression uses facts or inputs, link them as dependencies
                self._extract_expr_dependencies(c.get("expression", {}), c_id, relationships)

        # 3. Formulae
        formulae = data.get("formulae", [])
        # Fallback to 'formulas' in older drafts
        if not formulae:
            formulae = data.get("formulas", [])

        for f in formulae:
            f_id = f.get("id")
            if f_id:
                nodes[f_id] = {
                    "id": f_id,
                    "label": "Formula",
                    "properties": {
                        "formula_type": f.get("formula_type", "ARITHMETIC"),
                        "raw_expression": f.get("raw_expression", ""),
                        "expression": f.get("expression", {}),
                        "variable_bindings": f.get("variable_bindings", []),
                        "output_id": f.get("output_id", "")
                    }
                }
                relationships.append({"from": owner_id, "to": f_id, "type": "USES_FORMULA", "properties": {}})
                
                # Check variable bindings for dependencies
                for v in f.get("variable_bindings", []):
                    v_kind = v.get("source_kind")
                    v_id = v.get("source_id")
                    if v_id:
                        if v_kind == "INPUT":
                            relationships.append({"from": f_id, "to": f"input:{v_id}" if "input:" not in v_id else v_id, "type": "DEPENDS_ON", "properties": {}})
                        elif v_kind == "FACT":
                            relationships.append({"from": f_id, "to": v_id, "type": "DEPENDS_ON", "properties": {}})
                        elif v_kind == "DERIVED":
                            relationships.append({"from": f_id, "to": v_id, "type": "DEPENDS_ON", "properties": {}})

                # If formula uses lookup tables, link to Table nodes
                self._extract_expr_dependencies(f.get("expression", {}), f_id, relationships)

        # 4. Tables
        tables_list = data.get("tables", [])
        if not tables_list:
            tables_list = data.get("rate_tables", [])
            
        for t in tables_list:
            t_id = t.get("id")
            if t_id:
                nodes[t_id] = {
                    "id": t_id,
                    "label": "Table",
                    "properties": {
                        "title": t.get("title", ""),
                        "table_type": t.get("table_type", "RATE_MATRIX"),
                        "dimensions": t.get("dimensions", []),
                        "cells": t.get("cells", []),
                        "output_concept_type_id": t.get("output_concept_type_id", "")
                    }
                }
                relationships.append({"from": owner_id, "to": t_id, "type": "HAS_TABLE", "properties": {}})

        # 5. Inputs
        inputs_list = data.get("inputs", [])
        for i in inputs_list:
            i_id = i.get("id")
            if i_id:
                nodes[i_id] = {
                    "id": i_id,
                    "label": "InputParameter",
                    "properties": {
                        "name": i.get("name", ""),
                        "value_type": i.get("value_type", ""),
                        "unit": i.get("unit", ""),
                        "required": i.get("required", False),
                        "resolution_source": i.get("resolution_source", ""),
                        "constraints": i.get("constraints", [])
                    }
                }
                relationships.append({"from": owner_id, "to": i_id, "type": "HAS_INPUT", "properties": {}})

        # 6. Outputs
        outputs_list = data.get("outputs", [])
        for o in outputs_list:
            o_id = o.get("id")
            if o_id:
                nodes[o_id] = {
                    "id": o_id,
                    "label": "OutputParameter",
                    "properties": {
                        "name": o.get("name", ""),
                        "value_type": o.get("value_type", ""),
                        "producer_policy_ids": o.get("producer_policy_ids", []),
                        "nullable_statuses": o.get("nullable_statuses", []),
                        "validation_constraints": o.get("validation_constraints", [])
                    }
                }
                relationships.append({"from": owner_id, "to": o_id, "type": "HAS_OUTPUT", "properties": {}})
                
                # Link output to its producing formulas
                for p_id in o.get("producer_policy_ids", []):
                    relationships.append({"from": o_id, "to": p_id, "type": "DEPENDS_ON", "properties": {}})

        # 7. References
        references_list = data.get("references", [])
        for r in references_list:
            r_id = r.get("id")
            if r_id:
                nodes[r_id] = {
                    "id": r_id,
                    "label": "Reference",
                    "properties": {
                        "mention_text": r.get("mention_text", ""),
                        "normalized_target_citation": r.get("normalized_target_citation", ""),
                        "target_entity_id": r.get("target_entity_id"),
                        "reference_type": r.get("reference_type", "REFERENCES")
                    }
                }
                relationships.append({"from": owner_id, "to": r_id, "type": "REFERENCES", "properties": {}})

        # 8. Facts
        facts_list = data.get("facts", [])
        for f in facts_list:
            f_id = f.get("id")
            if f_id:
                nodes[f_id] = {
                    "id": f_id,
                    "label": "Fact",
                    "properties": {
                        "name": f.get("name", ""),
                        "concept_type_id": f.get("concept_type_id", ""),
                        "value_type": f.get("value_type", ""),
                        "value": f.get("value", "")
                    }
                }
                relationships.append({"from": owner_id, "to": f_id, "type": "RELATED_TO", "properties": {}})

    def _extract_expr_dependencies(self, expr, source_node_id, relationships):
        """Recursively parses AST expressions to find dependency targets."""
        if not expr or not isinstance(expr, dict):
            return
            
        # If it's an operation, recurse on args
        if "op" in expr and "args" in expr:
            op_type = expr["op"]
            # Lookups connect formula -> Table
            if op_type == "LOOKUP" and expr["args"]:
                tbl_expr = expr["args"][0]
                if tbl_expr.get("kind") == "FACT":
                    relationships.append({"from": source_node_id, "to": tbl_expr.get("id"), "type": "HAS_TABLE", "properties": {}})
            
            for arg in expr["args"]:
                self._extract_expr_dependencies(arg, source_node_id, relationships)
                
        # If it's a value, link inputs/facts/derived
        elif expr.get("kind") in ("INPUT", "FACT", "DERIVED"):
            t_id = expr.get("id")
            if t_id:
                # Ensure input: prefix matches node IDs
                if expr["kind"] == "INPUT" and "input:" not in t_id:
                    t_id = f"input:{t_id}"
                relationships.append({"from": source_node_id, "to": t_id, "type": "DEPENDS_ON", "properties": {}})
