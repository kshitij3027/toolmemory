"""
Voyage AI Embedding Wrapper for Tool Memory Project

This module provides a wrapper for the Voyage AI embedding API.
"""

import os
import time
from typing import List, Union, Optional
from dotenv import load_dotenv
import voyageai


class VoyageEmbedder:
    """
    A wrapper class for Voyage AI embedding API.
    
    Provides methods to generate embeddings for single texts or batches of texts
    with error handling and retry logic.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "voyage-code-2"):
        """
        Initialize the VoyageEmbedder.
        
        Args:
            api_key (Optional[str]): Voyage AI API key. If None, will get from environment.
            model (str): Model name to use for embeddings. Defaults to "voyage-code-2".
            
        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY not found in environment variables and not provided")
        
        # Initialize client and model
        self.client = voyageai.Client(api_key=self.api_key)
        self.model = model
        
        print(f"VoyageEmbedder initialized with model: {self.model}")
    
    def get_embedding(self, text: str, input_type: str = "document") -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text (str): Text to embed.
            input_type (str): Type of input - "document" or "query".
            
        Returns:
            List[float]: The embedding vector.
            
        Raises:
            Exception: If API call fails after retries.
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                result = self.client.embed(
                    texts=[text], 
                    model=self.model, 
                    input_type=input_type
                )
                return result.embeddings[0]
                
            except voyageai.RateLimitError as e:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Rate limit error after {max_retries} attempts: {str(e)}")
                    raise
                    
            except voyageai.APIError as e:
                print(f"Voyage AI API error: {str(e)}")
                raise
                
            except Exception as e:
                print(f"Unexpected error getting embedding: {str(e)}")
                raise
    
    def get_embeddings(self, texts: List[str], input_type: str = "document") -> List[List[float]]:
        """
        Get embeddings for multiple texts in a batch.
        
        Args:
            texts (List[str]): List of texts to embed.
            input_type (str): Type of input - "document" or "query".
            
        Returns:
            List[List[float]]: List of embedding vectors.
            
        Raises:
            Exception: If API call fails after retries.
        """
        if not texts:
            return []
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                result = self.client.embed(
                    texts=texts, 
                    model=self.model, 
                    input_type=input_type
                )
                return result.embeddings
                
            except voyageai.RateLimitError as e:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Rate limit error after {max_retries} attempts: {str(e)}")
                    raise
                    
            except voyageai.APIError as e:
                print(f"Voyage AI API error: {str(e)}")
                raise
                
            except Exception as e:
                print(f"Unexpected error getting embeddings: {str(e)}")
                raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model.
        
        Returns:
            int: Embedding dimension (1024 for voyage-code-2).
        """
        # Model dimension mapping
        model_dimensions = {
            "voyage-code-2": 1024,
            "voyage-2": 1024,
            "voyage-large-2": 1536,
            "voyage-law-2": 1024,
            "voyage-multilingual-2": 1024
        }
        
        return model_dimensions.get(self.model, 1024)  # Default to 1024


if __name__ == "__main__":
    """
    Example usage and testing of the VoyageEmbedder.
    """
    try:
        # Initialize embedder
        embedder = VoyageEmbedder()
        
        # Test single embedding
        sample_text = "This is a sample text for testing the Voyage AI embedding API."
        print(f"Getting embedding for: {sample_text}")
        
        embedding = embedder.get_embedding(sample_text, input_type="document")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        
        # Test batch embeddings
        sample_texts = [
            "First sample text for batch testing.",
            "Second sample text for batch testing.",
            "Third sample text for batch testing."
        ]
        print(f"\nGetting embeddings for {len(sample_texts)} texts...")
        
        embeddings = embedder.get_embeddings(sample_texts, input_type="document")
        print(f"Number of embeddings: {len(embeddings)}")
        print(f"Each embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        
        # Test query embedding
        query_text = "What is the purpose of embeddings?"
        query_embedding = embedder.get_embedding(query_text, input_type="query")
        print(f"\nQuery embedding dimension: {len(query_embedding)}")
        
        print("\nVoyage AI embedding test completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
