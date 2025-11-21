"""
Research Papers Scraper Agent
Fetches academic papers from arXiv and other sources
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class ResearchPaperScraper:
    """Agent specialized in scraping research papers"""

    def __init__(self):
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        self.user_agent = "Mozilla/5.0 (compatible; MultiAgentLearning/1.0)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_arxiv_papers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch papers from arXiv API

        Args:
            query: Search query (e.g., "machine learning", "cat:cs.AI")
            max_results: Maximum number of papers to fetch

        Returns:
            List of paper metadata and abstracts
        """
        logger.info(f"Fetching arXiv papers for query: {query}")

        papers = []

        try:
            # Build API request
            params = {
                "search_query": query,
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }

            response = self.session.get(self.arxiv_api_url, params=params, timeout=15)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)

            # Namespace for arXiv API
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            # Extract paper information
            for entry in root.findall('atom:entry', ns):
                paper = {}

                # Title
                title_elem = entry.find('atom:title', ns)
                paper['title'] = title_elem.text.strip() if title_elem is not None else "No title"

                # Abstract
                summary_elem = entry.find('atom:summary', ns)
                paper['abstract'] = summary_elem.text.strip() if summary_elem is not None else ""

                # Authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                paper['authors'] = authors

                # Published date
                published_elem = entry.find('atom:published', ns)
                paper['published'] = published_elem.text if published_elem is not None else ""

                # arXiv ID and link
                id_elem = entry.find('atom:id', ns)
                paper['url'] = id_elem.text if id_elem is not None else ""

                # Categories
                categories = []
                for category in entry.findall('atom:category', ns):
                    term = category.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = categories

                # PDF link
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        paper['pdf_url'] = link.get('href')

                paper['source'] = 'arXiv'
                paper['fetched_at'] = datetime.now().isoformat()

                papers.append(paper)

            logger.info(f"Successfully fetched {len(papers)} papers from arXiv")

        except requests.RequestException as e:
            logger.error(f"Error fetching arXiv papers: {str(e)}")
        except ET.ParseError as e:
            logger.error(f"Error parsing arXiv response: {str(e)}")

        return papers

    def search_arxiv_by_category(self, category: str = "cs.AI", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search arXiv by category

        Args:
            category: arXiv category (e.g., cs.AI, cs.LG, cs.CL)
            max_results: Maximum number of papers

        Returns:
            List of papers
        """
        query = f"cat:{category}"
        return self.fetch_arxiv_papers(query, max_results)

    def search_arxiv_by_author(self, author: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search arXiv by author name

        Args:
            author: Author name
            max_results: Maximum number of papers

        Returns:
            List of papers
        """
        query = f"au:{author}"
        return self.fetch_arxiv_papers(query, max_results)

    def fetch_recent_ai_papers(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent AI/ML papers from multiple categories

        Args:
            max_results: Maximum number of papers per category

        Returns:
            Combined list of papers
        """
        logger.info("Fetching recent AI/ML papers")

        all_papers = []

        categories = [
            "cs.AI",  # Artificial Intelligence
            "cs.LG",  # Machine Learning
            "cs.CL",  # Computation and Language
            "cs.CV",  # Computer Vision
        ]

        for category in categories:
            papers = self.search_arxiv_by_category(category, max_results // len(categories))
            all_papers.extend(papers)

        # Sort by published date (most recent first)
        all_papers.sort(key=lambda x: x.get('published', ''), reverse=True)

        return all_papers[:max_results]

    def fetch_semantic_scholar_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch papers from Semantic Scholar API (placeholder)

        Args:
            query: Search query
            limit: Number of papers to fetch

        Returns:
            List of papers
        """
        logger.info(f"Fetching Semantic Scholar papers for query: {query}")

        # This is a placeholder - would integrate with Semantic Scholar API
        papers = [{
            "title": f"Semantic Scholar: {query}",
            "note": "Integration with Semantic Scholar API pending",
            "fetched_at": datetime.now().isoformat()
        }]

        return papers

    def fetch_pubmed_papers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch medical/biological research papers from PubMed (placeholder)

        Args:
            query: Search query
            max_results: Maximum number of papers

        Returns:
            List of papers
        """
        logger.info(f"Fetching PubMed papers for query: {query}")

        # This is a placeholder - would integrate with PubMed API
        papers = [{
            "title": f"PubMed: {query}",
            "note": "Integration with PubMed API pending",
            "fetched_at": datetime.now().isoformat()
        }]

        return papers


# Standalone functions for backward compatibility
def fetch_arxiv_papers(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetch papers from arXiv"""
    scraper = ResearchPaperScraper()
    return scraper.fetch_arxiv_papers(query, max_results)


def search_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search arXiv (alias for fetch_arxiv_papers)"""
    return fetch_arxiv_papers(query, max_results)


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    scraper = ResearchPaperScraper()

    # Test arXiv search
    print("Testing arXiv search...")
    papers = scraper.fetch_arxiv_papers("machine learning", max_results=5)

    print(f"\nFetched {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'][:3])}")
        print(f"   Published: {paper['published']}")
        print(f"   Categories: {', '.join(paper['categories'])}")
        print(f"   URL: {paper['url']}")

    # Test category search
    print("\n\nTesting category search (cs.AI)...")
    ai_papers = scraper.search_arxiv_by_category("cs.AI", max_results=3)
    print(f"Fetched {len(ai_papers)} AI papers")

    # Test recent AI papers
    print("\n\nTesting recent AI/ML papers...")
    recent = scraper.fetch_recent_ai_papers(max_results=10)
    print(f"Fetched {len(recent)} recent AI/ML papers")
