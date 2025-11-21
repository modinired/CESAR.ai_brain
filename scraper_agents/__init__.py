"""
Scraper agents for multi-agent learning ecosystem
"""

from .financial_data import fetch_yahoo_finance, fetch_financial_news
from .educational_materials import fetch_cpa_materials, fetch_coursera_courses
from .research_papers import fetch_arxiv_papers, search_arxiv

__all__ = [
    'fetch_yahoo_finance',
    'fetch_financial_news',
    'fetch_cpa_materials',
    'fetch_coursera_courses',
    'fetch_arxiv_papers',
    'search_arxiv'
]
