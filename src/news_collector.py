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

    def _fetch_news(self, query: str, lang: str = "ko", country: str = "KR", max_results: int = 10) -> list[dict]:
        """RSS 피드에서 뉴스 가져오기"""
        encoded_query = quote(query, safe='')
        url = f"{self.BASE_URL}?q={encoded_query}&hl={lang}&gl={country}&ceid={country}:{lang}"

        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:max_results]:
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

    def collect_news(
        self,
        category: Optional[str] = None,
        languages: Optional[list[tuple[str, str]]] = None
    ) -> dict:
        """뉴스 수집 메인 함수 (글로벌 뉴스 지원)

        Args:
            category: 수집할 카테고리 (None이면 가중치 기반 랜덤 선택)
            languages: (언어코드, 국가코드) 튜플 리스트
                       기본값: [("ko", "KR"), ("en", "US")]
                       예시: [("ja", "JP"), ("de", "DE")]
        """
        if category is None:
            category = self.select_category()

        if languages is None:
            languages = [("ko", "KR"), ("en", "US")]

        cat_info = self.categories[category]
        query = self._build_query(cat_info["keywords"])

        # 여러 언어/국가에서 기사 수집
        all_articles = []
        for lang, country in languages:
            articles = self._fetch_news(query, lang=lang, country=country)
            for article in articles:
                article["lang"] = lang
                article["country"] = country
            all_articles.extend(articles)

        # 중복 제거 (링크 기준)
        seen_links = set()
        unique_articles = []
        for article in all_articles:
            if article["link"] not in seen_links:
                seen_links.add(article["link"])
                unique_articles.append(article)

        if not unique_articles:
            # 폴백: AI 카테고리로 재시도
            if category != "ai":
                return self.collect_news("ai", languages=languages)
            return {"category": category, "articles": [], "error": "No articles found"}

        # 가장 관련성 높은 기사 선택 (첫 번째 기사)
        main_article = unique_articles[0]
        related_articles = unique_articles[1:4]  # 참고용 관련 기사 3개

        return {
            "category": category,
            "category_name": cat_info["name"],
            "main_article": main_article,
            "related_articles": related_articles,
            "collected_at": datetime.now().isoformat(),
            "languages": languages,
        }

    def collect_news_titles(
        self,
        category: Optional[str] = None,
        languages: Optional[list[tuple[str, str]]] = None,
        max_per_lang: int = 15
    ) -> dict:
        """뉴스 제목만 다량 수집 (주제 선정용)

        Args:
            category: 수집할 카테고리 (None이면 가중치 기반 랜덤 선택)
            languages: (언어코드, 국가코드) 튜플 리스트
            max_per_lang: 언어별 최대 수집 개수 (기본 15개)

        Returns:
            카테고리 정보와 뉴스 제목 리스트
        """
        if category is None:
            category = self.select_category()

        if languages is None:
            languages = [("ko", "KR"), ("en", "US")]

        cat_info = self.categories[category]

        # 모든 키워드 사용 (랜덤 선택 없이)
        query = " OR ".join(cat_info["keywords"][:5])

        # 여러 언어/국가에서 제목 수집
        all_titles = []
        for lang, country in languages:
            articles = self._fetch_news(query, lang=lang, country=country, max_results=max_per_lang)
            for article in articles:
                all_titles.append({
                    "title": article["title"],
                    "source": article["source"],
                    "lang": lang,
                })

        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_titles = []
        for item in all_titles:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                unique_titles.append(item)

        return {
            "category": category,
            "category_name": cat_info["name"],
            "titles": unique_titles,
            "collected_at": datetime.now().isoformat(),
        }


# 테스트
if __name__ == "__main__":
    collector = NewsCollector()

    # 기본: 한국어 + 영어 뉴스 수집
    result = collector.collect_news()
    print(f"\n=== 글로벌 뉴스 수집 (기본: 한국어 + 영어) ===")
    print(f"카테고리: {result['category_name']}")
    print(f"수집 언어: {result['languages']}")
    print(f"\n메인 기사: {result['main_article']['title']}")
    print(f"출처: {result['main_article']['source']}")
    print(f"언어/국가: {result['main_article']['lang']}/{result['main_article']['country']}")
    print(f"\n관련 기사:")
    for i, article in enumerate(result['related_articles'], 1):
        print(f"  {i}. [{article['lang']}] {article['title']}")

    # 영어만 수집 예시
    print(f"\n=== 영어만 수집 ===")
    result_en = collector.collect_news(languages=[("en", "US")])
    print(f"메인 기사: {result_en['main_article']['title']}")
