"""
Google Gemini API를 사용한 블로그 글 생성 모듈
"""
import json
import re
import sys
import os

import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GEMINI_API_KEY
from src.templates.prompts import INFO_ARTICLE_PROMPT, EXPERIENCE_ARTICLE_PROMPT


class ContentGenerator:
    """Gemini 기반 콘텐츠 생성기"""

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

    def _parse_json_response(self, text: str) -> dict:
        """응답에서 JSON 추출"""
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
            text = re.sub(r'(?<!\\)\n', '\\n', text)
            # 이스케이프 안 된 탭 처리
            text = re.sub(r'(?<!\\)\t', '\\t', text)
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 세 번째 시도: content 필드만 추출해서 재구성
        try:
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', text)
            meta_match = re.search(r'"meta_description"\s*:\s*"([^"]*)"', text)
            content_match = re.search(r'"content"\s*:\s*"(.*?)",\s*"tags"', text, re.DOTALL)
            tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            category_match = re.search(r'"category"\s*:\s*"([^"]*)"', text)

            if title_match and content_match:
                # 태그 파싱
                tags = []
                if tags_match:
                    tags = [t.strip().strip('"') for t in tags_match.group(1).split(',')]

                return {
                    "title": title_match.group(1),
                    "meta_description": meta_match.group(1) if meta_match else "",
                    "content": content_match.group(1).replace('\n', '\\n'),
                    "tags": tags,
                    "category": category_match.group(1) if category_match else "",
                }
        except Exception:
            pass

        raise ValueError(f"JSON 파싱 실패\n원본: {text[:500]}")

    def generate_info_article(self, news_data: dict) -> dict:
        """정보형 글 생성"""
        related = "\n".join(
            [f"  - {a['title']} ({a['source']})" for a in news_data.get("related_articles", [])]
        )

        prompt = INFO_ARTICLE_PROMPT.format(
            category_name=news_data["category_name"],
            main_title=news_data["main_article"]["title"],
            main_link=news_data["main_article"]["link"],
            source=news_data["main_article"]["source"],
            related_articles=related or "없음",
        )

        response = self.model.generate_content(prompt)
        article = self._parse_json_response(response.text)

        article["article_type"] = "info"
        article["source_news"] = news_data["main_article"]["title"]

        return article

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


# 테스트
if __name__ == "__main__":
    from src.news_collector import NewsCollector

    collector = NewsCollector()
    news = collector.collect_news("ai")

    print(f"수집된 뉴스: {news['main_article']['title']}")
    print("\n글 생성 중...")

    generator = ContentGenerator()
    article = generator.generate_info_article(news)

    print(f"\n=== 생성된 글 ===")
    print(f"제목: {article['title']}")
    print(f"메타: {article['meta_description']}")
    print(f"태그: {', '.join(article['tags'])}")
    print(f"\n본문 미리보기:\n{article['content'][:500]}...")
