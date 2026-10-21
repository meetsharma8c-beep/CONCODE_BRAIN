"""
CONCODE Neural Brain — Workspace Retriever
Sentence-transformers (MiniLM) + FAISS for context-aware code retrieval.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger("concode.retriever")


class WorkspaceRetriever:
    """
    Indexes workspace files using MiniLM embeddings and retrieves
    relevant code context via FAISS similarity search.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 512):
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.model = None
        self.index = None
        self.chunks: List[str] = []
        self.chunk_sources: List[str] = []  # filename for each chunk
        self._load_model()

    def _load_model(self):
        """Load the sentence-transformer embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            # Offline mode is configured before transformers is imported in
            # src.config. A missing local model leaves this optional subsystem
            # unavailable instead of downloading one.
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Retriever model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load retriever model: {e}")
            self.model = None

    def _chunk_text(self, text: str, filename: str) -> List[Dict[str, str]]:
        """Split file content into overlapping chunks."""
        chunks = []
        lines = text.split("\n")
        current_chunk = []
        current_length = 0

        for line in lines:
            current_chunk.append(line)
            current_length += len(line) + 1

            if current_length >= self.chunk_size:
                chunk_text = "\n".join(current_chunk)
                chunks.append({"text": chunk_text, "source": filename})
                # Overlap: keep last 3 lines
                overlap = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk[:]
                current_chunk = list(overlap)
                current_length = sum(len(l) + 1 for l in current_chunk)

        # Add remaining
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            if chunk_text.strip():
                chunks.append({"text": chunk_text, "source": filename})

        return chunks

    def index_workspace(self, workspace_files: Dict[str, str]):
        """
        Build a FAISS or NumPy index from workspace files.

        Args:
            workspace_files: {"filename": "file_content", ...}
        """
        if self.model is None:
            logger.warning("Retriever model not loaded, skipping indexing")
            return

        if not workspace_files:
            logger.info("No workspace files provided, skipping indexing")
            return

        try:
            # Chunk all files
            self.chunks = []
            self.chunk_sources = []
            for filename, content in workspace_files.items():
                if not content or not content.strip():
                    continue
                file_chunks = self._chunk_text(content, filename)
                for chunk in file_chunks:
                    self.chunks.append(chunk["text"])
                    self.chunk_sources.append(chunk["source"])

            if not self.chunks:
                logger.info("No chunks generated from workspace files")
                return

            # Encode chunks
            embeddings = self.model.encode(self.chunks, show_progress_bar=False)
            embeddings = np.array(embeddings, dtype=np.float32)

            # Normalize for cosine similarity (NumPy fallback path)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.embeddings = embeddings / norms

            # Try FAISS index building if available
            try:
                import faiss
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dim)
                # FAISS needs its own normalized copy (normalize_L2 mutates in-place)
                faiss_embeddings = np.copy(self.embeddings)
                self.index.add(faiss_embeddings)
            except Exception as fe:
                logger.info(f"FAISS index build bypassed ({fe}); using NumPy cosine similarity matrix.")
                self.index = "numpy"

            logger.info(
                f"Indexed {len(self.chunks)} chunks from "
                f"{len(workspace_files)} files"
            )
        except Exception as e:
            logger.error(f"Failed to index workspace: {e}")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve the most relevant code chunks for a query.

        Returns:
            List of {"text": "...", "source": "filename", "score": 0.85}
        """
        if self.model is None or not self.chunks or getattr(self, "embeddings", None) is None:
            return []

        try:
            query_embedding = self.model.encode([query], show_progress_bar=False)
            query_embedding = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(query_embedding)
            if q_norm > 0:
                query_embedding /= q_norm

            k = min(top_k, len(self.chunks))

            # FAISS branch
            if self.index is not None and self.index != "numpy":
                try:
                    scores, indices = self.index.search(query_embedding, k)
                    results = []
                    for i, idx in enumerate(indices[0]):
                        if idx < 0 or idx >= len(self.chunks):
                            continue
                        results.append({
                            "text": self.chunks[idx],
                            "source": self.chunk_sources[idx],
                            "score": round(float(scores[0][i]), 4),
                        })
                    return results
                except Exception:
                    pass

            # NumPy fallback branch
            sims = np.dot(self.embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(sims)[::-1][:k]

            results = []
            for idx in top_indices:
                results.append({
                    "text": self.chunks[idx],
                    "source": self.chunk_sources[idx],
                    "score": round(float(sims[idx]), 4),
                })
            return results
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    @property
    def is_ready(self) -> bool:
        """Whether the retriever is ready for queries."""
        return self.model is not None
