import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings

class VectorService:
    """
    Manages persistent document chunk storage, semantic vector searching,
    and collection maintenance via ChromaDB.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorService, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        chroma_dir = Path(settings.STORAGE_DIR) / "chroma_db"
        os.makedirs(chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBED_MODEL
        )
        
        self.collection = self.client.get_or_create_collection(
            name="dcpr_chunks",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, version_id: str, document_id: str, chunks: list[dict]):
        """
        Batches and upserts chunks into the collection.
        Chunk format expected:
        {
            "chunk_idx": int,
            "text": str,
            "page": int,
            "section": str,
            "char_count": int
        }
        """
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for c in chunks:
            chunk_id = f"{version_id}_{c['chunk_idx']}"
            ids.append(chunk_id)
            documents.append(c["text"])
            metadatas.append({
                "version_id": version_id,
                "document_id": document_id,
                "page": c.get("page", 1),
                "section": c.get("section", "General"),
                "chunk_idx": c["chunk_idx"]
            })

        # ChromaDB supports batching up to ~5400 items, let's batch in chunks of 500
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

    def search(self, query: str, top_k: int = None, document_id: str = None) -> list[dict]:
        """
        Performs vector similarity search. If document_id is provided, filters by document_id.
        Returns formatted list of chunks with similarity scores.
        """
        if top_k is None:
            top_k = settings.RAG_SEARCH_K

        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, dists):
                # Cosine distance in ChromaDB: score = 1 - distance
                similarity_score = round(1.0 - float(dist), 4)
                formatted.append({
                    "text": doc,
                    "page": meta.get("page", 1),
                    "section": meta.get("section", "General"),
                    "version_id": meta.get("version_id"),
                    "document_id": meta.get("document_id"),
                    "chunk_idx": meta.get("chunk_idx"),
                    "score": similarity_score
                })

        return formatted

    def delete_version_chunks(self, version_id: str):
        """Deletes all vector chunks associated with a specific document version."""
        try:
            self.collection.delete(where={"version_id": version_id})
        except Exception as e:
            print(f"[VectorService] Error deleting chunks for version {version_id}: {e}")

    def delete_document_chunks(self, document_id: str):
        """Deletes all vector chunks associated with a document_id."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"[VectorService] Error deleting chunks for document {document_id}: {e}")

    def stats(self) -> dict:
        """Returns storage stats."""
        try:
            count = self.collection.count()
            return {
                "status": "online",
                "total_chunks": count,
                "collection_name": self.collection.name,
                "embed_model": settings.EMBED_MODEL
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

vector_service = VectorService()
