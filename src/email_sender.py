"""
Gmail SMTP를 통한 이메일 발송 모듈
복붙 친화적인 블로그 글 전송
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    NOTIFY_EMAIL,
    TISTORY_BLOG_NAME,
)
from src.thumbnail_generator import ThumbnailGenerator

# 템플릿 파일 경로
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
EMAIL_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "email_template.html")


class EmailSender:
    """Gmail SMTP 기반 이메일 발송기"""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = GMAIL_ADDRESS
        self.sender_password = GMAIL_APP_PASSWORD
        self.recipient_email = NOTIFY_EMAIL
        self.blog_name = TISTORY_BLOG_NAME
        self.thumbnail_generator = ThumbnailGenerator()

    def _load_template(self) -> str:
        """HTML 템플릿 파일 로드"""
        with open(EMAIL_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def _create_email_html(self, article: dict) -> str:
        """복붙 친화적인 HTML 이메일 생성"""
        template = self._load_template()

        # 티스토리 글쓰기 페이지 URL
        write_url = f"https://{self.blog_name}.tistory.com/manage/newpost"

        # 태그 문자열 (복사용)
        tags_str = ", ".join(article.get("tags", []))

        # 글 유형
        article_type = "정보형 글" if article.get("article_type") == "info" else "체험형 글"

        # 썸네일 URL 생성
        thumbnail_url = self.thumbnail_generator.generate_thumbnail_url(
            title=article.get("title", ""),
            tags=article.get("tags", []),
            category=article.get("category", ""),
        )

        # 템플릿 변수 치환
        html = template.format(
            date=datetime.now().strftime("%Y년 %m월 %d일 %H:%M"),
            article_type=article_type,
            title=article.get("title", "제목 없음"),
            tags=tags_str,
            meta_description=article.get("meta_description", ""),
            content=article.get("content", "내용 없음"),
            write_url=write_url,
            category=article.get("category", "N/A"),
            article_id=article.get("id", "N/A"),
            thumbnail_url=thumbnail_url,
        )

        return html

    def _create_plain_text(self, article: dict) -> str:
        """플레인 텍스트 버전 (이메일 클라이언트 호환용)"""
        tags_str = ", ".join(article.get("tags", []))

        # HTML 태그 간단히 제거
        content = article.get('content', '')
        import re
        content_plain = re.sub(r'<[^>]+>', '\n', content)
        content_plain = re.sub(r'\n{3,}', '\n\n', content_plain)

        return f"""
새 블로그 글이 준비되었습니다
생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}
유형: {'정보형 글' if article.get('article_type') == 'info' else '체험형 글'}

{'='*50}

[제목]
{article.get('title', '제목 없음')}

[태그]
{tags_str}

[메타 설명]
{article.get('meta_description', '')}

[본문]
{content_plain}

{'='*50}

티스토리 글쓰기: https://{self.blog_name}.tistory.com/manage/newpost
"""

    def send_article(self, article: dict) -> bool:
        """블로그 글 이메일 발송"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Auto-Blog] {article.get('title', '새 글')}"
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email

            # 플레인 텍스트와 HTML 모두 첨부
            plain_content = self._create_plain_text(article)
            html_content = self._create_email_html(article)

            msg.attach(MIMEText(plain_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"이메일 발송 완료: {self.recipient_email}")
            return True

        except Exception as e:
            print(f"이메일 발송 실패: {e}")
            return False

    def send_simple_notification(self, subject: str, message: str) -> bool:
        """간단한 텍스트 알림 이메일"""
        try:
            msg = MIMEText(message, "plain", "utf-8")
            msg["Subject"] = f"[Auto-Blog] {subject}"
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"알림 발송 실패: {e}")
            return False


# 테스트
if __name__ == "__main__":
    sender = EmailSender()

    test_article = {
        "id": "test-001",
        "title": "ChatGPT 5.0 출시 임박, 달라지는 3가지",
        "meta_description": "OpenAI가 차세대 AI 모델을 준비 중입니다.",
        "content": "<h2>들어가며</h2><p>OpenAI가 새로운 GPT 모델을 준비하고 있습니다.</p><h2>주요 변화</h2><p>이번 업데이트에서는 다음과 같은 변화가 예상됩니다.</p>",
        "tags": ["ChatGPT", "AI", "OpenAI", "GPT-5"],
        "category": "AI/인공지능",
        "article_type": "info",
    }

    sender.send_article(test_article)
