"""
Google Gemini API를 사용한 블로그 글 생성 모듈
"""
import json
import re
import sys
import os
import hashlib
from datetime import datetime
from pathlib import Path

import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GEMINI_API_KEY
from src.templates.prompts import (
    EXPERIENCE_ARTICLE_PROMPT,
    UNIFIED_ARTICLE_PROMPT,
)


class ContentGenerator:
    """Gemini 기반 콘텐츠 생성기"""

    # 캐시 디렉토리
    CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "max_output_tokens": 8192,
            }
        )
        # 캐시 디렉토리 생성
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, news_titles: list, category: str) -> str:
        """뉴스 제목 기반 캐시 키 생성 (당일 기준)"""
        today = datetime.now().strftime("%Y%m%d")
        titles_str = "|".join(sorted([t["title"] for t in news_titles[:10]]))
        content = f"{today}:{category}:{titles_str}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _get_cached_article(self, cache_key: str) -> dict | None:
        """캐시된 글 가져오기"""
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
                # 당일 캐시만 유효
                if cached.get("cached_date") == datetime.now().strftime("%Y%m%d"):
                    print("📦 캐시된 글 사용")
                    return cached.get("article")
        return None

    def _save_to_cache(self, cache_key: str, article: dict):
        """글 캐시에 저장"""
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        cache_data = {
            "cached_date": datetime.now().strftime("%Y%m%d"),
            "cached_at": datetime.now().isoformat(),
            "article": article,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def _parse_json_response(self, text: str) -> dict:
        """응답에서 JSON 추출"""
        original_text = text  # 디버깅용 원본 저장

        # JSON 블록 찾기
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # 중괄호로 시작하는 JSON 찾기
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

        # 첫 번째 시도: 그대로 파싱
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 두 번째 시도: content 필드 내 문제가 있는 문자 수정
        try:
            # JSON 문자열 내부의 이스케이프 안 된 줄바꿈 처리
            fixed_text = re.sub(r'(?<!\\)\n', '\\n', text)
            # 이스케이프 안 된 탭 처리
            fixed_text = re.sub(r'(?<!\\)\t', '\\t', fixed_text)
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass

        # 세 번째 시도: 필드별로 추출해서 재구성
        try:
            result = {}

            # 기본 문자열 필드들 추출
            string_fields = [
                "trend_summary", "reader_perspective", "selected_topic",
                "title", "meta_description", "category"
            ]
            for field in string_fields:
                match = re.search(rf'"{field}"\s*:\s*"([^"]*)"', text)
                if match:
                    result[field] = match.group(1)

            # content 필드 (HTML 포함, 복잡함) - tags 앞까지 추출
            content_match = re.search(r'"content"\s*:\s*"(.*?)",\s*"tags"', text, re.DOTALL)
            if content_match:
                content = content_match.group(1)
                # 이스케이프 처리
                content = content.replace('\n', '').replace('\r', '')
                result["content"] = content

            # tags 배열 추출
            tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [t.strip().strip('"').strip("'") for t in tags_str.split(',') if t.strip()]
                result["tags"] = tags

            # 필수 필드 확인
            if result.get("title") and result.get("content"):
                return result

        except Exception as e:
            print(f"필드별 추출 실패: {e}")

        # 네 번째 시도: content 필드 내 따옴표 이스케이프 문제 해결
        try:
            # content 내부의 이스케이프 안 된 따옴표 처리
            fixed_text = re.sub(r'(?<!\\)"(?=[^:,\[\]{}]*[,\]\}])', '\\"', text)
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass

        raise ValueError(f"JSON 파싱 실패\n원본: {original_text[:1000]}")

    def generate_experience_article(self, user_memo: str, category: str = "일상/리뷰") -> dict:
        """체험형 글 생성"""
        prompt = EXPERIENCE_ARTICLE_PROMPT.format(
            user_memo=user_memo,
            category=category,
        )

        response = self.model.generate_content(prompt)
        article = self._parse_json_response(response.text)

        article["article_type"] = "experience"
        article["user_memo"] = user_memo

        return article

    def generate_unified_article(self, news_data: dict, use_cache: bool = True) -> dict:
        """뉴스 흐름 분석 + 글 작성을 1회 API 호출로 처리

        Args:
            news_data: collect_news_titles()의 반환값
            use_cache: 캐시 사용 여부 (기본: True)

        Returns:
            생성된 블로그 글 데이터
        """
        category = news_data.get("category", "ai")
        category_name = news_data.get("category_name", "AI/테크")
        titles = news_data.get("titles", [])

        # 캐시 확인
        if use_cache:
            cache_key = self._get_cache_key(titles, category)
            cached = self._get_cached_article(cache_key)
            if cached:
                return cached

        # 뉴스 제목을 문자열로 변환
        titles_str = "\n".join([f"- {item['title']}" for item in titles])

        # 통합 프롬프트로 1회 API 호출
        print("📰 뉴스 분석 및 글 생성 중... (1회 API 호출)")
        prompt = UNIFIED_ARTICLE_PROMPT.format(
            news_titles=titles_str,
            category_name=category_name,
        )

        response = self.model.generate_content(prompt)
        article = self._parse_json_response(response.text)

        # 결과 출력
        print(f"📊 트렌드: {article.get('trend_summary', '')}")
        print(f"👀 독자 관점: {article.get('reader_perspective', '')}")
        print(f"💡 선정된 주제: {article.get('selected_topic', '')}")
        print(f"✍️ 제목: {article.get('title', '')}")

        # 메타데이터 추가
        article["article_type"] = "unified"
        article["source_topic"] = article.get("selected_topic", "")

        # 캐시 저장
        if use_cache:
            self._save_to_cache(cache_key, article)
            print("💾 캐시에 저장됨")

        return article


# 테스트
if __name__ == "__main__":
    from src.news_collector import NewsCollector

    collector = NewsCollector()
    generator = ContentGenerator()

    print("=" * 50)
    print("통합 글 생성 테스트 (1회 API 호출)")
    print("=" * 50)

    # 뉴스 제목 수집
    news_data = collector.collect_news_titles()
    print(f"\n카테고리: {news_data['category_name']}")
    print(f"수집된 뉴스 제목 수: {len(news_data['titles'])}")

    # 통합 글 생성
    article = generator.generate_unified_article(news_data, use_cache=False)

    print(f"\n{'=' * 50}")
    print("=== 생성된 글 ===")
    print(f"{'=' * 50}")
    print(f"제목: {article['title']}")
    print(f"메타: {article['meta_description']}")
    print(f"태그: {', '.join(article['tags'])}")
    print(f"\n본문 미리보기:\n{article['content'][:800]}...")
