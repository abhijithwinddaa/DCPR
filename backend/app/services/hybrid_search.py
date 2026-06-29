import re
import os
import pickle
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from app.services.vector_service import vector_service
from app.core.config import settings

class ProductionCertifiedHybridEngine:
    """
    Production-certified hybrid engine with consistent memory cache packaging and MD5 multi-worker stability.
    """
    
    REGULATION_CODE_REGEX = re.compile(r'\b\d+(?:\(\d+\)|[\-\(][a-z\d]+\)?)*\b', re.IGNORECASE)

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.storage_dir = Path(settings.STORAGE_DIR) / "bm25_indices"
        os.makedirs(self.storage_dir, exist_ok=True)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.reranker = None

    def _get_reranker(self):
        if self.reranker is None:
            print(f"[HybridEngine] Initializing CrossEncoder reranker model ({settings.RERANK_MODEL})...")
            self.reranker = CrossEncoder(settings.RERANK_MODEL)
        return self.reranker

    @classmethod
    def _tokenize_statutory(cls, text: str) -> List[str]:
        codes = cls.REGULATION_CODE_REGEX.findall(text)
        clean_text = cls.REGULATION_CODE_REGEX.sub(" ", text).lower()
        words = [w for w in clean_text.split() if len(w) > 2]
        return [c.lower() for c in codes] + words

    def build_and_persist_index(self, document_id: str, corpus_chunks: List[Dict[str, Any]]):
        """Called ONCE during background document ingestion."""
        tokenized_corpus = [self._tokenize_statutory(c["text"]) for c in corpus_chunks]
        bm25_instance = BM25Okapi(tokenized_corpus)
        
        # Consistent cache packaging fix
        cache_data = {"bm25": bm25_instance, "chunks": corpus_chunks}
        self._memory_cache[document_id] = cache_data
        
        index_path = self.storage_dir / f"bm25_{document_id}.pkl"
        with open(index_path, "wb") as f:
            pickle.dump(cache_data, f)

    def _get_bm25_index(self, document_id: str) -> Optional[tuple[BM25Okapi, List[Dict[str, Any]]]]:
        # Consistent retrieval from memory cache
        if document_id in self._memory_cache:
            data = self._memory_cache[document_id]
            return data["bm25"], data["chunks"]

        index_path = self.storage_dir / f"bm25_{document_id}.pkl"
        if index_path.exists():
            with open(index_path, "rb") as f:
                data = pickle.load(f)
                self._memory_cache[document_id] = data
                return data["bm25"], data["chunks"]
        return None

    def execute_hybrid_search(
        self, 
        query: str, 
        document_id: Optional[str] = None, 
        top_k: int = 5,
        fallback_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        # 1. Dense Vector Search (ChromaDB)
        dense_results = vector_service.search(query=query, top_k=top_k * 4, document_id=document_id)
        if not dense_results and fallback_chunks:
            dense_results = fallback_chunks[:top_k * 4]

        # 2. Code-Aware Sparse BM25 Search
        sparse_results = []
        if document_id:
            bm25_data = self._get_bm25_index(document_id)
            if bm25_data:
                bm25, chunks = bm25_data
                tokenized_query = self._tokenize_statutory(query)
                scores = bm25.get_scores(tokenized_query)
                ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k * 4]
                sparse_results = [chunks[i] for i in ranked if scores[i] > 0]

        # If sparse search has no results, merge dense results
        if not sparse_results:
            sparse_results = dense_results

        # 3. Reciprocal Rank Fusion (RRF) with hashlib multi-worker stability
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        def add_rrf(results, weight=1.0):
            for rank, doc in enumerate(results, start=1):
                text_content = doc.get('text', '')
                text_sig = hashlib.md5(text_content[:80].encode('utf-8')).hexdigest()
                did = f"{doc.get('document_id', 'doc')}_{doc.get('page', 1)}_{text_sig}"
                doc_map[did] = doc
                rrf_scores[did] = rrf_scores.get(did, 0.0) + weight * (1.0 / (self.rrf_k + rank))

        has_statutory_code = bool(self.REGULATION_CODE_REGEX.search(query))
        add_rrf(dense_results, weight=1.0)
        add_rrf(sparse_results, weight=2.0 if has_statutory_code else 1.0)

        sorted_candidates = [doc_map[did] for did in sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k * 2]]

        if not sorted_candidates:
            return []

        # 4. Post-Fusion Cross-Encoder Re-Ranking
        try:
            reranker = self._get_reranker()
            pairs = [[query, c["text"]] for c in sorted_candidates]
            cross_scores = reranker.predict(pairs)

            final_ranked = []
            for doc, score in sorted(zip(sorted_candidates, cross_scores), key=lambda x: x[1], reverse=True)[:top_k]:
                doc_copy = dict(doc)
                doc_copy["score"] = round(float(score), 4)
                final_ranked.append(doc_copy)
            return final_ranked
        except Exception as e:
            print(f"[HybridEngine] Reranker exception fallback: {e}")
            return sorted_candidates[:top_k]

hybrid_search_engine = ProductionCertifiedHybridEngine()
