"""
Vector Index Query Module

This module provides query functionality for ChromaDB vector index.
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


class VectorIndexQuery:
    """Query interface for ChromaDB vector index"""

    def __init__(self, chroma_path: str = "chroma_db"):
        """
        Initialize vector index query

        Args:
            chroma_path: Path to ChromaDB directory
        """
        self.chroma_path = Path(chroma_path)

        if not self.chroma_path.exists():
            raise ValueError(f"ChromaDB not found at {chroma_path}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        # Get collection
        self.collection = self.client.get_collection("transcripts_unified")

        # Configure Gemini for embeddings
        use_paid_tier = os.getenv("USE_PAID_TIER", "").lower() == "true"
        api_key = os.getenv("GEMINI_API_KEY_PAID") if use_paid_tier else os.getenv("GEMINI_API_KEY_FREE")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=api_key)

        print(f"✅ Vector index loaded: {self.collection.count()} documents")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for query text using Gemini"""
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']

    def search(
        self,
        query_text: str,
        n_results: int = 5,
        filter_meeting_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across transcriptions

        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_meeting_id: Optional meeting ID to filter by

        Returns:
            List of search results with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query_text)

        # Build filter
        where_filter = None
        if filter_meeting_id:
            where_filter = {"meeting_id": filter_meeting_id}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []

        if results and results['documents'] and len(results['documents']) > 0:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []

            for i, doc in enumerate(documents):
                result = {
                    'text': doc,
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'distance': distances[i] if i < len(distances) else 0.0
                }
                formatted_results.append(result)

        return formatted_results

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()

        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }
