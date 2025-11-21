"""
Financial Data Scraper Agent
Fetches financial data from various sources including Yahoo Finance, financial news, etc.
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class FinancialDataScraper:
    """Agent specialized in scraping financial data"""

    def __init__(self):
        self.user_agent = "Mozilla/5.0 (compatible; MultiAgentLearning/1.0)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_yahoo_finance(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Fetch stock data from Yahoo Finance

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary with ticker data
        """
        logger.info(f"Fetching Yahoo Finance data for tickers: {tickers}")

        results = {}

        for ticker in tickers:
            try:
                url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"

                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()

                if "quoteResponse" in data and "result" in data["quoteResponse"]:
                    quote_data = data["quoteResponse"]["result"]

                    if quote_data:
                        results[ticker] = {
                            "symbol": ticker,
                            "data": quote_data[0],
                            "fetched_at": datetime.now().isoformat()
                        }
                    else:
                        results[ticker] = {"error": "No data found"}
                else:
                    results[ticker] = {"error": "Invalid response format"}

            except requests.RequestException as e:
                logger.error(f"Error fetching data for {ticker}: {str(e)}")
                results[ticker] = {"error": str(e)}

        return results

    def fetch_financial_news(self, topic: str = "markets", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch financial news articles

        Args:
            topic: News topic to search for
            limit: Number of articles to fetch

        Returns:
            List of news articles
        """
        logger.info(f"Fetching financial news for topic: {topic}")

        articles = []

        try:
            # Example: Using a public news API or RSS feed
            # This is a placeholder - replace with actual news API
            url = f"https://news.ycombinator.com/item?id={topic}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse response (simplified)
            articles.append({
                "title": f"Financial News: {topic}",
                "content": response.text[:1000],
                "url": url,
                "fetched_at": datetime.now().isoformat()
            })

        except requests.RequestException as e:
            logger.error(f"Error fetching financial news: {str(e)}")

        return articles[:limit]

    def fetch_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch cryptocurrency prices

        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH'])

        Returns:
            Dictionary with crypto price data
        """
        logger.info(f"Fetching crypto prices for: {symbols}")

        results = {}

        try:
            # Using CoinGecko API (free, no auth required)
            symbol_ids = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana'
            }

            ids = [symbol_ids.get(s, s.lower()) for s in symbols]
            ids_str = ','.join(ids)

            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            for symbol in symbols:
                symbol_id = symbol_ids.get(symbol, symbol.lower())
                if symbol_id in data:
                    results[symbol] = {
                        "symbol": symbol,
                        "price_usd": data[symbol_id].get("usd"),
                        "change_24h": data[symbol_id].get("usd_24h_change"),
                        "fetched_at": datetime.now().isoformat()
                    }
                else:
                    results[symbol] = {"error": "Symbol not found"}

        except requests.RequestException as e:
            logger.error(f"Error fetching crypto prices: {str(e)}")
            for symbol in symbols:
                results[symbol] = {"error": str(e)}

        return results

    def fetch_economic_indicators(self) -> Dict[str, Any]:
        """
        Fetch economic indicators (simplified version)

        Returns:
            Dictionary with economic indicators
        """
        logger.info("Fetching economic indicators")

        # This is a placeholder - would integrate with FRED API or similar
        indicators = {
            "fetched_at": datetime.now().isoformat(),
            "note": "Integration with economic data APIs pending",
            "sources": ["FRED", "World Bank", "IMF"]
        }

        return indicators


# Standalone functions for backward compatibility
def fetch_yahoo_finance(tickers: List[str]) -> Dict[str, Any]:
    """Fetch Yahoo Finance data for given tickers"""
    scraper = FinancialDataScraper()
    return scraper.fetch_yahoo_finance(tickers)


def fetch_financial_news(topic: str = "markets", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch financial news articles"""
    scraper = FinancialDataScraper()
    return scraper.fetch_financial_news(topic, limit)


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    scraper = FinancialDataScraper()

    # Test Yahoo Finance
    print("Testing Yahoo Finance...")
    data = scraper.fetch_yahoo_finance(["AAPL", "GOOGL"])
    print(json.dumps(data, indent=2))

    # Test crypto prices
    print("\nTesting Crypto Prices...")
    crypto_data = scraper.fetch_crypto_prices(["BTC", "ETH"])
    print(json.dumps(crypto_data, indent=2))
