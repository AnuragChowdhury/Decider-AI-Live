"""
Web Search Tool for Market Intelligence
Provides external context, trends, and news to enhance decision-making.
"""

from typing import List, Dict, Any
from ddgs import DDGS
import re

class WebSearchTool:
    """
    Searches the web using DuckDuckGo for market trends, news, and context.
    """
    
    def __init__(self):
        self.ddg = DDGS()
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Performs a web search and returns results.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 5, max: 10)
            
        Returns:
            {
                "success": bool,
                "query": str,
                "results": [
                    {
                        "title": str,
                        "snippet": str,
                        "url": str
                    }
                ],
                "summary": str (concatenated snippets),
                "error": str (if failed)
            }
        """
        if max_results > 10:
            max_results = 10
            
        try:
            # Perform search
            results = list(self.ddg.text(query, max_results=max_results))
            
            # Format results
            formatted_results = []
            snippets = []
            
            for r in results[:max_results]:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
                snippets.append(r.get("body", ""))
            
            # Create summary
            summary = " | ".join(snippets[:3])  # First 3 results
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "summary": summary,
                "result_count": len(formatted_results),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "results": [],
                "summary": "",
                "result_count": 0,
                "error": f"Search failed: {str(e)}"
            }
    
    def search_news(self, topic: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Searches for recent news about a topic.
        """
        query = f"{topic} news latest trends 2026"
        return self.search(query, max_results)
    
    def search_market_trends(self, industry: str, product: str = None, max_results: int = 3) -> Dict[str, Any]:
        """
        Searches for market trends in a specific industry/product.
        
        Example:
            search_market_trends("automotive", "classic cars")
        """
        if product:
            query = f"{product} {industry} market trends forecast 2026"
        else:
            query = f"{industry} market trends forecast 2026"
        
        return self.search(query, max_results)

# Singleton instance
web_search_tool = WebSearchTool()

def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Helper function to search the web.
    
    Example:
        result = search_web("electric vehicle market trends 2026")
    """
    return web_search_tool.search(query, max_results)

def search_market_intel(industry: str, product: str = None) -> Dict[str, Any]:
    """
    Helper function to get market intelligence.
    
    Example:
        result = search_market_intel("automotive", "classic cars")
    """
    return web_search_tool.search_market_trends(industry, product)

from langchain_core.tools import tool

@tool
def search_internet(query: str) -> str:
    """
    Search the internet for market trends, news, and external context. 
    Use for questions about market trends, news, external comparisons.
    """
    # Logic is handled manually in the graph, this is just for schema binding
    return ""
