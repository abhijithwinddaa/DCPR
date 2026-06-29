import os
import json
import shutil
import networkx as nx
from neo4j import GraphDatabase
from app.core.config import settings

class Neo4jConnection:
    """
    Manages the lifecycle of the Neo4j driver connection and provides
    session runners. Enforces constraints at startup.
    Falls back to a NetworkX-based in-memory and JSON-persisted graph
    if the Neo4j service is offline.
    """
    def __init__(self):
        self._driver = None
        self.use_fallback = False
        self.nx_graph = None
        self.nx_file_path = os.path.join(settings.STORAGE_DIR, "graph.json")

    def connect(self):
        if self.use_fallback:
            return

        if not self._driver:
            print(f"Connecting to Neo4j database at {settings.NEO4J_URI}...")
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Verify connection
                self._driver.verify_connectivity()
                print("Successfully connected to Neo4j.")
                # Run constraint setup
                self.setup_constraints()
            except Exception as e:
                print(f"Warning: Failed to connect to Neo4j ({e}). Falling back to local NetworkX graph.")
                self.use_fallback = True
                self._driver = None
                self._init_networkx_graph()

    def _init_networkx_graph(self):
        """Initializes the fallback NetworkX graph by copying the prebuilt one if needed."""
        self.nx_graph = nx.DiGraph()
        
        # Check if the fallback graph.json exists in storage
        if not os.path.exists(self.nx_file_path):
            # Seed it from knowledge/graphs/graph.json if available
            seed_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "knowledge", "graphs", "graph.json"
            )
            if os.path.exists(seed_path):
                print(f"Seeding local graph from {seed_path}...")
                try:
                    os.makedirs(os.path.dirname(self.nx_file_path), exist_ok=True)
                    shutil.copy(seed_path, self.nx_file_path)
                except Exception as e:
                    print(f"Failed to copy seed graph: {e}")
            else:
                # Create default empty graph JSON
                os.makedirs(os.path.dirname(self.nx_file_path), exist_ok=True)
                with open(self.nx_file_path, "w", encoding="utf-8") as f:
                    json.dump({"metadata": {}, "nodes": [], "links": []}, f, indent=2)

        # Load NetworkX from file
        if os.path.exists(self.nx_file_path):
            try:
                with open(self.nx_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Load metadata
                metadata = data.get("metadata", {})
                for k, v in metadata.items():
                    self.nx_graph.graph[k] = v
                
                # Load nodes
                for node in data.get("nodes", []):
                    nid = node["id"]
                    attrs = {k: v for k, v in node.items() if k != "id"}
                    self.nx_graph.add_node(nid, **attrs)
                
                # Load links
                for link in data.get("links", []):
                    source = link["source"]
                    target = link["target"]
                    attrs = {k: v for k, v in link.items() if k not in ["source", "target"]}
                    self.nx_graph.add_edge(source, target, **attrs)
                
                print(f"Successfully loaded fallback graph with {len(self.nx_graph.nodes)} nodes and {len(self.nx_graph.edges)} edges.")
            except Exception as e:
                print(f"Error loading graph from {self.nx_file_path}: {e}")

    def save_networkx_graph(self):
        """Persists the local NetworkX graph back to graph.json."""
        if not self.use_fallback or not self.nx_graph:
            return
        
        data = {
            "metadata": dict(self.nx_graph.graph),
            "nodes": [],
            "links": []
        }
        
        for node, attrs in self.nx_graph.nodes(data=True):
            node_data = {"id": node}
            node_data.update(attrs)
            data["nodes"].append(node_data)
        
        for u, v, attrs in self.nx_graph.edges(data=True):
            link_data = {"source": u, "target": v}
            link_data.update(attrs)
            data["links"].append(link_data)
            
        try:
            with open(self.nx_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Successfully saved fallback graph to {self.nx_file_path}")
        except Exception as e:
            print(f"Error saving graph to {self.nx_file_path}: {e}")

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def get_session(self):
        self.connect()
        if self.use_fallback:
            return None
        return self._driver.session()

    def execute_query(self, query, parameters=None):
        self.connect()
        if self.use_fallback:
            print("Running query in fallback mode (No-op on neo4j driver).")
            return []
        with self.get_session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]


    def setup_constraints(self):
        """Creates uniqueness constraints on core regulatory graph nodes at startup."""
        print("Enforcing uniqueness constraints in Neo4j graph database...")
        constraints = [
            "CREATE CONSTRAINT unique_document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT unique_scheme_id IF NOT EXISTS FOR (s:Scheme) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT unique_regulation_id IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT unique_condition_id IF NOT EXISTS FOR (c:Condition) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT unique_formula_id IF NOT EXISTS FOR (f:Formula) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT unique_table_id IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT unique_definition_id IF NOT EXISTS FOR (d:Definition) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT unique_amendment_id IF NOT EXISTS FOR (a:Amendment) REQUIRE a.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                with self._driver.session() as session:
                    session.run(constraint)
            except Exception as e:
                print(f"Warning: Failed to apply constraint '{constraint}': {e}")

# Global Neo4j Connection instance
neo4j_db = Neo4jConnection()
# Attempt connecting on initialization/import
try:
    neo4j_db.connect()
except Exception:
    pass
