import networkx as nx

class GraphValidator:
    """
    GraphValidator uses NetworkX topology check algorithms to validate
    structural completeness, identify cycles, broken references, and orphans.
    """
    def __init__(self):
        pass

    def validate(self, G):
        """
        Validates G and returns a validation summary.
        """
        broken_references = []
        orphan_nodes = []
        cycles = []
        duplicate_entities = []

        # 1. Detect Broken References
        # Check for edges pointing to non-existent nodes
        for u, v, attrs in G.edges(data=True):
            if u not in G or v not in G:
                broken_references.append({
                    "from": u,
                    "to": v,
                    "type": attrs.get("type", "RELATED_TO")
                })
        
        # Check for reference nodes targeting unresolved citations
        for node, attrs in G.nodes(data=True):
            if attrs.get("label") == "Reference":
                target = attrs.get("target_entity_id")
                if target and target not in G:
                    broken_references.append({
                        "from": node,
                        "to": target,
                        "type": "REFERENCES"
                    })

        # 2. Detect Cycles
        # Build a sub-graph of dependency relations (DEPENDS_ON, USES_FORMULA) to check circular math/rules
        dep_edges = [(u, v) for u, v, attrs in G.edges(data=True) if attrs.get("type") in ("DEPENDS_ON", "USES_FORMULA")]
        dep_subgraph = nx.DiGraph(dep_edges)
        
        try:
            cycles_generator = nx.simple_cycles(dep_subgraph)
            cycles = list(cycles_generator)
        except Exception as e:
            print(f"Warning running cycle check: {e}")

        # 3. Detect Orphan Nodes (degree is 0)
        for node in G.nodes():
            if G.degree(node) == 0:
                # Exclude standalone stubs if they are expected, but in this check we flag them
                orphan_nodes.append(node)

        # 4. Detect Duplicate Entities
        # Handled at parse time (dictionary keys), but we can search node aliases or names for duplicate properties
        seen_citations = {}
        for node, attrs in G.nodes(data=True):
            citation = attrs.get("citation")
            if citation and attrs.get("label") in ("Scheme", "Regulation"):
                if citation in seen_citations:
                    duplicate_entities.append({
                        "citation": citation,
                        "ids": [seen_citations[citation], node]
                    })
                seen_citations[citation] = node

        # 5. Density and Confidence Distribution
        density = nx.density(G)
        
        # Confidence distribution: simulate/extract from properties
        conf_dist = {
            "verified": 0,
            "needs_review": 0,
            "unreviewed": 0
        }
        for node, attrs in G.nodes(data=True):
            status = attrs.get("modeling_status", "")
            if status == "MODELED_EXECUTABLE":
                conf_dist["verified"] += 1
            elif status == "STUB":
                conf_dist["unreviewed"] += 1
            else:
                conf_dist["needs_review"] += 1

        return {
            "broken_references": broken_references,
            "cycles": cycles,
            "orphan_nodes": orphan_nodes,
            "duplicate_entities": duplicate_entities,
            "graph_density": density,
            "confidence_distribution": conf_dist,
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges()
        }
