"""
Research Tools for Tool Memory Project

This module provides Tavily search functionality with performance tracking
for enhancing agent research capabilities.
"""

import os
import time
import json
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv


class TavilySearchTool:
    """
    A tool for performing web searches using the Tavily API.
    
    Provides methods to search the web, track performance, and format results
    for agent consumption.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TavilySearchTool.
        
        Args:
            api_key (Optional[str]): Tavily API key. If None, gets from environment.
            
        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables and not provided")
        
        # API endpoints
        self.search_url = "https://api.tavily.com/search"
        self.extract_url = "https://api.tavily.com/extract"
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Query patterns for optimization tracking (advanced feature)
        self.query_patterns = {}
        
        print("TavilySearchTool initialized successfully")
    
    def search(
        self,
        query: str,
        topic: str = "general",
        search_depth: str = "basic",
        chunks_per_source: int = 3,
        max_results: int = 5,
        time_range: Optional[str] = None,
        days: int = 7,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_image_descriptions: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search using Tavily API.
        
        Args:
            query (str): The search query string.
            topic (str): Search topic ("general", "news", etc.).
            search_depth (str): "basic" or "advanced".
            chunks_per_source (int): Number of content chunks per source.
            max_results (int): Maximum number of results to return.
            time_range (Optional[str]): Time range for search (None for all time).
            days (int): Number of days to search back.
            include_answer (bool): Whether to include a direct answer.
            include_raw_content (bool): Whether to include raw HTML content.
            include_images (bool): Whether to include images.
            include_image_descriptions (bool): Whether to include image descriptions.
            include_domains (Optional[List[str]]): Domains to include.
            exclude_domains (Optional[List[str]]): Domains to exclude.
            
        Returns:
            Dict[str, Any]: Search results from Tavily API.
            
        Raises:
            Exception: If API request fails.
        """
        # Performance tracking start
        start_time = time.time()
        
        try:
            # Prepare payload
            payload = {
                "query": query,
                "topic": topic,
                "search_depth": search_depth,
                "chunks_per_source": chunks_per_source,
                "max_results": max_results,
                "time_range": time_range,
                "days": days,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
                "include_images": include_images,
                "include_image_descriptions": include_image_descriptions,
                "include_domains": include_domains or [],
                "exclude_domains": exclude_domains or []
            }
            
            print(f"Performing Tavily search for: {query[:50]}...")
            
            # Make API request
            response = requests.post(
                self.search_url,
                json=payload,
                headers=self.headers,
                timeout=30  # 30 second timeout
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            search_results = response.json()
            
            # Performance tracking end
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Tavily search for '{query}' completed in {duration:.2f} seconds")
            
            # Store query patterns for optimization tracking
            self.query_patterns[query] = {
                "duration": duration,
                "results_count": len(search_results.get("results", [])),
                "timestamp": time.time()
            }
            
            return search_results
            
        except requests.exceptions.RequestException as e:
            print(f"Error during Tavily search: {str(e)}")
            raise Exception(f"Tavily API request failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error during search: {str(e)}")
            raise
    
    def extract_content(
        self,
        urls: str,
        include_images: bool = False,
        extract_depth: str = "basic"
    ) -> Dict[str, Any]:
        """
        Extract content from specific URLs using Tavily API.
        
        Args:
            urls (str): URL or comma-separated URLs to extract content from.
            include_images (bool): Whether to include images in extraction.
            extract_depth (str): "basic" or "advanced" extraction depth.
            
        Returns:
            Dict[str, Any]: Extracted content from Tavily API.
            
        Raises:
            Exception: If API request fails.
        """
        try:
            # Prepare payload
            payload = {
                "urls": urls,
                "include_images": include_images,
                "extract_depth": extract_depth
            }
            
            print(f"Extracting content from: {urls[:100]}...")
            
            # Make API request
            response = requests.post(
                self.extract_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            extraction_results = response.json()
            
            print("Content extraction completed successfully")
            
            return extraction_results
            
        except requests.exceptions.RequestException as e:
            print(f"Error during content extraction: {str(e)}")
            raise Exception(f"Tavily extraction API request failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error during extraction: {str(e)}")
            raise
    
    def format_results_for_agent(self, tavily_response: Dict[str, Any]) -> str:
        """
        Format Tavily search results for agent consumption.
        
        Args:
            tavily_response (Dict[str, Any]): Raw response from Tavily API.
            
        Returns:
            str: Formatted string suitable for LLM context.
        """
        if not tavily_response:
            return "No search results available."
        
        formatted_result = ["Search Results:"]
        
        # Include direct answer if available
        if tavily_response.get("answer"):
            formatted_result.append(f"\nDirect Answer: {tavily_response['answer']}")
            formatted_result.append("")  # Empty line for spacing
        
        # Format search results
        results = tavily_response.get("results", [])
        if results:
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content available")
                
                # Truncate content if too long
                if len(content) > 300:
                    content = content[:300] + "..."
                
                result_entry = f"{i}. **{title}**\n   URL: {url}\n   Content: {content}\n"
                formatted_result.append(result_entry)
        else:
            formatted_result.append("No specific results found.")
        
        return "\n".join(formatted_result)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for search queries.
        
        Returns:
            Dict[str, Any]: Performance statistics.
        """
        if not self.query_patterns:
            return {"message": "No search queries performed yet"}
        
        durations = [pattern["duration"] for pattern in self.query_patterns.values()]
        result_counts = [pattern["results_count"] for pattern in self.query_patterns.values()]
        
        stats = {
            "total_queries": len(self.query_patterns),
            "average_duration": sum(durations) / len(durations),
            "fastest_query": min(durations),
            "slowest_query": max(durations),
            "average_results_per_query": sum(result_counts) / len(result_counts) if result_counts else 0,
            "recent_queries": list(self.query_patterns.keys())[-5:]  # Last 5 queries
        }
        
        return stats
    
    def mock_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Mock search for testing without API calls.
        
        Args:
            query (str): Search query (for context).
            **kwargs: Additional parameters (ignored in mock).
            
        Returns:
            Dict[str, Any]: Mock search results.
        """
        mock_response = {
            "query": query,
            "answer": f"This is a mock answer for the query: {query}",
            "results": [
                {
                    "title": f"Mock Result 1 for {query}",
                    "url": "https://example.com/result1",
                    "content": f"This is mock content related to {query}. It demonstrates how the search tool would format real results.",
                    "score": 0.95
                },
                {
                    "title": f"Mock Result 2 for {query}",
                    "url": "https://example.com/result2", 
                    "content": f"Additional mock content for {query}. This shows multiple results formatting.",
                    "score": 0.87
                }
            ],
            "images": [],
            "follow_up_questions": [
                f"What are the latest developments in {query}?",
                f"How does {query} compare to alternatives?"
            ]
        }
        
        print(f"Mock search performed for: {query}")
        return mock_response


if __name__ == "__main__":
    """
    Example usage and testing of TavilySearchTool.
    """
    try:
        # Initialize Tavily search tool
        tavily_tool = TavilySearchTool()
        
        # Test search functionality
        print("Testing Tavily search...")
        test_query = "latest advancements in quantum computing"
        
        # Perform search
        search_results = tavily_tool.search(
            query=test_query,
            max_results=3,
            include_answer=True,
            search_depth="basic"
        )
        
        # Format and display results
        formatted_results = tavily_tool.format_results_for_agent(search_results)
        print("\nFormatted search results:")
        print(formatted_results)
        
        # Show performance stats
        print("\nPerformance statistics:")
        stats = tavily_tool.get_performance_stats()
        print(json.dumps(stats, indent=2))
        
        # Test mock search
        print("\nTesting mock search...")
        mock_results = tavily_tool.mock_search("artificial intelligence trends")
        formatted_mock = tavily_tool.format_results_for_agent(mock_results)
        print("\nFormatted mock results:")
        print(formatted_mock)
        
        print("\nTavilySearchTool testing completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        print("Make sure TAVILY_API_KEY is set in your .env file")
