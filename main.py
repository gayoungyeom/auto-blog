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


def generate_info_article(category: str = None, use_cache: bool = True) -> dict:
    """정보형 글 생성 파이프라인 (통합 방식 - 1회 API 호출)

    뉴스 흐름 분석 + 주제 선정 + 글 생성을 1회 API 호출로 처리
    """
    print("=" * 50)
    print("정보형 글 생성 시작 (통합 방식)")
    print("=" * 50)

    # 1. 뉴스 제목 수집
    print("\n[1/3] 뉴스 제목 수집 중...")
    collector = NewsCollector()
    news_data = collector.collect_news_titles(category)

    if not news_data.get("titles"):
        print("뉴스 수집 실패: 기사를 찾을 수 없습니다.")
        return None

    print(f"  - 카테고리: {news_data['category_name']}")
    print(f"  - 수집된 기사 수: {len(news_data['titles'])}개")

    # 2. 통합 글 생성 (1회 API 호출)
    print("\n[2/3] AI 글 생성 중...")
    generator = ContentGenerator()
    article = generator.generate_unified_article(news_data, use_cache=use_cache)
    print(f"  - 제목: {article['title']}")
    print(f"  - 태그: {', '.join(article['tags'])}")

    # 3. 글 저장 + 이메일 발송
    print("\n[3/3] 글 저장 및 이메일 발송 중...")
    article_id = save_article(article)
    print(f"  - ID: {article_id}")

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

    # 정보형 글 생성 (통합 방식 - 1회 API 호출)
    info_parser = subparsers.add_parser("info", help="정보형 글 생성 (1회 API 호출)")
    info_parser.add_argument(
        "--category",
        choices=["ai", "health", "economy", "lifestyle"],
        default=None,
        help="카테고리 선택 (미지정 시 가중치 기반 랜덤)",
    )
    info_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="캐시 사용 안 함 (새로 생성)",
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
        generate_info_article(args.category, use_cache=not args.no_cache)
    elif args.command == "experience":
        generate_experience_article(args.memo, args.category)
    elif args.command == "list":
        list_articles()
    else:
        parser.print_help()
        print("\n사용 예시:")
        print("  python main.py info             # 정보형 글 생성 (1회 API 호출)")
        print("  python main.py info --no-cache  # 캐시 무시하고 새로 생성")
        print("  python main.py experience '메모'    # 체험형 글 생성")
        print("  python main.py list                 # 저장된 글 목록")


if __name__ == "__main__":
    main()
