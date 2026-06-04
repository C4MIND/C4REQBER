"""News aggregation, ticker feed, and local storage for c44tcdi v4.1"""

from src.news.aggregator import NewsAggregator
from src.news.storage import NewsStorage


__all__ = ["NewsAggregator", "NewsStorage"]
