import networkx as nx
from app.db.neo4j_conn import neo4j_db

class GraphService:
    """
    GraphService bridges CKM graph generation with Neo4j container
    and local NetworkX fallback.
    """

    @staticmethod
    def load_graph_data(nodes: list, relationships: list, metadata: dict):
        """Loads node/edge sets into either Neo4j or the fallback NetworkX graph."""
        neo4j_db.connect()
        
        if neo4j_db.use_fallback:
            print("[GraphService] Syncing to local NetworkX fallback graph...")
            G = neo4j_db.nx_graph
            if G is None:
                neo4j_db.nx_graph = nx.DiGraph()
                G = neo4j_db.nx_graph
            
            # Store metadata
            for k, v in metadata.items():
                G.graph[k] = v
            
            # Load nodes
            for node in nodes:
                nid = node["id"]
                label = node["label"]
                props = {pk: pv for pk, pv in node.items() if pk not in ("id", "label")}
                # Combine props
                attrs = {"label": label}
                attrs.update(props)
                # If properties is a dictionary
                if "properties" in node:
                    attrs.update(node["properties"])
                G.add_node(nid, **attrs)
                
            # Load relationships
            for rel in relationships:
                source = rel["from"]
                target = rel["to"]
                rel_type = rel["type"]
                props = {rk: rv for rk, rv in rel.items() if rk not in ("from", "to", "type")}
                attrs = {"type": rel_type}
                attrs.update(props)
                if "properties" in rel:
                    attrs.update(rel["properties"])
                G.add_edge(source, target, **attrs)
                
            # Save fallback to disk
            neo4j_db.save_networkx_graph()
            print(f"[GraphService] Local graph saved. Node count: {len(G.nodes)}, Edge count: {len(G.edges)}")
            return True
        else:
            print("[GraphService] Syncing to active Neo4j database...")
            # Run Cypher queries
            try:
                # Clear existing graph schema if re-syncing
                neo4j_db.execute_query("MATCH (n) DETACH DELETE n")
                
                # Merge nodes
                for node in nodes:
                    nid = node["id"]
                    label = node["label"]
                    props = node.get("properties", {})
                    # Flatten standard keys into properties
                    for k, v in node.items():
                        if k not in ("id", "label", "properties"):
                            props[k] = v
                    
                    # Convert properties to cypher string representation
                    prop_strings = []
                    for pk, pv in props.items():
                        if isinstance(pv, (dict, list)):
                            import json
                            pv_str = json.dumps(pv).replace("'", "\\'")
                            prop_strings.append(f"{pk}: '{pv_str}'")
                        else:
                            escaped_pv = str(pv).replace("'", "\\'")
                            prop_strings.append(f"{pk}: '{escaped_pv}'")
                    prop_strings.append(f"graph_schema_version: '{metadata.get('graph_schema_version', '1.0')}'")
                    
                    props_str = ", ".join(prop_strings)
                    query = f"MERGE (n:{label} {{id: $id}}) ON CREATE SET n += {{{props_str}}} ON MATCH SET n += {{{props_str}}}"
                    neo4j_db.execute_query(query, {"id": nid})

                # Merge edges
                for rel in relationships:
                    source = rel["from"]
                    target = rel["to"]
                    rel_type = rel["type"]
                    query = f"MATCH (a {{id: $source}}), (b {{id: $target}}) MERGE (a)-[r:{rel_type}]->(b)"
                    neo4j_db.execute_query(query, {"source": source, "target": target})
                
                print("[GraphService] Neo4j graph synchronization complete.")
                return True
            except Exception as e:
                print(f"[GraphService] Error loading graph to Neo4j: {e}. Switching to NetworkX fallback.")
                neo4j_db.use_fallback = True
                neo4j_db._init_networkx_graph()
                return GraphService.load_graph_data(nodes, relationships, metadata)

    @staticmethod
    def get_subgraph(scheme_id: str) -> dict:
        """
        Retrieves all descendants of the target scheme node to construct a visual representation
        for React Flow rendering.
        """
        neo4j_db.connect()
        
        nodes_out = []
        edges_out = []
        visited_nodes = set()

        if neo4j_db.use_fallback:
            G = neo4j_db.nx_graph
            if G is None or scheme_id not in G:
                # If target not found in fallback, try searching case insensitive
                found = False
                for node in (G.nodes if G else []):
                    if scheme_id.lower() in node.lower() or node.lower() in scheme_id.lower():
                        scheme_id = node
                        found = True
                        break
                if not found or G is None:
                    return {"nodes": [], "edges": []}

            # Gather descendants using DFS
            descendants = nx.descendants(G, scheme_id)
            subgraph_nodes = descendants | {scheme_id}
            
            # Gather node details
            for nid in subgraph_nodes:
                attrs = G.nodes[nid]
                nodes_out.append({
                    "id": nid,
                    "label": attrs.get("label", "RegulatoryEntity"),
                    "title": attrs.get("title", nid.split(":")[-1]),
                    "citation": attrs.get("citation"),
                    "modeling_status": attrs.get("modeling_status", "UNKNOWN")
                })
                visited_nodes.add(nid)
            
            # Gather edge details
            edge_idx = 0
            for u, v, attrs in G.edges(data=True):
                if u in subgraph_nodes and v in subgraph_nodes:
                    edges_out.append({
                        "id": f"e{edge_idx}",
                        "source": u,
                        "target": v,
                        "label": attrs.get("type", "DEPENDS_ON")
                    })
                    edge_idx += 1
        else:
            try:
                # Query Neo4j for all nodes reachable from the scheme node
                query = """
                MATCH (s {id: $scheme_id})
                MATCH path = (s)-[*0..4]->(dep)
                WITH nodes(path) as ns, relationships(path) as rels
                UNWIND ns as n
                WITH DISTINCT n, rels
                UNWIND rels as r
                RETURN DISTINCT n, r
                """
                results = neo4j_db.execute_query(query, {"scheme_id": scheme_id})
                
                edge_set = set()
                for record in results:
                    node = record["n"]
                    rel = record["r"]
                    
                    nid = node["id"]
                    if nid not in visited_nodes:
                        labels = list(node.labels)
                        label = labels[0] if labels else "RegulatoryEntity"
                        nodes_out.append({
                            "id": nid,
                            "label": label,
                            "title": node.get("title", nid.split(":")[-1]),
                            "citation": node.get("citation"),
                            "modeling_status": node.get("modeling_status", "UNKNOWN")
                        })
                        visited_nodes.add(nid)
                    
                    if rel:
                        rel_id = rel.element_id
                        if rel_id not in edge_set:
                            start_node = rel.nodes[0]
                            end_node = rel.nodes[1]
                            edges_out.append({
                                "id": f"e_{rel_id}",
                                "source": start_node.get("id"),
                                "target": end_node.get("id"),
                                "label": rel.type
                            })
                            edge_set.add(rel_id)
            except Exception as e:
                print(f"[GraphService] Neo4j query error: {e}. Falling back to local NetworkX subgraph query.")
                neo4j_db.use_fallback = True
                neo4j_db._init_networkx_graph()
                return GraphService.get_subgraph(scheme_id)

        return {"nodes": nodes_out, "edges": edges_out}
