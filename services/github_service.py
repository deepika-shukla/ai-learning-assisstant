"""
GitHub API Integration
Fetches relevant repositories and code examples for learning topics.
"""

import os
import httpx
from typing import Optional


class GitHubService:
    """
    Service for fetching GitHub repositories and code examples.
    Uses GitHub REST API (optional token for higher rate limits).
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize with optional GitHub token.
        Without token: 60 requests/hour
        With token: 5000 requests/hour
        
        Get token at: https://github.com/settings/tokens
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        
    def _get_headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Learning-Assistant"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def search_repositories(
        self,
        query: str,
        max_results: int = 5,
        language: Optional[str] = None,
        sort: str = "stars"
    ) -> list[dict]:
        """
        Search for GitHub repositories.
        
        Args:
            query: Search query (e.g., "machine learning tutorial")
            max_results: Number of repos to return
            language: Filter by programming language
            sort: Sort by "stars", "forks", or "updated"
            
        Returns:
            List of repository dictionaries
        """
        try:
            # Build search query
            search_query = f"{query} in:name,description,readme"
            if language:
                search_query += f" language:{language}"
            
            # Add qualifiers for quality
            search_query += " stars:>10"  # Filter out empty repos
            
            params = {
                "q": search_query,
                "sort": sort,
                "order": "desc",
                "per_page": min(max_results, 10)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/repositories",
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
            return self._parse_repos(data)
            
        except Exception as e:
            print(f"GitHub API error: {e}")
            return self._get_fallback_repos(query)
    
    async def get_readme(self, owner: str, repo: str) -> str:
        """
        Get the README content of a repository.
        
        Args:
            owner: Repository owner (e.g., "openai")
            repo: Repository name (e.g., "openai-python")
            
        Returns:
            README content as string
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        **self._get_headers(),
                        "Accept": "application/vnd.github.v3.raw"
                    }
                )
                
                if response.status_code == 200:
                    return response.text[:2000]  # First 2000 chars
                    
            return "README not available"
            
        except Exception as e:
            return f"Could not fetch README: {e}"
    
    async def get_trending(
        self,
        language: Optional[str] = None,
        since: str = "weekly"
    ) -> list[dict]:
        """
        Get trending repositories (approximation using search).
        
        Args:
            language: Filter by programming language
            since: Time period ("daily", "weekly", "monthly")
            
        Returns:
            List of trending repositories
        """
        # GitHub doesn't have official trending API
        # We approximate by searching for recent popular repos
        query = "stars:>100 pushed:>2024-01-01"
        if language:
            query += f" language:{language}"
            
        return await self.search_repositories(query, max_results=10, sort="stars")
    
    def _parse_repos(self, data: dict) -> list[dict]:
        """Parse GitHub API response."""
        repos = []
        
        for item in data.get("items", []):
            repos.append({
                "name": item.get("name", "Unknown"),
                "full_name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": item.get("description", "No description")[:200] if item.get("description") else "No description",
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "language": item.get("language", "Unknown"),
                "topics": item.get("topics", [])[:5],
                "updated_at": item.get("updated_at", ""),
                "owner": {
                    "name": item.get("owner", {}).get("login", "Unknown"),
                    "avatar": item.get("owner", {}).get("avatar_url", "")
                }
            })
            
        return repos
    
    def _get_fallback_repos(self, query: str) -> list[dict]:
        """Return curated fallback repos."""
        fallback_repos = {
            "python": [
                {
                    "name": "awesome-python",
                    "full_name": "vinta/awesome-python",
                    "url": "https://github.com/vinta/awesome-python",
                    "description": "A curated list of awesome Python frameworks, libraries, and resources",
                    "stars": 200000,
                    "forks": 24000,
                    "language": "Python",
                    "topics": ["python", "awesome-list"],
                    "owner": {"name": "vinta", "avatar": ""}
                }
            ],
            "machine learning": [
                {
                    "name": "awesome-machine-learning",
                    "full_name": "josephmisiti/awesome-machine-learning",
                    "url": "https://github.com/josephmisiti/awesome-machine-learning",
                    "description": "A curated list of awesome Machine Learning frameworks and libraries",
                    "stars": 60000,
                    "forks": 14000,
                    "language": "Python",
                    "topics": ["machine-learning", "deep-learning"],
                    "owner": {"name": "josephmisiti", "avatar": ""}
                }
            ],
            "default": [
                {
                    "name": f"Search GitHub",
                    "full_name": "search",
                    "url": f"https://github.com/search?q={query.replace(' ', '+')}",
                    "description": f"Search GitHub for repositories about {query}",
                    "stars": 0,
                    "forks": 0,
                    "language": "Various",
                    "topics": [],
                    "owner": {"name": "GitHub", "avatar": ""}
                }
            ]
        }
        
        query_lower = query.lower()
        for keyword, repos in fallback_repos.items():
            if keyword in query_lower:
                return repos
                
        return fallback_repos["default"]


# Synchronous wrappers
def search_github_repos(query: str, max_results: int = 5) -> list[dict]:
    """Synchronous wrapper for repository search."""
    import asyncio
    service = GitHubService()
    return asyncio.run(service.search_repositories(query, max_results))


def get_repo_readme(owner: str, repo: str) -> str:
    """Synchronous wrapper for README fetch."""
    import asyncio
    service = GitHubService()
    return asyncio.run(service.get_readme(owner, repo))
