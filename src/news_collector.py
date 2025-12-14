"""
Google News RSS를 통한 뉴스 수집 모듈
"""
import feedparser
import random
from datetime import datetime
from typing import Optional
from urllib.parse import quote
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import CATEGORIES


class NewsCollector:
    """Google News RSS 기반 뉴스 수집기"""

    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self):
        self.categories = CATEGORIES

    def _build_query(self, keywords: list[str], days: int = 2) -> str:
        """검색 쿼리 생성"""
        # 키워드 중 랜덤하게 2-3개 선택
        selected = random.sample(keywords, min(3, len(keywords)))
        query = " OR ".join(selected)
        return query

    def _fetch_news(self, query: str, lang: str = "ko", country: str = "KR") -> list[dict]:
        """RSS 피드에서 뉴스 가져오기"""
        encoded_query = quote(query, safe='')
        url = f"{self.BASE_URL}?q={encoded_query}&hl={lang}&gl={country}&ceid={country}:{lang}"

        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:10]:  # 최대 10개
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
            })

        return articles

    def select_category(self) -> str:
        """가중치 기반 카테고리 선택"""
        categories = list(self.categories.keys())
        weights = [self.categories[c]["weight"] for c in categories]
        return random.choices(categories, weights=weights, k=1)[0]

    def collect_news(self, category: Optional[str] = None) -> dict:
        """뉴스 수집 메인 함수"""
        if category is None:
            category = self.select_category()

        cat_info = self.categories[category]
        query = self._build_query(cat_info["keywords"])
        articles = self._fetch_news(query)

        if not articles:
            # 폴백: AI 카테고리로 재시도
            if category != "ai":
                return self.collect_news("ai")
            return {"category": category, "articles": [], "error": "No articles found"}

        # 가장 관련성 높은 기사 선택 (첫 번째 기사)
        main_article = articles[0]
        related_articles = articles[1:4]  # 참고용 관련 기사 3개

        return {
            "category": category,
            "category_name": cat_info["name"],
            "main_article": main_article,
            "related_articles": related_articles,
            "collected_at": datetime.now().isoformat(),
        }


# 테스트
if __name__ == "__main__":
    collector = NewsCollector()
    result = collector.collect_news()
    print(f"\n카테고리: {result['category_name']}")
    print(f"메인 기사: {result['main_article']['title']}")
    print(f"출처: {result['main_article']['source']}")
    print(f"\n관련 기사:")
    for i, article in enumerate(result['related_articles'], 1):
        print(f"  {i}. {article['title']}")
