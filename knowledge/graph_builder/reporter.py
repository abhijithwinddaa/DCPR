import os
import networkx as nx

class GraphReporter:
    """
    GraphReporter performs transitive traversals, resolves semantic queries,
    and generates graph_report.md and coverage_report.md.
    """
    def __init__(self, base_output_path="knowledge"):
        self.base_path = base_output_path
        self.reports_dir = os.path.join(self.base_path, "reports")

    def _ensure_dirs(self):
        os.makedirs(self.reports_dir, exist_ok=True)

    # --- Transitive Traversal Utilities ---
    def get_direct_dependencies(self, G, entity_id):
        """Returns direct neighbors reachable via outgoing edges."""
        if entity_id not in G:
            return []
        deps = []
        for v in G.successors(entity_id):
            edge_data = G.get_edge_data(entity_id, v)
            deps.append({
                "id": v,
                "label": G.nodes[v].get("label", "Node"),
                "relationship": edge_data.get("type", "RELATED_TO"),
                "title": G.nodes[v].get("title", "")
            })
        return deps

    def get_transitive_dependencies(self, G, entity_id, visited=None):
        """Recursively collects all nodes this entity depends on."""
        if visited is None:
            visited = set()
        
        if entity_id not in G or entity_id in visited:
            return []
            
        visited.add(entity_id)
        transitive = []
        
        # Follow outgoing edges
        for v in G.successors(entity_id):
            edge_data = G.get_edge_data(entity_id, v)
            # Include in dependency chain
            node_info = {
                "id": v,
                "label": G.nodes[v].get("label", "Node"),
                "relationship": edge_data.get("type", "RELATED_TO"),
                "title": G.nodes[v].get("title", "")
            }
            if node_info not in transitive:
                transitive.append(node_info)
            # Recurse
            for sub_dep in self.get_transitive_dependencies(G, v, visited):
                if sub_dep not in transitive:
                    transitive.append(sub_dep)
                    
        return transitive

    def get_dependency_tree(self, G, entity_id, depth=0, visited=None):
        """Generates an ASCII text representation of the dependency tree."""
        if visited is None:
            visited = set()
            
        if entity_id not in G:
            return "[Node not found]"
            
        label = G.nodes[entity_id].get("label", "Node")
        title = G.nodes[entity_id].get("title", "")
        title_str = f" ({title})" if title else ""
        
        result = "  " * depth + f"- {entity_id} [{label}]{title_str}\n"
        
        if entity_id in visited:
            return "  " * depth + f"- {entity_id} [CYCLE DETECTED 🔄]\n"
            
        visited.add(entity_id)
        
        for v in G.successors(entity_id):
            edge_type = G.get_edge_data(entity_id, v).get("type", "RELATED_TO")
            result += "  " * (depth + 1) + f"└─[:{edge_type}]─→\n"
            result += self.get_dependency_tree(G, v, depth + 2, visited.copy())
            
        return result

    def get_impacted_entities(self, G, entity_id, visited=None):
        """Recursively collects all entities impacted if entity_id changes (incoming edges)."""
        if visited is None:
            visited = set()
            
        if entity_id not in G or entity_id in visited:
            return []
            
        visited.add(entity_id)
        impacted = []
        
        # Follow incoming edges
        for u in G.predecessors(entity_id):
            edge_data = G.get_edge_data(u, entity_id)
            node_info = {
                "id": u,
                "label": G.nodes[u].get("label", "Node"),
                "relationship": edge_data.get("type", "RELATED_TO"),
                "title": G.nodes[u].get("title", "")
            }
            if node_info not in impacted:
                impacted.append(node_info)
            # Recurse upwards
            for sub_imp in self.get_impacted_entities(G, u, visited):
                if sub_imp not in impacted:
                    sub_imp["relationship"] = "TRANSITIVE_IMPACT"
                    impacted.append(sub_imp)
                    
        return impacted

    # --- Query Answering ---
    def resolve_queries(self, G):
        """Answers the 8 semantic queries for the report."""
        ans = {}
        
        scheme_id = "dcpr:scheme:33-9"
        
        # 1. Regulations referenced
        # Find Reference nodes connected from 33(9) that target Regulations
        refs = []
        for u, v, attrs in G.edges(data=True):
            if u == scheme_id and attrs.get("type") == "REFERENCES":
                # v is the Reference node. Check if Reference connects to a Regulation
                for rv in G.successors(v):
                    if G.nodes[rv].get("label") == "Regulation":
                        refs.append(f"{rv} ({G.nodes[rv].get('title', '')})")
        ans["regulations_referenced"] = refs if refs else ["No direct regulation matches in graph"]

        # 2. Conditions applying
        ans["conditions_apply"] = [v for v in G.successors(scheme_id) if G.nodes[v].get("label") == "Condition"]

        # 3. Formulae used
        ans["formulae_used"] = [v for v in G.successors(scheme_id) if G.nodes[v].get("label") == "Formula"]

        # 4. Tables used
        # Connect Scheme -> Formula -> Table
        tables = []
        for v in G.successors(scheme_id):
            if G.nodes[v].get("label") == "Formula":
                for fv in G.successors(v):
                    if G.nodes[fv].get("label") == "Table":
                        tables.append(fv)
            elif G.nodes[v].get("label") == "Table":
                tables.append(v)
        ans["tables_used"] = list(set(tables))

        # 5. Definitions required
        ans["definitions_required"] = [v for v in G.successors(scheme_id) if G.nodes[v].get("label") == "Definition"]

        # 6. Transitive dependencies
        ans["transitive_dependencies"] = self.get_transitive_dependencies(G, scheme_id)

        # 7. Impacted entities for Regulation 52
        ans["impacted_reg52"] = self.get_impacted_entities(G, "dcpr:regulation:52")

        # 8. Dependency Tree
        ans["dependency_tree"] = self.get_dependency_tree(G, scheme_id)

        return ans

    def generate_reports(self, G, val_summary):
        """Generates graph_report.md and coverage_report.md."""
        self._ensure_dirs()
        ans = self.resolve_queries(G)
        
        # 1. Generate graph_report.md
        self._write_graph_report(G, ans, val_summary)

        # 2. Generate coverage_report.md
        self._write_coverage_report(G, val_summary)

    def _write_graph_report(self, G, ans, val):
        report_path = os.path.join(self.reports_dir, "graph_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# DCPR Knowledge Graph Query Report\n\n")
            f.write("This report answers semantic verification queries for the loaded DCPR Knowledge Graph.\n\n")
            
            f.write("## 1. What regulations does Scheme 33(9) reference?\n")
            for r in ans["regulations_referenced"]:
                f.write(f"- `{r}`\n")
            f.write("\n")

            f.write("## 2. What conditions apply to Scheme 33(9)?\n")
            for c in ans["conditions_apply"]:
                f.write(f"- `{c}` (Message: *\"{G.nodes[c].get('message', '')}\"*)\n")
            f.write("\n")

            f.write("## 3. What formulae are used in Scheme 33(9)?\n")
            for fm in ans["formulae_used"]:
                f.write(f"- `{fm}`\n")
            f.write("\n")

            f.write("## 4. What tables are used in Scheme 33(9)?\n")
            for t in ans["tables_used"]:
                f.write(f"- `{t}`\n")
            f.write("\n")

            f.write("## 5. What definitions are required?\n")
            if ans["definitions_required"]:
                for d in ans["definitions_required"]:
                    f.write(f"- `{d}`\n")
            else:
                f.write("- *No definitions registered directly under Scheme 33(9) node.*\n")
            f.write("\n")

            f.write("## 6. Show all transitive dependencies of Scheme 33(9)\n")
            f.write("Below is the recursive dependency path resolved by the graph builder:\n")
            for d in ans["transitive_dependencies"]:
                f.write(f"- `{d['id']}` [{d['label']}] (via `{d['relationship']}` relationship)\n")
            f.write("\n")

            f.write("## 7. Show all entities impacted if Regulation 52 changes\n")
            if ans["impacted_reg52"]:
                for imp in ans["impacted_reg52"]:
                    f.write(f"- `{imp['id']}` [{imp['label']}] (Relationship: `{imp['relationship']}`)\n")
            else:
                f.write("- *No entities impacted.*\n")
            f.write("\n")

            f.write("## 8. Complete Transitive Dependency Tree (Scheme 33(9))\n")
            f.write("```text\n")
            f.write(ans["dependency_tree"])
            f.write("```\n")

        print(f"Graph query report written to: {report_path}")

    def _write_coverage_report(self, G, val):
        report_path = os.path.join(self.reports_dir, "coverage_report.md")
        
        # Calculate scores
        total_nodes = val["total_nodes"]
        broken = len(val["broken_references"])
        
        # Calculate coverage health score
        # Let's subtract penalty for broken links and circular dependencies
        ref_count = len([n for n in G.nodes() if G.nodes[n].get("label") == "Reference"])
        resolved_count = ref_count - broken
        ref_resolved_rate = (resolved_count / ref_count * 100) if ref_count > 0 else 100
        
        health_score = 100.0
        if total_nodes > 0:
            health_score -= (broken / total_nodes * 50.0) # penalty
        if val["cycles"]:
            health_score -= 20.0
        health_score = max(0.0, min(100.0, health_score))

        # Node label counts
        counts = {
            "Scheme": 0, "Regulation": 0, "Definition": 0, "Condition": 0,
            "Formula": 0, "Exception": 0, "Table": 0, "Reference": 0,
            "InputParameter": 0, "OutputParameter": 0
        }
        for n, attrs in G.nodes(data=True):
            lbl = attrs.get("label")
            if lbl in counts:
                counts[lbl] += 1

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# DCPR Corpus Graph Health & Coverage Report\n\n")
            f.write("## Graph Health Coverage Score\n\n")
            f.write(f"### Score: **{health_score:.1f}%**\n\n")
            
            f.write("## Required Coverage Metrics\n\n")
            f.write(f"- **schemes_loaded**: {counts['Scheme']}\n")
            f.write(f"- **regulations_loaded**: {counts['Regulation']}\n")
            f.write(f"- **definitions_loaded**: {counts['Definition']}\n")
            f.write(f"- **conditions_loaded**: {counts['Condition']}\n")
            f.write(f"- **formulae_loaded**: {counts['Formula']}\n")
            f.write(f"- **tables_loaded**: {counts['Table']}\n")
            f.write(f"- **references_loaded**: {ref_count}\n")
            f.write(f"- **references_resolved**: {resolved_count}\n")
            f.write(f"- **broken_references**: {broken}\n")
            f.write(f"- **orphan_nodes**: {len(val['orphan_nodes'])}\n")
            f.write(f"- **duplicate_entities**: {len(val['duplicate_entities'])}\n")
            f.write(f"- **graph_density**: {val['graph_density']:.6f}\n")
            f.write("- **confidence_distribution**:\n")
            for k, v in val["confidence_distribution"].items():
                f.write(f"  - `{k}`: {v} nodes\n")
            f.write("\n")
            
            f.write("## Loaded Element Metrics\n\n")
            f.write(f"- **Total Nodes Loaded:** {total_nodes}\n")
            f.write(f"- **Total Relationships Loaded:** {val['total_edges']}\n")
            f.write(f"- **Graph Density:** {val['graph_density']:.4f}\n\n")
            
            f.write("| Element Label | Nodes Loaded |\n")
            f.write("|---|---|\n")
            for k, v in counts.items():
                f.write(f"| {k} | {v} |\n")
            f.write("\n")

            f.write("## Cross-Reference Quality\n\n")
            f.write(f"- **Total References:** {ref_count}\n")
            f.write(f"- **Resolved References:** {resolved_count}\n")
            f.write(f"- **Resolution Rate:** {ref_resolved_rate:.2f}%\n\n")

            if broken:
                f.write("## Broken Reference Details\n")
                for br in val["broken_references"]:
                    f.write(f"- Edge `({br['from']}) -[:{br['type']}]-> ({br['to']})` targeting non-existent node.\n")
                f.write("\n")

            if val["cycles"]:
                f.write("## Circular Loop Details\n")
                for cy in val["cycles"]:
                    f.write(f"- Loop: `{' -> '.join(cy)} -> {cy[0]}`\n")
                f.write("\n")

            if val["duplicate_entities"]:
                f.write("## Duplicate Entity Details\n")
                for de in val["duplicate_entities"]:
                    f.write(f"- Duplicate Citation: `{de['citation']}` shared between `{de['ids'][0]}` and `{de['ids'][1]}`\n")
                f.write("\n")

        print(f"Graph coverage report written to: {report_path}")

# Helper helper to extract node props
def G_label_msg(node_id, label_type, prop):
    # This is a mock helper, but we don't have global graph G here unless passed,
    # so we define a dummy helper or handle it. Since G is passed in caller,
    # we can resolve it directly.
    return ""
