"""
Auto-Blog 메인 스크립트
뉴스 수집 → 글 생성 → 이메일 발송 파이프라인
"""
import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from src.news_collector import NewsCollector
from src.content_generator import ContentGenerator
from src.email_sender import EmailSender


# 글 저장소
ARTICLES_DIR = Path(__file__).parent / "data" / "articles"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def save_article(article: dict) -> str:
    """글 저장 및 ID 반환"""
    article_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    article["id"] = article_id
    article["created_at"] = datetime.now().isoformat()

    file_path = ARTICLES_DIR / f"{article_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    return article_id


def generate_info_article(category: str = None) -> dict:
    """정보형 글 생성 파이프라인"""
    print("=" * 50)
    print("정보형 글 생성 시작")
    print("=" * 50)

    # 1. 뉴스 수집
    print("\n[1/4] 뉴스 수집 중...")
    collector = NewsCollector()
    news = collector.collect_news(category)

    if "error" in news:
        print(f"뉴스 수집 실패: {news['error']}")
        return None

    print(f"  - 카테고리: {news['category_name']}")
    print(f"  - 메인 기사: {news['main_article']['title']}")

    # 2. 글 생성
    print("\n[2/4] AI 글 생성 중...")
    generator = ContentGenerator()
    article = generator.generate_info_article(news)
    print(f"  - 제목: {article['title']}")
    print(f"  - 태그: {', '.join(article['tags'])}")

    # 3. 글 저장
    print("\n[3/4] 글 저장 중...")
    article_id = save_article(article)
    print(f"  - ID: {article_id}")

    # 4. 이메일 발송
    print("\n[4/4] 이메일 발송 중...")
    sender = EmailSender()
    success = sender.send_article(article)

    if success:
        print("\n완료! 이메일을 확인하세요.")
        print("티스토리에서 복붙 후 발행하면 됩니다.")
    else:
        print("\n이메일 발송 실패. 글은 저장되었습니다.")
        print(f"저장 위치: {ARTICLES_DIR / f'{article_id}.json'}")

    return article


def generate_experience_article(memo: str, category: str = "일상/리뷰") -> dict:
    """체험형 글 생성 파이프라인"""
    print("=" * 50)
    print("체험형 글 생성 시작")
    print("=" * 50)

    # 1. 글 생성
    print("\n[1/3] AI 글 생성 중...")
    generator = ContentGenerator()
    article = generator.generate_experience_article(memo, category)
    print(f"  - 제목: {article['title']}")
    print(f"  - 필요한 사진 수: {article.get('photo_count', 0)}개")

    # 2. 글 저장
    print("\n[2/3] 글 저장 중...")
    article_id = save_article(article)
    print(f"  - ID: {article_id}")

    # 3. 이메일 발송
    print("\n[3/3] 이메일 발송 중...")
    sender = EmailSender()
    success = sender.send_article(article)

    if success:
        print("\n완료! 이메일을 확인하세요.")
        print(f"사진 {article.get('photo_count', 0)}개를 준비한 후 발행하세요.")
    else:
        print("\n이메일 발송 실패.")
        print(f"저장 위치: {ARTICLES_DIR / f'{article_id}.json'}")

    return article


def list_articles():
    """저장된 글 목록"""
    print("\n저장된 글 목록:")
    print("-" * 50)

    articles = []
    for file in sorted(ARTICLES_DIR.glob("*.json"), reverse=True)[:10]:
        with open(file, "r", encoding="utf-8") as f:
            article = json.load(f)
            articles.append(article)
            print(f"  [{article['id']}]")
            print(f"  제목: {article['title']}")
            print(f"  생성: {article['created_at']}")
            print()

    if not articles:
        print("  저장된 글이 없습니다.")

    return articles


def main():
    parser = argparse.ArgumentParser(description="Auto-Blog 자동화 시스템")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # 정보형 글 생성
    info_parser = subparsers.add_parser("info", help="정보형 글 생성")
    info_parser.add_argument(
        "--category",
        choices=["ai"],
        default="ai",
        help="카테고리 선택 (기본: ai)",
    )

    # 체험형 글 생성
    exp_parser = subparsers.add_parser("experience", help="체험형 글 생성")
    exp_parser.add_argument("memo", help="경험 메모 (짧은 설명)")
    exp_parser.add_argument(
        "--category",
        default="일상/리뷰",
        help="카테고리 (기본: 일상/리뷰)",
    )

    # 저장된 글 목록
    subparsers.add_parser("list", help="저장된 글 목록")

    args = parser.parse_args()

    if args.command == "info":
        generate_info_article(args.category)
    elif args.command == "experience":
        generate_experience_article(args.memo, args.category)
    elif args.command == "list":
        list_articles()
    else:
        parser.print_help()
        print("\n사용 예시:")
        print("  python main.py info    # AI 뉴스 글 생성")
        print("  python main.py list    # 저장된 글 목록")


if __name__ == "__main__":
    main()
