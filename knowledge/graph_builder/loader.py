import os
import json
import networkx as nx

class GraphLoader:
    """
    GraphLoader loads extracted node/edge sets into a networkx.DiGraph
    and handles exporting to Cypher, JSON, and GraphML.
    """
    def __init__(self, base_output_path="knowledge"):
        self.base_path = base_output_path
        self.graphs_dir = os.path.join(self.base_path, "graphs")

    def _ensure_dirs(self):
        os.makedirs(self.graphs_dir, exist_ok=True)

    def load(self, nodes, relationships, metadata):
        """
        Loads components into a NetworkX directed graph.
        """
        G = nx.DiGraph()
        
        # Save metadata as graph-level attributes
        for k, v in metadata.items():
            G.graph[k] = v

        for node in nodes:
            nid = node["id"]
            # Save ID as node key, label and properties as attributes
            G.add_node(nid, label=node["label"], **node["properties"])

        for edge in relationships:
            G.add_edge(edge["from"], edge["to"], type=edge["type"], **edge["properties"])

        return G

    def export(self, G, metadata):
        """
        Exports the NetworkX graph to Cypher, JSON, and GraphML files.
        """
        self._ensure_dirs()
        exported_paths = {}

        # 1. Export Cypher Script (dcpr_graph.cypher)
        cypher_path = os.path.join(self.graphs_dir, "dcpr_graph.cypher")
        self._export_cypher(G, metadata, cypher_path)
        exported_paths["cypher"] = cypher_path

        # 2. Export JSON Format (graph.json)
        json_path = os.path.join(self.graphs_dir, "graph.json")
        self._export_json(G, metadata, json_path)
        exported_paths["json"] = json_path

        # 3. Export GraphML (graph.graphml)
        graphml_path = os.path.join(self.graphs_dir, "graph.graphml")
        self._export_graphml(G, graphml_path)
        exported_paths["graphml"] = graphml_path

        return exported_paths

    def _export_cypher(self, G, metadata, path):
        """Generates Cypher query script to populate Neo4j."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("// DCPR Knowledge Graph Import Script\n")
            f.write(f"// Generated at: {metadata['generated_at']}\n")
            f.write(f"// Graph Schema Version: {metadata['graph_schema_version']}\n")
            f.write(f"// Source Hash: {metadata['source_hash']}\n\n")

            f.write("// 1. Setup Constraints & Indexes\n")
            f.write("CREATE CONSTRAINT unique_entity_id IF NOT EXISTS FOR (e:RegulatoryEntity) REQUIRE e.id IS UNIQUE;\n")
            f.write("CREATE INDEX index_citation IF NOT EXISTS FOR (e:RegulatoryEntity) ON (e.citation);\n\n")

            f.write("// 2. Create/Merge Nodes\n")
            for node, attrs in G.nodes(data=True):
                label = attrs.get("label", "RegulatoryEntity")
                props = {k: v for k, v in attrs.items() if k != "label"}
                # Convert properties to cypher string representation
                prop_strings = []
                for pk, pv in props.items():
                    escaped_pv = str(pv).replace("'", "\\'")
                    prop_strings.append(f"{pk}: '{escaped_pv}'")
                prop_strings.append(f"graph_schema_version: '{metadata['graph_schema_version']}'")
                prop_strings.append(f"knowledge_model_version: '{metadata['knowledge_model_version']}'")
                
                props_str = ", ".join(prop_strings)
                f.write(f"MERGE (n:{label} {{id: '{node}'}}) ON CREATE SET n += {{{props_str}}};\n")

            f.write("\n// 3. Create Relationships\n")
            for u, v, attrs in G.edges(data=True):
                rel_type = attrs.get("type", "RELATED_TO")
                f.write(f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) MERGE (a)-[r:{rel_type}]->(b);\n")
                
        print(f"Exported Cypher script to: {path}")

    def _export_json(self, G, metadata, path):
        """Exports graph in standard node-link JSON format."""
        data = {
            "metadata": metadata,
            "nodes": [],
            "links": []
        }

        for node, attrs in G.nodes(data=True):
            node_data = {"id": node}
            node_data.update(attrs)
            data["nodes"].append(node_data)

        for u, v, attrs in G.edges(data=True):
            link_data = {"source": u, "target": v}
            link_data.update(attrs)
            data["links"].append(link_data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            
        print(f"Exported JSON graph to: {path}")

    def _export_graphml(self, G, path):
        """Exports graph in standard XML GraphML format."""
        # Convert attributes to strings so GraphML writer doesn't crash on dicts
        G_graphml = nx.DiGraph()
        for node, attrs in G.nodes(data=True):
            clean_attrs = {}
            for k, v in attrs.items():
                clean_attrs[k] = str(v)
            G_graphml.add_node(node, **clean_attrs)

        for u, v, attrs in G.edges(data=True):
            clean_attrs = {}
            for k, v in attrs.items():
                clean_attrs[k] = str(v)
            G_graphml.add_edge(u, v, **clean_attrs)

        nx.write_graphml(G_graphml, path)
        print(f"Exported GraphML to: {path}")
