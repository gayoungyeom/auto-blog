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

# Content Categories (weight 합계 = 1.0)
CATEGORIES = {
    "ai": {
        "name": "AI/인공지능",
        "keywords": ["AI", "인공지능", "ChatGPT", "GPT", "LLM", "머신러닝", "딥러닝", "OpenAI", "Gemini", "Claude"],
        "weight": 0.25,
    },
    "health": {
        "name": "건강/웰빙",
        "keywords": ["건강", "다이어트", "운동", "영양제", "수면", "스트레스", "면역력", "헬스", "요가", "명상"],
        "weight": 0.25,
    },
    "economy": {
        "name": "경제/재테크",
        "keywords": ["경제", "주식", "부동산", "금리", "투자", "저축", "연금", "ETF", "재테크", "물가"],
        "weight": 0.25,
    },
    "lifestyle": {
        "name": "생활/라이프",
        "keywords": ["생활", "인테리어", "정리", "청소", "절약", "꿀팁", "홈케어", "가전", "수납", "미니멀"],
        "weight": 0.25,
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
