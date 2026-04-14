"""
Source Discovery Service for Discovery Lab V8
Searches arXiv, Wikipedia, and other academic sources
"""

import aiohttp
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SourceType(str, Enum):
    ARXIV = "arxiv"
    WIKIPEDIA = "wikipedia"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    UPLOAD = "upload"


@dataclass
class Source:
    id: str
    type: SourceType
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: Optional[str]
    url: Optional[str]
    relevance_score: float = 1.0
    is_selected: bool = True
    metadata: Dict[str, Any] = None


class SourceDiscoveryService:
    """Service for discovering academic and knowledge sources"""
    
    def __init__(self):
        self.arxiv_base = "http://export.arxiv.org/api/query"
        self.wikipedia_base = "https://en.wikipedia.org/w/api.php"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
    
    async def search(
        self,
        query: str,
        sources: List[str] = None,
        max_results: int = 10,
        locale: str = 'en'
    ) -> List[Source]:
        """
        Search multiple sources
        
        Args:
            query: Search query
            sources: List of sources to search ['arxiv', 'wikipedia', 'semantic_scholar']
            max_results: Maximum results per source
            locale: Language code
        
        Returns:
            List of Source objects
        """
        if sources is None:
            sources = ['arxiv', 'wikipedia']
        
        all_sources = []
        
        if 'arxiv' in sources:
            arxiv_results = await self.search_arxiv(query, max_results // 2)
            all_sources.extend(arxiv_results)
        
        if 'wikipedia' in sources:
            wiki_results = await self.search_wikipedia(query, max_results // 2, locale)
            all_sources.extend(wiki_results)
        
        if 'semantic_scholar' in sources:
            ss_results = await self.search_semantic_scholar(query, max_results // 2)
            all_sources.extend(ss_results)
        
        # Sort by relevance (mock scoring for now)
        all_sources.sort(key=lambda s: s.relevance_score, reverse=True)
        
        return all_sources[:max_results]
    
    async def search_arxiv(self, query: str, max_results: int = 5) -> List[Source]:
        """Search arXiv papers"""
        try:
            # Format query for arXiv
            search_query = query.replace(' ', '+')
            url = f"{self.arxiv_base}?search_query=all:{search_query}&start=0&max_results={max_results}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        return []
                    
                    xml_content = await response.text()
                    return self._parse_arxiv_response(xml_content)
        except Exception as e:
            print(f"arXiv search error: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Source]:
        """Parse arXiv XML response"""
        import xml.etree.ElementTree as ET
        
        sources = []
        try:
            root = ET.fromstring(xml_content)
            # arXiv Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                id_elem = entry.find('atom:id', ns)
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text)
                
                # Extract year
                year = None
                if published is not None:
                    try:
                        year = int(published.text[:4])
                    except:
                        pass
                
                # Build source
                source_id = id_elem.text.split('/')[-1] if id_elem is not None else "unknown"
                
                sources.append(Source(
                    id=f"arxiv-{source_id}",
                    type=SourceType.ARXIV,
                    title=title.text.strip() if title is not None else "Unknown",
                    authors=authors[:3],  # Limit authors
                    year=year,
                    abstract=summary.text[:500] + "..." if summary is not None and len(summary.text) > 500 else (summary.text if summary is not None else None),
                    url=id_elem.text if id_elem is not None else None,
                    relevance_score=0.9
                ))
        except Exception as e:
            print(f"Parse arXiv error: {e}")
        
        return sources
    
    async def search_wikipedia(
        self, 
        query: str, 
        max_results: int = 5,
        locale: str = 'en'
    ) -> List[Source]:
        """Search Wikipedia articles"""
        try:
            # Use Wikipedia API
            lang = 'ru' if locale == 'ru' else 'en'
            base_url = f"https://{lang}.wikipedia.org/w/api.php"
            
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    return self._parse_wikipedia_response(data, lang)
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def _parse_wikipedia_response(self, data: dict, lang: str) -> List[Source]:
        """Parse Wikipedia API response"""
        sources = []
        
        search_results = data.get('query', {}).get('search', [])
        
        for result in search_results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            page_id = result.get('pageid', '')
            
            # Clean snippet (remove HTML)
            import re
            clean_snippet = re.sub('<.*?>', '', snippet)
            
            sources.append(Source(
                id=f"wiki-{page_id}",
                type=SourceType.WIKIPEDIA,
                title=title,
                authors=[],
                year=None,
                abstract=clean_snippet[:300] + "..." if len(clean_snippet) > 300 else clean_snippet,
                url=f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                relevance_score=0.8
            ))
        
        return sources
    
    async def search_semantic_scholar(
        self, 
        query: str, 
        max_results: int = 5
    ) -> List[Source]:
        """Search Semantic Scholar"""
        try:
            url = f"{self.semantic_scholar_base}/paper/search"
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'title,authors,year,abstract,url'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    return self._parse_semantic_scholar_response(data)
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []
    
    def _parse_semantic_scholar_response(self, data: dict) -> List[Source]:
        """Parse Semantic Scholar API response"""
        sources = []
        
        papers = data.get('data', [])
        
        for paper in papers:
            paper_id = paper.get('paperId', '')
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            year = paper.get('year')
            
            authors = [a.get('name', '') for a in paper.get('authors', [])]
            
            sources.append(Source(
                id=f"ss-{paper_id}",
                type=SourceType.SEMANTIC_SCHOLAR,
                title=title,
                authors=authors[:3],
                year=year,
                abstract=abstract[:500] + "..." if abstract and len(abstract) > 500 else abstract,
                url=paper.get('url'),
                relevance_score=0.85
            ))
        
        return sources


# Singleton instance
_source_service: Optional[SourceDiscoveryService] = None


def get_source_service() -> SourceDiscoveryService:
    """Get or create singleton SourceDiscoveryService"""
    global _source_service
    if _source_service is None:
        _source_service = SourceDiscoveryService()
    return _source_service
