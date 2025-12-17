"""
Pollinations.ai를 사용한 무료 썸네일 생성 모듈
"""
import os
import requests
from urllib.parse import quote
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 썸네일 저장 경로
THUMBNAIL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "thumbnails")


class ThumbnailGenerator:
    """Pollinations.ai 기반 무료 썸네일 생성기"""

    BASE_URL = "https://image.pollinations.ai/prompt"

    # 트렌디하고 깔끔한 스타일 프롬프트
    STYLE_PROMPT = (
        "minimalist, modern, clean design, trendy, professional, "
        "soft gradient background, subtle lighting, high quality, "
        "blog thumbnail style, no text, no watermark"
    )

    def __init__(self):
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    def _translate_to_english(self, title: str, tags: list[str]) -> str:
        """제목과 태그를 영어 키워드로 변환 (간단한 매핑)"""
        # 주요 한글 키워드 -> 영어 매핑
        keyword_map = {
            "인공지능": "artificial intelligence",
            "AI": "AI technology",
            "챗봇": "chatbot",
            "로봇": "robot",
            "자동화": "automation",
            "머신러닝": "machine learning",
            "딥러닝": "deep learning",
            "테크": "technology",
            "스타트업": "startup",
            "앱": "mobile app",
            "클라우드": "cloud computing",
            "데이터": "data analytics",
            "보안": "cybersecurity",
            "블록체인": "blockchain",
            "메타버스": "metaverse",
            "VR": "virtual reality",
            "AR": "augmented reality",
            "건강": "health wellness",
            "다이어트": "diet fitness",
            "운동": "exercise workout",
            "영양제": "supplements vitamins",
            "경제": "economy finance",
            "주식": "stock market",
            "부동산": "real estate",
            "투자": "investment",
            "생활": "lifestyle",
            "인테리어": "interior design",
            "요리": "cooking food",
            "맛집": "restaurant food",
            "레시피": "recipe cooking",
        }

        english_keywords = []

        # 제목에서 키워드 추출
        for kor, eng in keyword_map.items():
            if kor in title:
                english_keywords.append(eng)
                if len(english_keywords) >= 2:
                    break

        # 태그에서 영어 키워드 추출
        for tag in tags[:3]:  # 상위 3개 태그만 사용
            if len(english_keywords) >= 4:
                break
            tag_lower = tag.lower()
            if tag_lower in keyword_map:
                if keyword_map[tag_lower] not in english_keywords:
                    english_keywords.append(keyword_map[tag_lower])
            elif tag.isascii():  # 이미 영어인 경우
                if tag not in english_keywords:
                    english_keywords.append(tag)
            else:
                # 매핑에 없는 한글은 기본 키워드로
                for kor, eng in keyword_map.items():
                    if kor in tag and eng not in english_keywords:
                        english_keywords.append(eng)
                        break

        # 기본 키워드 추가
        if not english_keywords:
            english_keywords = ["technology", "digital", "innovation"]

        return ", ".join(english_keywords[:4])

    def _build_prompt(self, title: str, tags: list[str], category: str = "") -> str:
        """이미지 생성용 프롬프트 구성"""
        keywords = self._translate_to_english(title, tags)

        # 카테고리별 추가 스타일
        category_style = {
            "ai": "futuristic, neural network visualization, blue and purple tones",
            "tech": "modern gadgets, sleek design, tech aesthetic",
            "economy": "business, finance, growth charts, professional",
            "startup": "innovation, entrepreneurship, modern office",
        }

        extra_style = category_style.get(category.lower(), "modern, professional")

        prompt = f"{keywords}, {extra_style}, {self.STYLE_PROMPT}"
        return prompt

    def generate_thumbnail_url(self, title: str, tags: list[str], category: str = "") -> str:
        """썸네일 이미지 URL 생성 (다운로드 없이 URL만 반환)"""
        prompt = self._build_prompt(title, tags, category)
        encoded_prompt = quote(prompt)

        # 1:1 비율 (1024x1024)
        url = f"{self.BASE_URL}/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return url

    def download_thumbnail(self, title: str, tags: list[str], category: str = "", filename: str = None) -> str:
        """썸네일 이미지 다운로드 및 저장"""
        url = self.generate_thumbnail_url(title, tags, category)

        # 파일명 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thumbnail_{timestamp}.png"

        filepath = os.path.join(THUMBNAIL_DIR, filename)

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"썸네일 저장 완료: {filepath}")
            return filepath

        except requests.RequestException as e:
            print(f"썸네일 다운로드 실패: {e}")
            return ""


# 테스트
if __name__ == "__main__":
    generator = ThumbnailGenerator()

    # 테스트 데이터
    test_title = "ChatGPT 5.0 출시 임박, 달라지는 3가지"
    test_tags = ["ChatGPT", "AI", "OpenAI", "GPT-5"]
    test_category = "ai"

    # URL 생성 테스트
    url = generator.generate_thumbnail_url(test_title, test_tags, test_category)
    print(f"\n=== 썸네일 URL ===")
    print(url)

    # 다운로드 테스트
    print(f"\n=== 썸네일 다운로드 ===")
    filepath = generator.download_thumbnail(test_title, test_tags, test_category)
    if filepath:
        print(f"저장 위치: {filepath}")
