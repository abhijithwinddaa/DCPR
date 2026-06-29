# DCPR Graph Builder Package
import os
import json
import networkx as nx

_G = None

def get_graph():
    """Retrieves or loads the graph from the standard graph.json export."""
    global _G
    if _G is not None:
        return _G
        
    # Attempt to load from standard location
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_path, "graphs", "graph.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            G = nx.DiGraph()
            # Set graph metadata
            for k, v in data.get("metadata", {}).items():
                G.graph[k] = v
            # Load nodes
            for node in data.get("nodes", []):
                nid = node["id"]
                props = {k: v for k, v in node.items() if k != "id"}
                G.add_node(nid, **props)
            # Load edges
            for link in data.get("links", []):
                G.add_edge(link["source"], link["target"], **{k: v for k, v in link.items() if k not in ("source", "target")})
            _G = G
        except Exception as e:
            print(f"Warning: Failed to load graph from {json_path}: {e}")
            
    return _G

def set_active_graph(G):
    """Allows setting an in-memory graph directly (e.g. during a build run)."""
    global _G
    _G = G

def get_direct_dependencies(entity_id):
    """Returns direct dependencies of the given entity."""
    G = get_graph()
    if G is None or entity_id not in G:
        return []
    from knowledge.graph_builder.reporter import GraphReporter
    return GraphReporter().get_direct_dependencies(G, entity_id)

def get_transitive_dependencies(entity_id):
    """Recursively collects all nodes this entity depends on."""
    G = get_graph()
    if G is None or entity_id not in G:
        return []
    from knowledge.graph_builder.reporter import GraphReporter
    return GraphReporter().get_transitive_dependencies(G, entity_id)

def get_dependency_tree(entity_id):
    """Generates an ASCII text representation of the dependency tree."""
    G = get_graph()
    if G is None or entity_id not in G:
        return f"Entity {entity_id} not found in graph."
    from knowledge.graph_builder.reporter import GraphReporter
    return GraphReporter().get_dependency_tree(G, entity_id)

def get_impacted_entities(entity_id):
    """Recursively collects all entities impacted if entity_id changes."""
    G = get_graph()
    if G is None or entity_id not in G:
        return []
    from knowledge.graph_builder.reporter import GraphReporter
    return GraphReporter().get_impacted_entities(G, entity_id)
