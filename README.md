# Auto-Blog

AI 기반 블로그 자동화 시스템. 뉴스를 수집하고, AI가 글을 작성하고, 이메일로 발송합니다.

## 프로젝트 구조

```
auto-blog/
├── main.py                 # 진입점 (여기서 시작)
├── requirements.txt        # 필요한 라이브러리 목록
├── .env                    # 비밀 설정 (API 키 등)
│
├── config/
│   └── settings.py         # 설정값 모음
│
├── src/                    # 핵심 기능 모듈들
│   ├── news_collector.py   # 1. 뉴스 수집
│   ├── content_generator.py # 2. AI 글 생성
│   ├── email_sender.py     # 3. 이메일 발송
│   └── templates/
│       └── prompts.py      # AI에게 줄 지시문
│
├── data/
│   └── articles/           # 생성된 글 저장소
│
└── .github/workflows/
    └── daily_post.yml      # 자동 실행 설정 (GitHub Actions)
```

## 데이터 흐름

```
[1] 뉴스 수집          [2] AI 글 생성         [3] 이메일 발송

Google News  ──→  news_collector.py  ──→  뉴스 데이터
                                              │
                                              ▼
                  content_generator.py  ←─────┘
                         │
                         ▼
                    블로그 글 (JSON)
                         │
                         ├──→  data/articles/에 저장
                         │
                         ▼
                  email_sender.py  ──→  Gmail로 발송
```

## 설치 방법

### 1. 의존성 설치

```bash
cd auto-blog
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 다음 값들을 채워주세요:

| 변수명               | 설명                 | 발급 방법                                                       |
| -------------------- | -------------------- | --------------------------------------------------------------- |
| `GEMINI_API_KEY`     | Google Gemini API 키 | [Google AI Studio](https://aistudio.google.com/apikey)          |
| `GMAIL_ADDRESS`      | 발송할 Gmail 주소    | -                                                               |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호    | [Google 앱 비밀번호](https://myaccount.google.com/apppasswords) |
| `NOTIFY_EMAIL`       | 알림 받을 이메일     | -                                                               |
| `TISTORY_BLOG_NAME`  | 티스토리 블로그 이름 | URL에서 확인 (예: `myblog`.tistory.com)                         |

## 사용 방법

### 정보형 글 생성 (AI 뉴스)

```bash
# 자동 카테고리 선택 (일단 AI 100%)
python main.py info

# 특정 카테고리 지정
python main.py info --category ai
```

### 저장된 글 목록 보기

```bash
python main.py list
```

## 각 파일 역할

### `main.py` - 지휘자

모든 모듈을 조합해서 실행하는 메인 함수입니다.

```python
def generate_info_article(category):
    # 1. 뉴스 수집
    collector = NewsCollector()
    news = collector.collect_news(category)

    # 2. AI로 글 생성
    generator = ContentGenerator()
    article = generator.generate_info_article(news)

    # 3. 파일로 저장
    save_article(article)

    # 4. 이메일 발송
    sender = EmailSender()
    sender.send_article(article)
```

### `src/news_collector.py` - 뉴스 수집기

Google News RSS에서 뉴스를 가져옵니다.

```python
class NewsCollector:
    def collect_news(self, category):
        # 반환값 예시:
        return {
            "category": "ai",
            "category_name": "AI/인공지능",
            "main_article": {
                "title": "ChatGPT 5.0 출시",
                "source": "조선일보"
            },
            "related_articles": [...]
        }
```

### `src/content_generator.py` - AI 글 생성기

Gemini API를 사용해 블로그 글을 생성합니다.

```python
class ContentGenerator:
    def generate_info_article(self, news_data):
        # AI에게 글 작성 요청
        response = self.model.generate_content(prompt)

        # JSON 형태로 반환
        return {
            "title": "...",
            "content": "<h2>...</h2><p>...</p>",
            "tags": ["AI", "테크", ...]
        }
```

### `src/email_sender.py` - 이메일 발송기

생성된 글을 Gmail로 발송합니다. 복붙하기 쉬운 형태의 HTML 이메일입니다.

### `src/templates/prompts.py` - AI 지시문

AI에게 줄 프롬프트(지시문) 템플릿입니다. SEO 최적화된 블로그 글을 작성하도록 지시합니다.

### `config/settings.py` - 설정 모음

환경변수와 카테고리 설정을 관리합니다.

```python
CATEGORIES = {
    "ai": {
        "name": "AI/인공지능",
        "keywords": ["AI", "ChatGPT", ...],
        "weight": 1,  # 100% 확률로 선택
    },
    # "tech": {  },
    # "economy": {  },
}
```

## 발행 방법

1. `python main.py info` 실행
2. 이메일 확인
3. **[티스토리에서 글쓰기]** 버튼 클릭
4. 제목/본문 복붙
5. 태그 입력 → 발행!

## GitHub Actions 자동화

`.github/workflows/daily_post.yml` 설정으로 매일 자동 실행됩니다.

GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 환경변수를 설정하세요.

## 기술 스택

- **Python 3.11+**
- **Google Gemini API** - AI 글 생성
- **Google News RSS** - 뉴스 수집
- **Gmail SMTP** - 이메일 발송
- **GitHub Actions** - 자동화 스케줄링
