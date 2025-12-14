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


class EmailSender:
    """Gmail SMTP 기반 이메일 발송기"""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = GMAIL_ADDRESS
        self.sender_password = GMAIL_APP_PASSWORD
        self.recipient_email = NOTIFY_EMAIL
        self.blog_name = TISTORY_BLOG_NAME

    def _create_email_html(self, article: dict) -> str:
        """복붙 친화적인 HTML 이메일 생성"""
        # 티스토리 글쓰기 페이지 URL
        write_url = f"https://{self.blog_name}.tistory.com/manage/newpost"

        # 태그 문자열 (복사용)
        tags_str = ", ".join(article.get("tags", []))

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; }}
        .header h1 {{ margin: 0 0 5px 0; font-size: 22px; }}
        .header .date {{ opacity: 0.9; font-size: 14px; }}
        .section {{ padding: 20px 25px; border-bottom: 1px solid #eee; }}
        .section:last-child {{ border-bottom: none; }}
        .section-title {{ font-size: 12px; text-transform: uppercase; color: #888; margin-bottom: 8px; letter-spacing: 1px; }}
        .copy-box {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin: 10px 0; font-family: inherit; }}
        .title-box {{ font-size: 18px; font-weight: bold; color: #333; }}
        .tags-box {{ color: #666; }}
        .content-box {{ max-height: 500px; overflow-y: auto; line-height: 1.8; }}
        .content-box h2 {{ color: #333; margin-top: 25px; margin-bottom: 15px; font-size: 20px; }}
        .content-box h3 {{ color: #444; margin-top: 20px; margin-bottom: 10px; font-size: 17px; }}
        .content-box p {{ margin: 12px 0; }}
        .content-box ul, .content-box ol {{ margin: 15px 0; padding-left: 25px; }}
        .content-box li {{ margin: 8px 0; }}
        .button-section {{ text-align: center; padding: 30px; background: #fafafa; }}
        .write-btn {{ display: inline-block; background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); color: white !important; padding: 16px 50px; border-radius: 8px; text-decoration: none; font-size: 18px; font-weight: bold; box-shadow: 0 4px 15px rgba(255,107,53,0.3); }}
        .write-btn:hover {{ opacity: 0.9; }}
        .steps {{ background: #fff3cd; border-radius: 8px; padding: 20px; margin: 20px 25px; }}
        .steps h3 {{ margin: 0 0 15px 0; color: #856404; font-size: 16px; }}
        .steps ol {{ margin: 0; padding-left: 20px; color: #856404; }}
        .steps li {{ margin: 8px 0; }}
        .meta-info {{ font-size: 14px; color: #666; }}
        .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; background: #fafafa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>새 블로그 글이 준비되었습니다</h1>
            <div class="date">{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} | {'정보형 글' if article.get('article_type') == 'info' else '체험형 글'}</div>
        </div>

        <div class="steps">
            <h3>발행 방법 (30초 컷)</h3>
            <ol>
                <li>아래 <strong>[티스토리에서 글쓰기]</strong> 버튼 클릭</li>
                <li>제목 복사 → 붙여넣기</li>
                <li>본문 복사 → 붙여넣기 (HTML 모드)</li>
                <li>태그 입력 → 발행!</li>
            </ol>
        </div>

        <div class="section">
            <div class="section-title">제목 (복사하세요)</div>
            <div class="copy-box title-box">{article.get('title', '제목 없음')}</div>
        </div>

        <div class="section">
            <div class="section-title">태그 (복사하세요)</div>
            <div class="copy-box tags-box">{tags_str}</div>
        </div>

        <div class="section">
            <div class="section-title">메타 설명</div>
            <div class="meta-info">{article.get('meta_description', '')}</div>
        </div>

        <div class="section">
            <div class="section-title">본문 (HTML 모드에서 복사하세요)</div>
            <div class="copy-box content-box">
                {article.get('content', '내용 없음')}
            </div>
        </div>

        <div class="button-section">
            <a href="{write_url}" class="write-btn" target="_blank">티스토리에서 글쓰기</a>
        </div>

        <div class="footer">
            <p>이 메일은 Auto-Blog 시스템에서 자동으로 발송되었습니다.</p>
            <p>카테고리: {article.get('category', 'N/A')} | 글 ID: {article.get('id', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
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
