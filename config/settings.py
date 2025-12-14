import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gmail Settings
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")

# Tistory Blog (블로그 이름만 필요 - URL 생성용)
TISTORY_BLOG_NAME = os.getenv("TISTORY_BLOG_NAME")

# Content Categories
CATEGORIES = {
    "ai": {
        "name": "AI/인공지능",
        "keywords": ["AI", "인공지능", "ChatGPT", "GPT", "LLM", "머신러닝", "딥러닝", "OpenAI", "Gemini", "Claude"],
        "weight": 0.7,  # 70% 확률
    },
    "tech": {
        "name": "테크 리뷰",
        "keywords": ["스마트폰", "애플", "삼성", "구글", "테크", "가젯", "앱", "소프트웨어"],
        "weight": 0.15,
    },
    "economy": {
        "name": "시사/경제",
        "keywords": ["경제", "주식", "투자", "금리", "환율", "부동산", "스타트업"],
        "weight": 0.15,
    },
}

# Publishing Schedule
PUBLISH_SCHEDULE = {
    "info_article": {
        "frequency": "daily",  # daily or every_other_day
        "time": "09:00",
    },
    "experience_article": {
        "frequency": "weekly",
        "day": "saturday",
        "time": "10:00",
    },
}

# Article Settings
ARTICLE_CONFIG = {
    "min_length": 1500,
    "max_length": 2500,
    "keyword_density": 0.025,  # 2.5%
}
