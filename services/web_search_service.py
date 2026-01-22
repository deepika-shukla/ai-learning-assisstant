"""
Web Search Service using DuckDuckGo
Free, no API key required!

INTERVIEW TIP: This demonstrates external API integration
and gives the AI access to real-time web information.
"""

import asyncio
from typing import Optional


class WebSearchService:
    """
    Web search using DuckDuckGo.
    
    INTERVIEW TIP: DuckDuckGo is chosen because:
    1. No API key required (easy setup)
    2. No rate limits for reasonable usage
    3. Privacy-focused (good for users)
    4. Returns quality results
    """
    
    def __init__(self):
        self.results_per_query = 5
    
    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "source": "DuckDuckGo"
                    })
            
            return results
            
        except ImportError:
            print("⚠️ duckduckgo-search not installed. Run: pip install duckduckgo-search")
            return []
        except Exception as e:
            print(f"⚠️ Web search error: {e}")
            return []
    
    def search_news(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search for recent news articles.
        
        INTERVIEW TIP: Separating news search allows users
        to get current events vs general information.
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("body", ""),
                        "date": r.get("date", ""),
                        "source": r.get("source", "News")
                    })
            
            return results
            
        except ImportError:
            return []
        except Exception as e:
            print(f"⚠️ News search error: {e}")
            return []
    
    def search_for_learning(self, topic: str) -> dict:
        """
        Specialized search for learning resources.
        Combines tutorials, documentation, and articles.
        
        INTERVIEW TIP: This shows domain-specific API usage -
        tailoring generic search for educational purposes.
        """
        results = {
            "tutorials": [],
            "documentation": [],
            "articles": []
        }
        
        try:
            # Search for tutorials
            tutorial_results = self.search(f"{topic} tutorial for beginners", max_results=3)
            results["tutorials"] = tutorial_results
            
            # Search for documentation
            doc_results = self.search(f"{topic} official documentation", max_results=2)
            results["documentation"] = doc_results
            
            # Search for articles/guides
            article_results = self.search(f"{topic} guide how to learn", max_results=3)
            results["articles"] = article_results
            
        except Exception as e:
            print(f"⚠️ Learning search error: {e}")
        
        return results
    
    def format_results(self, results: list[dict]) -> str:
        """
        Format search results for display.
        
        Returns nicely formatted string for CLI output.
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"""
🔗 **{i}. {r.get('title', 'No title')}**
   {r.get('snippet', 'No description')[:150]}...
   📎 {r.get('url', '')}
""")
        
        return "\n".join(formatted)


# Quick test
if __name__ == "__main__":
    service = WebSearchService()
    
    print("🔍 Testing web search...")
    results = service.search("Python programming tutorial")
    print(service.format_results(results))
    
    print("\n📰 Testing news search...")
    news = service.search_news("artificial intelligence")
    print(service.format_results(news))
