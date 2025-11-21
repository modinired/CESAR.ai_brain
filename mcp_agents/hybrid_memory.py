"""
Hybrid Vector Memory - FAISS + PostgreSQL
==========================================

Combines FAISS for fast in-memory similarity search with PostgreSQL
for persistent storage and multi-tenant queries.

Features:
- Fast similarity search with FAISS
- Persistent storage in PostgreSQL + pgvector
- Multi-tenant isolation
- Automatic sync between FAISS and PostgreSQL
- Batch operations for efficiency
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import psycopg2
    from psycopg2.extras import Json
except ImportError as e:
    logging.warning(f"Hybrid memory dependencies missing: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HybridMemory")

# Configuration
DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_DIM = 384
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
FAISS_META_PATH = os.getenv("FAISS_META_PATH", "./data/faiss_meta.pkl")


# =============================================================================
# HYBRID VECTOR MEMORY
# =============================================================================

class HybridVectorMemory:
    """
    Hybrid vector memory with FAISS and PostgreSQL backends
    """

    def __init__(
        self,
        db_dsn: str = None,
        model_name: str = DEFAULT_MODEL,
        dim: int = DEFAULT_DIM,
        use_faiss: bool = True,
        use_postgres: bool = True
    ):
        self.db_dsn = db_dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        )
        self.model_name = model_name
        self.dim = dim
        self.use_faiss = use_faiss
        self.use_postgres = use_postgres

        # Initialize embedding model
        self.model = SentenceTransformer(model_name)

        # Initialize FAISS
        if self.use_faiss:
            self._init_faiss()

        logger.info(f"HybridVectorMemory initialized (FAISS: {use_faiss}, PostgreSQL: {use_postgres})")

    def _init_faiss(self):
        """Initialize FAISS index"""
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_META_PATH):
            # Load existing index
            self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_META_PATH, "rb") as f:
                self.faiss_meta = pickle.load(f)
            logger.info(f"Loaded FAISS index: {self.faiss_index.ntotal} vectors")
        else:
            # Create new index (inner product with normalized vectors = cosine similarity)
            self.faiss_index = faiss.IndexFlatIP(self.dim)
            self.faiss_meta = []
            logger.info("Created new FAISS index")

    def _save_faiss(self):
        """Save FAISS index to disk"""
        if self.use_faiss:
            faiss.write_index(self.faiss_index, FAISS_INDEX_PATH)
            with open(FAISS_META_PATH, "wb") as f:
                pickle.dump(self.faiss_meta, f)

    # =========================================================================
    # ADD OPERATIONS
    # =========================================================================

    def add(
        self,
        content: str,
        metadata: Dict[str, Any],
        mcp_system: Optional[str] = None,
        context_type: Optional[str] = None
    ) -> str:
        """
        Add content to both FAISS and PostgreSQL

        Args:
            content: Text content to index
            metadata: Associated metadata
            mcp_system: MCP system identifier
            context_type: Context type (e.g., 'error_resolution', 'skill')

        Returns:
            Unique identifier for the added content
        """
        # Generate embedding
        embedding = self.model.encode(content).astype('float32')

        # Normalize for cosine similarity
        faiss.normalize_L2(np.array([embedding]))

        # Generate ID
        import uuid
        content_id = str(uuid.uuid4())

        # Add to FAISS
        if self.use_faiss:
            self.faiss_index.add(np.array([embedding]))
            self.faiss_meta.append({
                "id": content_id,
                "content": content,
                "metadata": metadata,
                "mcp_system": mcp_system,
                "context_type": context_type
            })
            self._save_faiss()

        # Add to PostgreSQL
        if self.use_postgres:
            self._add_to_postgres(
                content_id,
                content,
                embedding.tolist(),
                metadata,
                mcp_system,
                context_type
            )

        logger.info(f"Added content: {content_id} ({mcp_system}/{context_type})")
        return content_id

    def add_batch(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        mcp_system: Optional[str] = None,
        context_type: Optional[str] = None
    ) -> List[str]:
        """
        Add multiple contents in batch (more efficient)

        Args:
            contents: List of text contents
            metadatas: List of metadata dicts
            mcp_system: MCP system identifier
            context_type: Context type

        Returns:
            List of content IDs
        """
        if len(contents) != len(metadatas):
            raise ValueError("Contents and metadatas must have same length")

        # Generate embeddings in batch
        embeddings = self.model.encode(contents).astype('float32')

        # Normalize
        faiss.normalize_L2(embeddings)

        # Generate IDs
        import uuid
        content_ids = [str(uuid.uuid4()) for _ in contents]

        # Add to FAISS
        if self.use_faiss:
            self.faiss_index.add(embeddings)

            for i, content_id in enumerate(content_ids):
                self.faiss_meta.append({
                    "id": content_id,
                    "content": contents[i],
                    "metadata": metadatas[i],
                    "mcp_system": mcp_system,
                    "context_type": context_type
                })

            self._save_faiss()

        # Add to PostgreSQL in batch
        if self.use_postgres:
            self._add_batch_to_postgres(
                content_ids,
                contents,
                embeddings.tolist(),
                metadatas,
                mcp_system,
                context_type
            )

        logger.info(f"Added {len(contents)} contents in batch")
        return content_ids

    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        mcp_system: Optional[str] = None,
        context_type: Optional[str] = None,
        use_postgres_filter: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query for similar content

        Args:
            query_text: Query text
            top_k: Number of results to return
            mcp_system: Filter by MCP system
            context_type: Filter by context type
            use_postgres_filter: Use PostgreSQL for filtering (slower but more accurate)

        Returns:
            List of similar contents with scores
        """
        # Generate query embedding
        query_embedding = self.model.encode(query_text).astype('float32')
        faiss.normalize_L2(np.array([query_embedding]))

        results = []

        # Query FAISS first (fast)
        if self.use_faiss and not use_postgres_filter:
            results = self._query_faiss(query_embedding, top_k, mcp_system, context_type)

        # Query PostgreSQL (for filtering or as fallback)
        if (self.use_postgres and use_postgres_filter) or not self.use_faiss:
            pg_results = self._query_postgres(
                query_embedding.tolist(),
                top_k,
                mcp_system,
                context_type
            )

            # Merge results
            if results:
                # Combine and deduplicate
                seen_ids = {r['id'] for r in results}
                for pg_res in pg_results:
                    if pg_res['id'] not in seen_ids:
                        results.append(pg_res)
                        seen_ids.add(pg_res['id'])
            else:
                results = pg_results

        # Sort by similarity score
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)

        return results[:top_k]

    def _query_faiss(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        mcp_system: Optional[str],
        context_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query FAISS index"""
        if self.faiss_index.ntotal == 0:
            return []

        # Search FAISS (over-fetch for filtering)
        fetch_k = min(top_k * 3, self.faiss_index.ntotal)
        distances, indices = self.faiss_index.search(
            np.array([query_embedding]),
            fetch_k
        )

        results = []

        for score, idx in zip(distances[0], indices[0]):
            if idx >= len(self.faiss_meta):
                continue

            meta = self.faiss_meta[idx]

            # Apply filters
            if mcp_system and meta.get('mcp_system') != mcp_system:
                continue

            if context_type and meta.get('context_type') != context_type:
                continue

            results.append({
                'id': meta.get('id'),
                'content': meta.get('content'),
                'metadata': meta.get('metadata'),
                'mcp_system': meta.get('mcp_system'),
                'context_type': meta.get('context_type'),
                'similarity': float(score),
                'source': 'faiss'
            })

            if len(results) >= top_k:
                break

        return results

    def _query_postgres(
        self,
        query_embedding: List[float],
        top_k: int,
        mcp_system: Optional[str],
        context_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query PostgreSQL with pgvector"""
        conn = psycopg2.connect(self.db_dsn)
        cursor = conn.cursor()

        # Build query with filters
        where_clauses = []
        params = [query_embedding, query_embedding, top_k]

        if mcp_system:
            where_clauses.append("mcp_system = %s")
            params.insert(3, mcp_system)

        if context_type:
            where_clauses.append("context_type = %s")
            params.insert(3, context_type)

        where_clause = " AND " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT
                id, content, metadata, mcp_system, context_type,
                1 - (embedding <=> %s::vector) as similarity
            FROM vector_memory
            WHERE embedding IS NOT NULL {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = [
            {
                'id': str(row[0]),
                'content': row[1],
                'metadata': row[2],
                'mcp_system': row[3],
                'context_type': row[4],
                'similarity': float(row[5]),
                'source': 'postgres'
            }
            for row in rows
        ]

        return results

    # =========================================================================
    # POSTGRESQL OPERATIONS
    # =========================================================================

    def _add_to_postgres(
        self,
        content_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        mcp_system: Optional[str],
        context_type: Optional[str]
    ):
        """Add single content to PostgreSQL"""
        conn = psycopg2.connect(self.db_dsn)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO vector_memory (
                    id, content, embedding, metadata, mcp_system, context_type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    mcp_system = EXCLUDED.mcp_system,
                    context_type = EXCLUDED.context_type,
                    updated_at = NOW()
            """, (
                content_id,
                content,
                embedding,
                Json(metadata),
                mcp_system,
                context_type
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add to PostgreSQL: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def _add_batch_to_postgres(
        self,
        content_ids: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        mcp_system: Optional[str],
        context_type: Optional[str]
    ):
        """Add batch to PostgreSQL"""
        conn = psycopg2.connect(self.db_dsn)
        cursor = conn.cursor()

        try:
            # Use execute_values for batch insert
            from psycopg2.extras import execute_values

            values = [
                (
                    content_ids[i],
                    contents[i],
                    embeddings[i],
                    Json(metadatas[i]),
                    mcp_system,
                    context_type
                )
                for i in range(len(content_ids))
            ]

            execute_values(
                cursor,
                """
                INSERT INTO vector_memory (
                    id, content, embedding, metadata, mcp_system, context_type
                )
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    mcp_system = EXCLUDED.mcp_system,
                    context_type = EXCLUDED.context_type,
                    updated_at = NOW()
                """,
                values
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed batch insert to PostgreSQL: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # =========================================================================
    # SYNC & MAINTENANCE
    # =========================================================================

    def sync_from_postgres_to_faiss(self, limit: int = 10000):
        """
        Sync PostgreSQL data to FAISS index

        Useful for rebuilding FAISS index from persistent storage
        """
        if not (self.use_faiss and self.use_postgres):
            return

        conn = psycopg2.connect(self.db_dsn)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, content, embedding, metadata, mcp_system, context_type
            FROM vector_memory
            WHERE embedding IS NOT NULL
            LIMIT %s
        """, (limit,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            logger.info("No data to sync from PostgreSQL")
            return

        # Rebuild FAISS index
        self.faiss_index = faiss.IndexFlatIP(self.dim)
        self.faiss_meta = []

        embeddings = []

        for row in rows:
            content_id, content, embedding, metadata, mcp_system, context_type = row

            embeddings.append(embedding)
            self.faiss_meta.append({
                "id": str(content_id),
                "content": content,
                "metadata": metadata,
                "mcp_system": mcp_system,
                "context_type": context_type
            })

        # Add to FAISS
        embeddings_array = np.array(embeddings, dtype='float32')
        faiss.normalize_L2(embeddings_array)
        self.faiss_index.add(embeddings_array)

        self._save_faiss()

        logger.info(f"Synced {len(rows)} vectors from PostgreSQL to FAISS")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = {
            "faiss_enabled": self.use_faiss,
            "postgres_enabled": self.use_postgres,
            "model": self.model_name,
            "dimension": self.dim
        }

        if self.use_faiss:
            stats["faiss_vectors"] = self.faiss_index.ntotal

        if self.use_postgres:
            conn = psycopg2.connect(self.db_dsn)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM vector_memory WHERE embedding IS NOT NULL")
            stats["postgres_vectors"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT mcp_system) FROM vector_memory")
            stats["mcp_systems"] = cursor.fetchone()[0]

            cursor.close()
            conn.close()

        return stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_hybrid_memory(
    db_dsn: str = None,
    model_name: str = DEFAULT_MODEL
) -> HybridVectorMemory:
    """
    Factory function to create hybrid memory

    Args:
        db_dsn: Database connection string
        model_name: Sentence transformer model name

    Returns:
        HybridVectorMemory instance
    """
    return HybridVectorMemory(db_dsn=db_dsn, model_name=model_name)
