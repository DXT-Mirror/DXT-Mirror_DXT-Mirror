"""
Strategic GitHub repository discovery for DXT-related projects.

This module implements a targeted search strategy that focuses on quality over quantity.
Instead of broad scraping, we use carefully crafted search queries and intelligent
filtering to find repositories that are likely to be DXT-related.

Key Design Principles:
1. Strategic Queries: Use specific search terms that indicate DXT relevance
2. Quality Filtering: Exclude empty, archived, or obviously irrelevant repositories
3. Relevance Ranking: Score repositories based on multiple relevance indicators
4. Rate Limiting: Respect GitHub API limits while maximizing discovery efficiency

Why This Approach Works:
- GitHub's search API is powerful but requires strategic use
- Quality filtering reduces noise and focuses on viable repositories
- Relevance ranking ensures we evaluate the most promising repositories first
- Rate limiting prevents API exhaustion while allowing sustained discovery
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """
    Represents a single repository discovered through GitHub search.
    
    This class encapsulates all the relevant information about a repository
    that we need for further evaluation. We store both the basic metadata
    and additional context that helps with relevance assessment.
    """
    full_name: str          # Repository identifier (owner/repo)
    clone_url: str          # HTTPS clone URL
    ssh_url: str            # SSH clone URL
    description: str        # Repository description
    stars: int              # Star count (popularity indicator)
    forks: int              # Fork count (community engagement)
    language: str           # Primary programming language
    updated_at: str         # Last update timestamp
    created_at: str         # Creation timestamp
    size: int               # Repository size in KB
    archived: bool          # Whether repository is archived
    is_fork: bool           # Whether this is a fork of another repository
    topics: List[str]       # Repository topics/tags
    license: str            # License type
    parent_repo: Optional[str] = None  # Parent repository if this is a fork
    fork_analysis: str = ""  # Analysis of fork characteristics


class StrategicGitHubSearch:
    """
    Strategic GitHub repository discovery system.
    
    This class implements a focused search strategy that maximizes the likelihood
    of finding relevant DXT repositories while minimizing API usage and noise.
    
    The strategy is based on:
    1. Targeted search queries that use DXT-specific terminology
    2. Quality filters that exclude obviously irrelevant repositories
    3. Intelligent ranking that prioritizes the most promising candidates
    4. Respectful rate limiting that works within GitHub's API constraints
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the strategic search system.
        
        Args:
            github_token: Optional GitHub API token for higher rate limits
        """
        self.github_token = github_token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'DXT-Curator-Strategic-Search'
        }
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def search_repositories(self, query: str, min_stars: int = 0, max_results: int = 100) -> List[SearchResult]:
        """
        Execute a strategic search for repositories.
        
        This method implements intelligent search with quality filtering. It:
        1. Uses GitHub's search API with strategic parameters
        2. Applies real-time quality filters to reduce noise
        3. Handles rate limiting gracefully
        4. Returns structured results ready for AI evaluation
        
        Args:
            query: Search query string
            min_stars: Minimum star count filter
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        results = []
        page = 1
        per_page = 100
        
        while len(results) < max_results:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': query,
                'sort': 'updated',      # Most recently updated first
                'order': 'desc',        # Descending order
                'per_page': per_page,
                'page': page
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            # Handle rate limiting gracefully
            if response.status_code == 403:
                print("Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
                continue
            
            if response.status_code != 200:
                print(f"Search API error: {response.status_code}")
                break
            
            data = response.json()
            
            if not data.get('items'):
                break
            
            for item in data['items']:
                # Apply quality filters in real-time
                # This reduces the amount of data we need to process later
                
                # Skip repositories with too few stars (if specified)
                if item['stargazers_count'] < min_stars:
                    continue
                
                # Skip archived repositories (they're not actively maintained)
                if item.get('archived', False):
                    continue
                
                # Skip repositories with no description (likely incomplete)
                if not item.get('description', '').strip():
                    continue
                
                # Skip repositories with zero size (likely empty)
                if item.get('size', 0) == 0:
                    continue
                
                # Analyze fork characteristics
                parent_repo = None
                fork_analysis = ""
                
                if item.get('fork', False):
                    # Get parent repository information
                    parent_repo = item.get('parent', {}).get('full_name') if item.get('parent') else None
                    
                    # Analyze fork characteristics
                    fork_analysis = self._analyze_fork_characteristics(item)
                
                # Create structured result
                result = SearchResult(
                    full_name=item['full_name'],
                    clone_url=item['clone_url'],
                    ssh_url=item['ssh_url'],
                    description=item.get('description', ''),
                    stars=item['stargazers_count'],
                    forks=item['forks_count'],
                    language=item.get('language', ''),
                    updated_at=item['updated_at'],
                    created_at=item['created_at'],
                    size=item.get('size', 0),
                    archived=item.get('archived', False),
                    is_fork=item.get('fork', False),
                    topics=item.get('topics', []),
                    parent_repo=parent_repo,
                    fork_analysis=fork_analysis,
                    license=item.get('license', {}).get('name', '') if item.get('license') else ''
                )
                
                results.append(result)
                
                if len(results) >= max_results:
                    break
            
            # If we got fewer results than requested, we've reached the end
            if len(data['items']) < per_page:
                break
            
            page += 1
            time.sleep(1)  # Rate limiting: 1 second between requests
        
        return results
    
    def _analyze_fork_characteristics(self, repo_item: Dict[str, Any]) -> str:
        """
        Analyze fork characteristics to determine if it's worth evaluating.
        
        This method looks at various indicators to determine if a fork has
        sufficient unique content to warrant separate evaluation.
        
        Args:
            repo_item: Repository data from GitHub API
            
        Returns:
            Human-readable analysis of fork characteristics
        """
        parent = repo_item.get('parent', {})
        if not parent:
            return "Fork without parent information"
        
        # Size comparison
        fork_size = repo_item.get('size', 0)
        parent_size = parent.get('size', 0)
        size_ratio = fork_size / parent_size if parent_size > 0 else 0
        
        # Star comparison
        fork_stars = repo_item.get('stargazers_count', 0)
        parent_stars = parent.get('stargazers_count', 0)
        
        # Activity comparison
        fork_updated = repo_item.get('updated_at', '')
        parent_updated = parent.get('updated_at', '')
        
        # Language comparison
        fork_language = repo_item.get('language', '')
        parent_language = parent.get('language', '')
        
        # Build analysis
        analysis_parts = []
        
        if size_ratio > 1.5:
            analysis_parts.append("significantly larger than parent")
        elif size_ratio > 1.2:
            analysis_parts.append("moderately larger than parent")
        elif size_ratio < 0.8:
            analysis_parts.append("smaller than parent")
        else:
            analysis_parts.append("similar size to parent")
        
        if fork_stars > parent_stars:
            analysis_parts.append("more popular than parent")
        elif fork_stars > 10:
            analysis_parts.append("has community engagement")
        elif fork_stars == 0:
            analysis_parts.append("no community engagement")
        
        if fork_updated > parent_updated:
            analysis_parts.append("more recently updated")
        elif fork_updated < parent_updated:
            analysis_parts.append("less recently updated")
        
        if fork_language != parent_language:
            analysis_parts.append(f"different language ({fork_language} vs {parent_language})")
        
        # Create summary
        if size_ratio > 1.5 or fork_stars > parent_stars or fork_updated > parent_updated:
            classification = "Fork with significant changes"
        elif size_ratio > 1.2 or fork_stars > 10:
            classification = "Fork with moderate changes"
        elif fork_stars > 0 or fork_updated >= parent_updated:
            classification = "Fork with minor changes"
        else:
            classification = "Fork with minimal changes"
        
        return f"{classification} - {', '.join(analysis_parts)}"
    
    def get_dxt_search_queries(self) -> List[Dict[str, Any]]:
        """
        Get strategic DXT search queries with priorities.
        
        This method defines our search strategy. Each query is designed to find
        repositories that are likely to be DXT-related, with different priorities
        based on the specificity and expected yield of each query.
        
        Query Design Philosophy:
        1. High Priority: Specific DXT terminology with high precision
        2. Medium Priority: Broader terms that might catch related projects
        3. Balanced Approach: Not too narrow (miss relevant repos) or too broad (too much noise)
        
        Returns:
            List of query configurations with search terms and parameters
        """
        return [
            {
                'query': 'claude desktop extension',
                'priority': 'high',
                'min_stars': 1,
                'max_results': 50,
                'rationale': 'Direct match for Claude Desktop Extensions'
            },
            {
                'query': 'claude mcp server',
                'priority': 'high',
                'min_stars': 0,
                'max_results': 30,
                'rationale': 'MCP (Model Context Protocol) servers for Claude'
            },
            {
                'query': 'anthropic claude tool',
                'priority': 'medium',
                'min_stars': 0,
                'max_results': 20,
                'rationale': 'General Claude tools from Anthropic ecosystem'
            },
            {
                'query': 'claude computer use',
                'priority': 'high',
                'min_stars': 0,
                'max_results': 20,
                'rationale': 'Computer use functionality with Claude'
            },
            {
                'query': 'claude automation workflow',
                'priority': 'medium',
                'min_stars': 0,
                'max_results': 15,
                'rationale': 'Automation and workflow tools using Claude'
            },
            {
                'query': 'claude api integration',
                'priority': 'medium',
                'min_stars': 0,
                'max_results': 15,
                'rationale': 'API integrations and wrappers for Claude'
            },
            {
                'query': 'claude desktop tools',
                'priority': 'medium',
                'min_stars': 0,
                'max_results': 10,
                'rationale': 'Desktop tools that work with Claude'
            },
            {
                'query': 'mcp protocol server',
                'priority': 'medium',
                'min_stars': 0,
                'max_results': 10,
                'rationale': 'MCP protocol implementations'
            }
        ]
    
    def discover_dxt_repositories(self) -> List[SearchResult]:
        """
        Execute strategic DXT repository discovery.
        
        This is the main discovery method that:
        1. Executes all strategic search queries
        2. Deduplicates results across queries
        3. Applies quality filtering
        4. Returns a comprehensive list of potential DXT repositories
        
        The method is designed to be thorough but efficient, balancing
        discovery completeness with API rate limits.
        
        Returns:
            List of unique SearchResult objects
        """
        print("🔍 Starting strategic DXT repository discovery...")
        
        all_results = []
        seen_repos = set()  # Track repository names to avoid duplicates
        
        search_queries = self.get_dxt_search_queries()
        
        for query_config in search_queries:
            print(f"Searching: {query_config['query']} (priority: {query_config['priority']})")
            
            # Execute the search query
            results = self.search_repositories(
                query_config['query'],
                query_config['min_stars'],
                query_config['max_results']
            )
            
            # Deduplicate results
            # This is important because repositories might match multiple queries
            new_results = []
            for result in results:
                if result.full_name not in seen_repos:
                    seen_repos.add(result.full_name)
                    new_results.append(result)
            
            all_results.extend(new_results)
            print(f"  Found {len(new_results)} new repositories")
            
            # Brief pause between searches to be respectful to GitHub API
            time.sleep(2)
        
        print(f"✅ Discovery complete: {len(all_results)} unique repositories found")
        return all_results
    
    def filter_by_recency(self, results: List[SearchResult], days: int = 365) -> List[SearchResult]:
        """
        Filter repositories by recent activity.
        
        This filter helps us focus on actively maintained repositories by
        excluding those that haven't been updated recently. The rationale is
        that actively maintained repositories are more likely to be useful
        for mirroring and have current, relevant code.
        
        Args:
            results: List of search results to filter
            days: Number of days to consider "recent"
            
        Returns:
            Filtered list of SearchResult objects
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = []
        for result in results:
            try:
                # Parse the GitHub timestamp format
                updated_date = datetime.fromisoformat(result.updated_at.replace('Z', '+00:00'))
                if updated_date > cutoff_date:
                    filtered.append(result)
            except (ValueError, AttributeError):
                # If date parsing fails, include the repo (better safe than sorry)
                filtered.append(result)
        
        return filtered
    
    def filter_by_activity(self, results: List[SearchResult], min_stars: int = 0, min_size: int = 1) -> List[SearchResult]:
        """
        Filter repositories by activity indicators.
        
        This filter uses stars and repository size as proxy indicators for
        repository quality and activity. While not perfect, these metrics
        help us prioritize repositories that have community engagement and
        substantial content.
        
        Args:
            results: List of search results to filter
            min_stars: Minimum star count
            min_size: Minimum repository size in KB
            
        Returns:
            Filtered list of SearchResult objects
        """
        filtered = []
        for result in results:
            if result.stars >= min_stars and result.size >= min_size:
                filtered.append(result)
        
        return filtered
    
    def rank_by_relevance(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank repositories by DXT relevance indicators.
        
        This method implements a sophisticated relevance scoring system that
        considers multiple factors to determine which repositories are most
        likely to be valuable DXT-related projects.
        
        Scoring Factors:
        1. Star count (community validation)
        2. Repository size (substantial content)
        3. Programming language (preference for common DXT languages)
        4. Description keywords (DXT-specific terminology)
        5. Repository topics (tagged with relevant topics)
        6. Recency (recently updated projects)
        7. Fork penalty (prefer original projects)
        
        Args:
            results: List of search results to rank
            
        Returns:
            List of SearchResult objects sorted by relevance score (highest first)
        """
        def relevance_score(repo: SearchResult) -> float:
            """Calculate relevance score for a single repository."""
            score = 0.0
            
            # Star weighting (community validation)
            # More stars indicate community interest and validation
            score += min(repo.stars * 0.1, 5.0)
            
            # Size weighting (substantial content)
            # Prefer repositories with meaningful content, but not too large
            if 1 <= repo.size <= 10000:  # Sweet spot for meaningful projects
                score += min(repo.size * 0.001, 2.0)
            
            # Language bonuses
            # Prefer languages commonly used in DXT projects
            if repo.language in ['Python', 'JavaScript', 'TypeScript']:
                score += 1.0
            elif repo.language in ['Go', 'Rust', 'Java']:
                score += 0.5
            
            # Description keyword bonuses
            # Look for DXT-specific terminology in descriptions
            desc_lower = repo.description.lower()
            high_value_keywords = ['claude', 'anthropic', 'mcp', 'desktop', 'extension', 'automation']
            for keyword in high_value_keywords:
                if keyword in desc_lower:
                    score += 2.0
            
            # Topics bonuses
            # GitHub topics provide additional context
            for topic in repo.topics:
                if any(keyword in topic.lower() for keyword in ['claude', 'anthropic', 'mcp', 'ai']):
                    score += 1.0
            
            # Recency bonus
            # Prefer recently updated repositories
            try:
                updated_date = datetime.fromisoformat(repo.updated_at.replace('Z', '+00:00'))
                days_ago = (datetime.now().replace(tzinfo=updated_date.tzinfo) - updated_date).days
                if days_ago < 30:
                    score += 2.0
                elif days_ago < 90:
                    score += 1.0
            except (ValueError, AttributeError):
                pass
            
            # Fork penalty
            # Prefer original repositories over forks
            if repo.is_fork:
                score -= 1.0
            
            return score
        
        # Sort by relevance score in descending order
        return sorted(results, key=relevance_score, reverse=True)
    
    def export_results(self, results: List[SearchResult], filename: str = "strategic_search_results.json") -> None:
        """
        Export search results to JSON file.
        
        This method converts SearchResult objects to a JSON format that can
        be easily processed by other parts of the system, particularly the
        AI evaluation components.
        
        Args:
            results: List of search results to export
            filename: Output filename
        """
        data = []
        for result in results:
            data.append({
                'full_name': result.full_name,
                'clone_url': result.clone_url,
                'ssh_url': result.ssh_url,
                'description': result.description,
                'stars': result.stars,
                'forks': result.forks,
                'language': result.language,
                'updated_at': result.updated_at,
                'created_at': result.created_at,
                'size': result.size,
                'archived': result.archived,
                'is_fork': result.is_fork,
                'topics': result.topics,
                'license': result.license
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📁 Results exported to {filename}")


def main():
    """
    CLI interface for repository discovery.
    
    This provides command-line access to the discovery functionality,
    useful for testing and manual discovery operations.
    """
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Strategic GitHub Search for DXT Repositories')
    parser.add_argument('--token', help='GitHub token (or use GITHUB_MIRROR_TOKEN/GITHUB_TOKEN env var)')
    parser.add_argument('--output', default='strategic_search_results.json', help='Output file')
    parser.add_argument('--min-stars', type=int, default=0, help='Minimum stars filter')
    parser.add_argument('--days', type=int, default=365, help='Only repos updated in last N days')
    parser.add_argument('--limit', type=int, help='Limit total results')
    
    args = parser.parse_args()
    
    # Get GitHub token from environment or command line
    token = args.token or os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not token:
        print("⚠️  Warning: No GitHub token provided. Rate limits will be very low.")
    
    # Initialize searcher
    searcher = StrategicGitHubSearch(token)
    
    # Execute discovery
    results = searcher.discover_dxt_repositories()
    
    # Apply filters
    if args.days:
        results = searcher.filter_by_recency(results, args.days)
        print(f"📅 After recency filter: {len(results)} repositories")
    
    if args.min_stars:
        results = searcher.filter_by_activity(results, args.min_stars)
        print(f"⭐ After stars filter: {len(results)} repositories")
    
    # Rank by relevance
    results = searcher.rank_by_relevance(results)
    
    # Apply limit
    if args.limit:
        results = results[:args.limit]
        print(f"🔢 Limited to: {len(results)} repositories")
    
    # Export results
    searcher.export_results(results, args.output)
    
    # Print summary
    print(f"\n📊 Search Summary:")
    print(f"Total repositories found: {len(results)}")
    
    if results:
        print(f"\n🌟 Top 5 repositories by relevance:")
        for i, repo in enumerate(results[:5]):
            print(f"  {i+1}. {repo.full_name} ({repo.stars} ⭐) - {repo.description[:60]}...")


if __name__ == "__main__":
    main()