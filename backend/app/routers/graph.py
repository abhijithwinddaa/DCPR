from fastapi import APIRouter, HTTPException
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/{node_id:path}")
def get_subgraph(node_id: str):
    """
    Returns the transitive dependencies (descendant nodes and edges) 
    centered around the selected scheme or regulation node.
    """
    # E.g. node_id = "dcpr:scheme:33-9" or "33-9"
    clean_node_id = node_id
    if not node_id.startswith("dcpr:"):
        # Fuzzy format it
        if "33(9)" in node_id or "33-9" in node_id:
            clean_node_id = "dcpr:scheme:33-9"
        else:
            clean_node_id = f"dcpr:scheme:{node_id}"

    print(f"[GraphRouter] Fetching subgraph for: {clean_node_id}")
    subgraph = GraphService.get_subgraph(clean_node_id)
    
    if not subgraph or not subgraph["nodes"]:
        # Try finding any default scheme if empty
        print(f"[GraphRouter] Subgraph for '{clean_node_id}' is empty. Seeding default scheme...")
        subgraph = GraphService.get_subgraph("dcpr:scheme:33-9")

    return subgraph
