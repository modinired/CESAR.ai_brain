"""
Educational Materials Scraper Agent
Fetches educational content from various sources
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class EducationalMaterialsScraper:
    """Agent specialized in scraping educational materials"""

    def __init__(self):
        self.user_agent = "Mozilla/5.0 (compatible; MultiAgentLearning/1.0)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_cpa_materials(self) -> List[Dict[str, Any]]:
        """
        Fetch CPA exam preparation materials

        Returns:
            List of CPA study materials
        """
        logger.info("Fetching CPA materials")

        materials = []

        # Sample sources for CPA materials
        sources = [
            {
                "name": "Becker CPA Free Sample",
                "url": "https://www.becker.com/cpa-review",
                "type": "course"
            },
            {
                "name": "AICPA Resources",
                "url": "https://www.aicpa.org/",
                "type": "resource"
            }
        ]

        for source in sources:
            try:
                response = self.session.get(source["url"], timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)

                # Extract title
                title = soup.find('title')
                title_text = title.get_text() if title else source["name"]

                materials.append({
                    "title": title_text,
                    "source": source["name"],
                    "url": source["url"],
                    "type": source["type"],
                    "content": text_content[:5000],  # Limit content
                    "word_count": len(text_content.split()),
                    "fetched_at": datetime.now().isoformat()
                })

            except requests.RequestException as e:
                logger.error(f"Error fetching {source['name']}: {str(e)}")
                materials.append({
                    "title": source["name"],
                    "error": str(e),
                    "url": source["url"]
                })

        return materials

    def fetch_coursera_courses(self, query: str = "data science", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch Coursera course information

        Args:
            query: Search query for courses
            limit: Number of courses to fetch

        Returns:
            List of course information
        """
        logger.info(f"Fetching Coursera courses for query: {query}")

        courses = []

        try:
            # Coursera browse page
            url = f"https://www.coursera.org/search?query={query.replace(' ', '%20')}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # This is a simplified example - actual scraping would need to handle
            # Coursera's dynamic content (likely requires Selenium)

            courses.append({
                "title": f"Coursera Courses: {query}",
                "url": url,
                "type": "course_catalog",
                "content": soup.get_text(separator=' ', strip=True)[:2000],
                "fetched_at": datetime.now().isoformat()
            })

        except requests.RequestException as e:
            logger.error(f"Error fetching Coursera courses: {str(e)}")

        return courses[:limit]

    def fetch_youtube_educational_content(self, topic: str) -> List[Dict[str, Any]]:
        """
        Fetch YouTube educational content metadata

        Args:
            topic: Topic to search for

        Returns:
            List of video metadata (Note: Actual implementation would use YouTube API)
        """
        logger.info(f"Fetching YouTube content for topic: {topic}")

        # This is a placeholder - actual implementation would use YouTube Data API
        content = [{
            "title": f"YouTube Educational Content: {topic}",
            "type": "video",
            "note": "Integration with YouTube Data API required for full functionality",
            "fetched_at": datetime.now().isoformat()
        }]

        return content

    def fetch_khan_academy_content(self, subject: str = "math") -> List[Dict[str, Any]]:
        """
        Fetch Khan Academy content

        Args:
            subject: Subject area to fetch

        Returns:
            List of educational content
        """
        logger.info(f"Fetching Khan Academy content for subject: {subject}")

        materials = []

        try:
            # Khan Academy subject page
            url = f"https://www.khanacademy.org/{subject}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            text_content = soup.get_text(separator=' ', strip=True)

            materials.append({
                "title": f"Khan Academy: {subject.title()}",
                "source": "Khan Academy",
                "url": url,
                "type": "educational_resource",
                "content": text_content[:5000],
                "fetched_at": datetime.now().isoformat()
            })

        except requests.RequestException as e:
            logger.error(f"Error fetching Khan Academy content: {str(e)}")

        return materials

    def fetch_mit_ocw_courses(self, department: str = "computer-science") -> List[Dict[str, Any]]:
        """
        Fetch MIT OpenCourseWare materials

        Args:
            department: Department to fetch courses from

        Returns:
            List of course materials
        """
        logger.info(f"Fetching MIT OCW courses for department: {department}")

        courses = []

        try:
            url = f"https://ocw.mit.edu/search/?d={department}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract course information
            text_content = soup.get_text(separator=' ', strip=True)

            courses.append({
                "title": f"MIT OCW: {department.replace('-', ' ').title()}",
                "source": "MIT OpenCourseWare",
                "url": url,
                "type": "university_course",
                "content": text_content[:5000],
                "fetched_at": datetime.now().isoformat()
            })

        except requests.RequestException as e:
            logger.error(f"Error fetching MIT OCW courses: {str(e)}")

        return courses


# Standalone functions for backward compatibility
def fetch_cpa_materials() -> List[Dict[str, Any]]:
    """Fetch CPA study materials"""
    scraper = EducationalMaterialsScraper()
    return scraper.fetch_cpa_materials()


def fetch_coursera_courses(query: str = "data science", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch Coursera courses"""
    scraper = EducationalMaterialsScraper()
    return scraper.fetch_coursera_courses(query, limit)


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    scraper = EducationalMaterialsScraper()

    # Test CPA materials
    print("Testing CPA Materials...")
    materials = scraper.fetch_cpa_materials()
    print(f"Fetched {len(materials)} CPA materials")

    # Test Khan Academy
    print("\nTesting Khan Academy...")
    khan_content = scraper.fetch_khan_academy_content("math")
    print(f"Fetched {len(khan_content)} Khan Academy materials")
