"""
MongoDB Memory Storage for Tool Memory Project

This module provides functions to store and retrieve memories from MongoDB
with vector search capabilities using Voyage AI embeddings.
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from voyage import VoyageEmbedder


class MongoDBMemory:
    """
    A class for managing memory storage and retrieval in MongoDB.
    
    Provides methods to add memories, search for relevant memories using vector search,
    and format results for LLM consumption.
    """
    
    def __init__(
        self, 
        connection_string: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        voyage_embedder: Optional[VoyageEmbedder] = None
    ):
        """
        Initialize the MongoDBMemory.
        
        Args:
            connection_string (Optional[str]): MongoDB connection string. If None, gets from env.
            db_name (Optional[str]): Database name. Defaults to "toolmemory".
            collection_name (Optional[str]): Collection name. Defaults to "memories".
            voyage_embedder (Optional[VoyageEmbedder]): Embedder instance. If None, creates new one.
            
        Raises:
            ValueError: If connection string is not provided and not found in environment.
            Exception: If MongoDB connection fails.
        """
        # Load environment variables
        load_dotenv()
        
        # Get connection parameters
        self.connection_string = connection_string or os.getenv("MONGO_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("MONGO_CONNECTION_STRING not found in environment variables and not provided")
        
        self.db_name = db_name or "toolmemory"
        self.collection_name = collection_name or "memories"
        
        # Initialize MongoDB client
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            print(f"Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            raise
        
        # Initialize embedder
        self.embedder = voyage_embedder if voyage_embedder else VoyageEmbedder()
        
        print("MongoDBMemory initialized successfully")
    
    def _ensure_vector_index(
        self, 
        vector_field_name: str = "embedding", 
        index_name: str = "vector_index_cosine"
    ) -> None:
        """
        Ensure a vector search index exists on the embedding field.
        
        Note: For MongoDB Atlas, vector search indexes are typically created 
        via the Atlas UI or Atlas Admin API. This method provides the index 
        definition for reference.
        
        Args:
            vector_field_name (str): Field name containing embeddings.
            index_name (str): Name for the vector search index.
        """
        # Get the actual embedding dimension by creating a sample embedding
        sample_embedding = self.embedder.get_embedding("sample text", input_type="document")
        embedding_dim = len(sample_embedding)
        
        index_definition = {
            "name": index_name,
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": vector_field_name,
                        "numDimensions": embedding_dim,  # Actual dimension from sample
                        "similarity": "cosine"
                    }
                ]
            }
        }
        
        print(f"Vector index definition for Atlas (create via Atlas UI):")
        print(json.dumps(index_definition, indent=2))
        print(f"Required dimensions: {embedding_dim}")
        
        # Note: Atlas vector search indexes must be created via Atlas UI or Admin API
        # This method just provides the definition for reference
    
    def add_memory(
        self, 
        text_content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a memory to the collection with embedding.
        
        Args:
            text_content (str): The text content to store.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
            
        Returns:
            str: The inserted document ID.
            
        Raises:
            Exception: If embedding generation or database insertion fails.
        """
        try:
            # Generate embedding for the text content
            print(f"Generating embedding for memory: {text_content[:50]}...")
            embedding = self.embedder.get_embedding(text_content, input_type="document")
            
            # Prepare document
            doc = {
                "text": text_content,
                "embedding": embedding,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc),
                "embedding_model": self.embedder.model,
                "embedding_dimension": len(embedding)
            }
            
            # Insert document
            result = self.collection.insert_one(doc)
            print(f"Memory added successfully with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error adding memory: {str(e)}")
            raise
    
    def search_memories(
        self, 
        query_text: str, 
        top_k: int = 5,
        vector_field_name: str = "embedding",
        index_name: str = "vector_index_cosine"
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories using vector search.
        
        Args:
            query_text (str): Query text to search for.
            top_k (int): Number of results to return.
            vector_field_name (str): Field name containing embeddings.
            index_name (str): Name of the vector search index.
            
        Returns:
            List[Dict[str, Any]]: List of relevant memory documents with scores.
            
        Raises:
            Exception: If embedding generation or database query fails.
        """
        try:
            # Generate query embedding
            print(f"Searching memories for: {query_text[:50]}...")
            query_embedding = self.embedder.get_embedding(query_text, input_type="query")
            
            # Construct MongoDB Atlas Vector Search aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": index_name,
                        "path": vector_field_name,
                        "queryVector": query_embedding,
                        "numCandidates": top_k * 10,  # Number of candidates to consider
                        "limit": top_k  # Number of results to return
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "text": 1,
                        "metadata": 1,
                        "created_at": 1,
                        "embedding_model": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            # Execute aggregation
            results = list(self.collection.aggregate(pipeline))
            print(f"Found {len(results)} relevant memories")
            
            return results
            
        except Exception as e:
            print(f"Error searching memories: {str(e)}")
            # Fallback to text-based search if vector search fails
            print("Falling back to text-based search...")
            return self._fallback_text_search(query_text, top_k)
    
    def _fallback_text_search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback text-based search when vector search is not available.
        
        Args:
            query_text (str): Query text to search for.
            top_k (int): Number of results to return.
            
        Returns:
            List[Dict[str, Any]]: List of relevant memory documents.
        """
        try:
            # Simple text search using MongoDB text search
            # First, ensure text index exists
            try:
                self.collection.create_index([("text", "text")])
            except:
                pass  # Index might already exist
            
            # Perform text search
            results = list(
                self.collection
                .find({"$text": {"$search": query_text}})
                .limit(top_k)
                .sort([("score", {"$meta": "textScore"})])
            )
            
            # Format results to match vector search format
            formatted_results = []
            for result in results:
                formatted_result = {
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "created_at": result.get("created_at"),
                    "embedding_model": result.get("embedding_model"),
                    "score": result.get("score", 0.5)  # Default score for text search
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            print(f"Fallback text search also failed: {str(e)}")
            return []
    
    def format_memories_for_prompt(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a string suitable for LLM prompt.
        
        Args:
            search_results (List[Dict[str, Any]]): Results from search_memories.
            
        Returns:
            str: Formatted string for LLM consumption.
        """
        if not search_results:
            return "No relevant memories found."
        
        formatted_memories = ["Relevant memories:"]
        
        for i, memory in enumerate(search_results, 1):
            text = memory.get("text", "")
            score = memory.get("score", 0)
            metadata = memory.get("metadata", {})
            source = metadata.get("source", "unknown")
            
            memory_entry = f"{i}. [Score: {score:.3f}] [Source: {source}] {text}"
            formatted_memories.append(memory_entry)
        
        return "\n".join(formatted_memories)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory collection.
        
        Returns:
            Dict[str, Any]: Statistics including count, latest entry, etc.
        """
        try:
            total_count = self.collection.count_documents({})
            
            # Get latest memory
            latest_memory = self.collection.find_one(
                {}, 
                sort=[("created_at", -1)]
            )
            
            # Get memory sources breakdown
            pipeline = [
                {"$group": {
                    "_id": "$metadata.source",
                    "count": {"$sum": 1}
                }}
            ]
            sources = list(self.collection.aggregate(pipeline))
            
            stats = {
                "total_memories": total_count,
                "latest_memory_date": latest_memory.get("created_at") if latest_memory else None,
                "sources_breakdown": {source["_id"] or "unknown": source["count"] for source in sources}
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting memory stats: {str(e)}")
            return {"error": str(e)}
    
    def close(self):
        """Close the MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()
            print("MongoDB connection closed")


if __name__ == "__main__":
    """
    Example usage and testing of MongoDBMemory.
    """
    try:
        # Initialize MongoDB memory
        mongo_memory = MongoDBMemory()
        
        # Display vector index information
        mongo_memory._ensure_vector_index()
        
        # Add some sample memories
        sample_memories = [
            {
                "text": "Python is a high-level programming language known for its simplicity and readability.",
                "metadata": {"source": "programming_knowledge", "type": "definition"}
            },
            {
                "text": "Machine learning algorithms require large datasets for training to achieve good performance.",
                "metadata": {"source": "ml_knowledge", "type": "principle"}
            },
            {
                "text": "Vector databases are optimized for similarity search and are commonly used in AI applications.",
                "metadata": {"source": "database_knowledge", "type": "explanation"}
            }
        ]
        
        print("\nAdding sample memories...")
        memory_ids = []
        for memory in sample_memories:
            memory_id = mongo_memory.add_memory(memory["text"], memory["metadata"])
            memory_ids.append(memory_id)
        
        # Test search functionality
        print("\nTesting memory search...")
        query = "What is machine learning?"
        search_results = mongo_memory.search_memories(query, top_k=3)
        
        # Format and display results
        formatted_memories = mongo_memory.format_memories_for_prompt(search_results)
        print(f"\nSearch results for '{query}':")
        print(formatted_memories)
        
        # Get memory statistics
        print("\nMemory statistics:")
        stats = mongo_memory.get_memory_stats()
        print(json.dumps(stats, indent=2, default=str))
        
        print("\nMongoDBMemory testing completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    
    finally:
        # Close connection
        if 'mongo_memory' in locals():
            mongo_memory.close()
