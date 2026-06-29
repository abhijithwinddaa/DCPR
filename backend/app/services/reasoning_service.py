import os
import sys
from typing import Optional
from app.core.config import settings

# Add workspace root directory (4 levels up) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from knowledge.reasoning.reasoning_engine import QwenReasoningEngine

class ReasoningService:
    """
    Service wrapper for natural language explainability.
    Queries local Ollama using Qwen, falling back to trace-based explanation if offline.
    """
    _engine_instance = None

    @classmethod
    def get_engine(cls) -> QwenReasoningEngine:
        return QwenReasoningEngine(
            ollama_url=settings.OLLAMA_URL,
            model_name=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )

    @classmethod
    def explain(cls, question: str, inputs: dict, outputs: dict, validation_status: dict, calculation_id: str = None) -> str:
        """
        Generates an explanation for the calculation output or a general question using the graph.
        """
        engine = cls.get_engine()
        
        # Pull graph context if it's a general question or contains keywords
        graph_context = cls.get_graph_context_for_question(question)
        
        context_data = {
            "user_inputs": inputs,
            "execution_output": outputs,
            "validation_output": validation_status,
            "graph_context": graph_context
        }
        print(f"[ReasoningService] Generating explanation for question: {question}...")
        return engine.explain(question, context_data)

    @classmethod
    def rag_explain(cls, question: str, document_id: Optional[str] = None, top_k: int = 5) -> dict:
        """
        Executes hybrid retrieval (BM25 + ChromaDB + CrossEncoder) and grounded reasoning.
        """
        import asyncio
        return asyncio.run(cls.rag_explain_async(question, document_id, top_k))

    @classmethod
    async def rag_explain_async(cls, question: str, document_id: Optional[str] = None, top_k: int = 5) -> dict:
        """
        Asynchronous hybrid retrieval (BM25 + ChromaDB + CrossEncoder) and grounded reasoning.
        """
        from app.services.vector_service import vector_service
        from app.services.query_rewriter import ProductionQueryRewriterService
        from app.services.hybrid_search import hybrid_search_engine
        
        engine = cls.get_engine()

        # 1. Asynchronous Query Rewriting (Silent LLM middleware + Dictionary Lookup)
        rewritten_payload = await ProductionQueryRewriterService.rewrite_query_async(question)
        search_query = rewritten_payload.normalized_query

        # 2. Hybrid Retrieval (BM25 Sparse + ChromaDB Dense + RRF + CrossEncoder)
        final_chunks = hybrid_search_engine.execute_hybrid_search(
            query=search_query,
            document_id=document_id,
            top_k=top_k
        )

        if not final_chunks:
            # Fallback to vector search if hybrid search yields empty candidate pool
            raw_chunks = vector_service.search(query=search_query, top_k=top_k, document_id=document_id)
            final_chunks = raw_chunks

        if not final_chunks:
            return {
                "question": question,
                "explanation": "No relevant document chunks found in the loaded corpus for this query. Please ensure you have uploaded and processed a regulatory PDF.",
                "sources": [],
                "was_fallback": True
            }

        # 3. Fetch Graph Context for cross-references
        graph_context = cls.get_graph_context_for_question(search_query)

        # 4. Generate RAG Explanation via Engine
        explanation, was_fallback = engine.explain_rag(question, final_chunks, graph_context)

        return {
            "question": question,
            "normalized_query": search_query,
            "explanation": explanation,
            "sources": final_chunks,
            "was_fallback": was_fallback
        }

    @classmethod
    def get_graph_context_for_question(cls, question: str) -> dict:
        """
        Analyzes the question to find matching regulations/schemes in the graph,
        and retrieves details for those entities along with their dependencies.
        """
        from app.db.neo4j_conn import neo4j_db
        import re
        
        # 1. Identify search tokens (e.g. "33(9)", "33-9", "33(7)", "Regulation 30", etc.)
        matches = re.findall(r"\b\d+(?:[\(\-]\d+\)?)?", question)
        tokens = list(set(matches))
        
        # Common terms mapping
        term_map = {
            "rehab": "rehabilitation",
            "incentive": "incentive",
            "fsi": "fsi",
            "bua": "built-up area"
        }
        for kw, full in term_map.items():
            if kw in question.lower():
                tokens.append(full)
                
        if not tokens:
            return {"matched_nodes": [], "connections": []}
            
        neo4j_db.connect()
        matched_nodes = []
        connections = []
        visited_ids = set()
        
        if neo4j_db.use_fallback:
            # Search NetworkX fallback
            G = neo4j_db.nx_graph
            if G:
                # Find matching nodes
                for node, attrs in G.nodes(data=True):
                    matched = False
                    for tok in tokens:
                        title_val = attrs.get("title") or ""
                        cit_val = attrs.get("citation") or ""
                        if (tok.lower() in (node or "").lower() or 
                            tok.lower() in title_val.lower() or 
                            tok.lower() in cit_val.lower()):
                            matched = True
                            break
                    if matched and node not in visited_ids:
                        matched_nodes.append({
                            "id": node,
                            "label": attrs.get("label") or "RegulatoryEntity",
                            "title": attrs.get("title") or node,
                            "citation": attrs.get("citation") or "",
                            "properties": {k: v for k, v in attrs.items() if k not in ("label", "title", "citation")}
                        })
                        visited_ids.add(node)
                
                # Gather direct relationships for matched nodes
                for u, v, attrs in G.edges(data=True):
                    if u in visited_ids or v in visited_ids:
                        connections.append({
                            "source": u,
                            "target": v,
                            "type": attrs.get("type", "DEPENDS_ON")
                        })
        else:
            # Query Neo4j
            try:
                for tok in tokens:
                    query = """
                    MATCH (n)
                    WHERE toLower(n.id) CONTAINS toLower($tok) 
                       OR toLower(n.title) CONTAINS toLower($tok) 
                       OR toLower(n.citation) CONTAINS toLower($tok)
                    RETURN n LIMIT 10
                    """
                    records = neo4j_db.execute_query(query, {"tok": tok})
                    for record in records:
                        node = record["n"]
                        nid = node.get("id")
                        if nid and nid not in visited_ids:
                            labels = list(node.labels)
                            label = labels[0] if labels else "RegulatoryEntity"
                            
                            props = dict(node)
                            matched_nodes.append({
                                "id": nid,
                                "label": label,
                                "title": props.get("title", nid),
                                "citation": props.get("citation", ""),
                                "properties": {k: v for k, v in props.items() if k not in ("title", "citation")}
                            })
                            visited_ids.add(nid)
                
                if visited_ids:
                    query = """
                    MATCH (a)-[r]->(b)
                    WHERE a.id IN $ids OR b.id IN $ids
                    RETURN a.id as source, b.id as target, type(r) as type
                    LIMIT 50
                    """
                    records = neo4j_db.execute_query(query, {"ids": list(visited_ids)})
                    for record in records:
                        connections.append({
                            "source": record["source"],
                            "target": record["target"],
                            "type": record["type"]
                        })
            except Exception as e:
                print(f"[ReasoningService] Neo4j query error: {e}")
                
        return {"matched_nodes": matched_nodes, "connections": connections}

