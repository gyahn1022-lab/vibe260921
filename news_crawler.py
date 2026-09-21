"""네이버 검색 결과(뉴스)에서 기사 링크를 모아 제목/언론사/날짜/본문을 크롤링한다.

필요 패키지: pip install requests beautifulsoup4 openpyxl
사용법:      python news_crawler.py            (저장된 기본 검색어 사용, 초기값: 반도체)
             python news_crawler.py 검색어 -n 5
             python news_crawler.py --set-default 검색어   (기본 검색어 변경)
             python news_crawler.py 검색어 --from 2026-09-01 --to 2026-09-10
"""
import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from datetime import date, datetime
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

SEARCH_URL = (
    "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0"
    "&ie=utf8&query=%EB%B0%98%EB%8F%84%EC%B2%B4&ackey=6zjfxkkq"
)
DEFAULT_QUERY = "반도체"  # 설정 파일이 없을 때 쓰는 기본값
CONFIG_PATH = Path(os.environ.get("APPDATA") or Path.home()) / "NewsSearchCrawler" / "settings.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}
# 네이버 뉴스 기사 URL 형태: https://n.news.naver.com/mnews/article/003/0014203493
NAVER_ARTICLE = re.compile(r"https://n\.news\.naver\.com/(?:mnews/)?article/\d+/\d+")


def get_default_query():
    """사용자가 저장한 기본 검색어를 읽는다. 없으면 DEFAULT_QUERY."""
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        query = str(data.get("default_query", "")).strip()
    except (OSError, ValueError, AttributeError):
        query = ""
    return query or DEFAULT_QUERY


def set_default_query(query):
    """기본 검색어를 설정 파일에 저장한다 (GUI와 터미널 실행이 함께 사용)."""
    query = query.strip()
    if not query:
        raise ValueError("기본 검색어가 비어 있습니다.")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps({"default_query": query}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_search_url(query):
    """검색어로 통합검색 URL을 만든다 (뉴스 영역 구조가 기본 URL과 동일)."""
    return "https://search.naver.com/search.naver?" + urlencode(
        {"where": "nexearch", "ie": "utf8", "query": query}
    )


def get_soup(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    res.encoding = "utf-8"
    return BeautifulSoup(res.text, "html.parser")


def clean_text(tag):
    """<mark> 등 인라인 태그 주변 공백이 사라지지 않게 텍스트를 뽑는다."""
    return " ".join(tag.get_text().replace("새 창 열림", "").split())


def collect_search_items(search_url, limit):
    """검색 결과 목록에서 기사별 제목/언론사/시간/요약/링크를 수집한다.

    각 기사의 제목(.tit), 요약(.body), 네이버뉴스 링크(.nav)는
    data-nlog-area 속성이 다르고 data-nlog-params 안의 gdid 가 같다.
    (클래스명은 해시라 자주 바뀌므로 data-* 속성과 sds-comps-* 클래스를 사용)
    """
    soup = get_soup(search_url)
    items = {}
    for a in soup.select("a[data-nlog-area][data-nlog-params]"):
        m = re.search(r"\.(tit|body|nav)$", a["data-nlog-area"])
        if not m:
            continue
        try:
            gdid = json.loads(a["data-nlog-params"]).get("gdid")
        except ValueError:
            continue
        if not gdid:
            continue
        item = items.setdefault(gdid, {})
        kind, href = m.group(1), a["href"]
        if kind == "tit":
            item["title"] = clean_text(a)
            item["original_url"] = href
        elif kind == "body":
            item["snippet"] = clean_text(a)
        elif kind == "nav":
            nm = NAVER_ARTICLE.match(href)
            item["naver_url"] = nm.group(0) if nm else ""
            profile = a.find_parent(attrs={"data-sds-comp": "Profile"})
            if profile:
                press = profile.select_one(".sds-comps-profile-info-title-text")
                when = profile.select_one(".sds-comps-profile-info-subtext")
                item["press"] = clean_text(press) if press else ""
                item["posted"] = when.get_text(strip=True) if when else ""
    result = [i for i in items.values() if i.get("naver_url")]
    return result[:limit]


def build_news_tab_url(query, start_date=None, end_date=None):
    """뉴스 탭 검색 URL. 기간(start_date~end_date)을 주면 그 기간의 기사만 검색된다."""
    params = {"where": "news", "query": query, "sm": "tab_opt", "sort": 0,
              "photo": 0, "field": 0, "pd": 0, "nso": "so:r,p:all"}
    if start_date and end_date:
        ds, de = start_date.strftime("%Y.%m.%d"), end_date.strftime("%Y.%m.%d")
        params.update({
            "pd": 3, "ds": ds, "de": de,
            "nso": f"so:r,p:from{ds.replace('.', '')}to{de.replace('.', '')}",
        })
    return "https://search.naver.com/search.naver?" + urlencode(params)


def collect_news_tab_links(query, seen, start_date=None, end_date=None):
    """뉴스 탭 검색 결과에서 아직 없는 네이버 뉴스 링크를 모은다."""
    url = build_news_tab_url(query, start_date, end_date)
    extra = []
    for a in get_soup(url).find_all("a", href=True):
        m = NAVER_ARTICLE.match(a["href"])
        if m and m.group(0) not in seen:
            seen.add(m.group(0))
            extra.append({"naver_url": m.group(0)})
    return extra


def find_articles(query, limit, start_date=None, end_date=None):
    """검색어(와 선택적으로 기간)로 기사 목록을 찾는다.

    기간을 지정하면 뉴스 탭 검색만 사용한다(통합검색은 기간 필터가 없다).
    기간이 없으면 통합검색 결과를 먼저 쓰고, 모자라면 뉴스 탭으로 보충한다.
    """
    items = []
    if not (start_date and end_date):
        items = collect_search_items(build_search_url(query), limit)
    if len(items) < limit:
        seen = {i["naver_url"] for i in items}
        try:
            items += collect_news_tab_links(query, seen, start_date, end_date)
        except requests.RequestException:
            if not items:
                raise
    return items[:limit]


# 흔한 조사/어미: 단어 빈도를 셀 때 "반도체는"과 "반도체가"를 같은 단어로 본다
_JOSA = re.compile(r"(으로|에서|에게|까지|부터|보다|이며|이다|했다|한다|은|는|이|가|을|를|의|에|도|로|과|와|만)$")
_STOP = {"이번", "지난", "기자", "관련", "대한", "통해", "있다", "있는", "것으로", "따르면", "위해", "이후", "현재"}
_NOISE = re.compile(r"(무단\s*전재|재배포|저작권|구독|@[\w.]+|▶|☞|사진=|photo)", re.I)
_BYLINE = re.compile(r"^\s*(\[[^\]]{1,20}\]|\([^)]{1,20}\))\s*([가-힣]{2,4}\s*(특파원|기자)\s*[=:]?)?\s*")


def _tokens(text):
    words = []
    for w in re.findall(r"[가-힣]{2,}|[A-Za-z0-9]{2,}", text):
        w = _JOSA.sub("", w) if len(w) > 2 else w
        if len(w) >= 2 and w not in _STOP:
            words.append(w)
    return words


def extract_keywords(text, limit=6):
    """본문에서 자주 등장하는 핵심 단어를 뽑는다 (숫자만인 단어는 제외)."""
    freq = {}
    for w in _tokens(text):
        if re.search(r"[가-힣A-Za-z]", w):
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(
        (w for w, c in freq.items() if c >= 2),
        key=lambda w: (-freq[w], -len(w)),
    )
    return ranked[:limit]


def _shorten(sentence, limit):
    """한 줄에 들어가도록 문장을 limit 글자 안에서 단어 경계로 자른다."""
    if len(sentence) <= limit:
        return sentence
    cut = sentence[:limit]
    if " " in cut[limit // 2:]:
        cut = cut[:cut.rindex(" ")]
    return cut.rstrip(" ,.·…") + "…"


def summarize(text, max_sentences=3, max_chars=60):
    """본문에서 핵심 문장만 골라 요약한다 (외부 API 없이 동작하는 추출 요약).

    결과는 최대 max_sentences 줄이고, 한 줄은 max_chars 글자를 넘지 않는다(줄바꿈으로 구분).

    문장에 포함된 단어가 기사 전체에서 얼마나 자주 나오는지로 점수를 매기고,
    기사 앞쪽 문장에 가산점을 준 뒤, 상위 문장을 원래 순서대로 이어 붙인다.
    """
    sentences = []
    for line in text.splitlines():
        for sent in re.split(r"(?<=[.!?])\s+", line.strip()):
            sent = _BYLINE.sub("", sent).strip()
            if (25 <= len(sent) <= 220 and sent.endswith((".", "!", "?", "\"", "”", "'", "’"))
                    and not _NOISE.search(sent)):  # 마침표 없는 줄은 소제목이라 제외
                sentences.append(sent)
    if not sentences:
        return _shorten(" ".join(text.split()), max_chars)
    if len(sentences) <= max_sentences:
        return "\n".join(_shorten(x, max_chars) for x in sentences)

    freq = {}
    for w in _tokens(" ".join(sentences)):
        freq[w] = freq.get(w, 0) + 1

    scored = []
    for idx, sent in enumerate(sentences):
        words = set(_tokens(sent))
        if not words:
            continue
        score = sum(freq[w] for w in words) / (len(words) ** 0.5)
        score *= 1.0 + 0.5 / (1 + idx)  # 앞쪽 문장일수록 가산
        scored.append((score, idx))
    top = sorted(sorted(scored, reverse=True)[:max_sentences], key=lambda x: x[1])
    return "\n".join(_shorten(sentences[idx], max_chars) for _, idx in top)


def parse_article(url):
    """기사 페이지 하나에서 제목, 언론사, 작성일, 본문을 추출한다."""
    soup = get_soup(url)

    title = soup.select_one("#title_area") or soup.select_one("h2.media_end_head_headline")
    press = soup.select_one("a.media_end_head_top_logo img")
    date = soup.select_one("span.media_end_head_info_datestamp_time")
    body = soup.select_one("#dic_area") or soup.select_one("#newsct_article")
    if body is None:
        return None

    # 본문 안의 사진 설명, 광고, 스크립트 등 제거
    for tag in body.select("script, style, .img_desc, .end_photo_org, .ad_wrap, figure"):
        tag.decompose()
    text = re.sub(r"\n\s*\n+", "\n", body.get_text("\n", strip=True))

    return {
        "summary": summarize(text),
        "keywords": extract_keywords(text),
        "url": url,
        "title": title.get_text(strip=True) if title else "",
        "press": (press.get("alt") or press.get("title") or "") if press else "",
        "date": date.get("data-date-time", date.get_text(strip=True)) if date else "",
        "content": text,
    }


def crawl(query, limit=10, delay=1.0, start_date=None, end_date=None):
    articles = []
    items = find_articles(query, limit, start_date, end_date)
    print(f"검색 결과 기사 {len(items)}개 발견")
    for i, item in enumerate(items, 1):
        try:
            article = parse_article(item["naver_url"])
        except requests.RequestException as e:
            print(f"[{i}] 요청 실패: {item['naver_url']} ({e})")
            continue
        if article is None:
            print(f"[{i}] 본문을 찾지 못함: {item['naver_url']}")
            continue
        # 검색 목록의 정보로 보완 (기사 페이지에서 못 얻은 값 채우기)
        article["title"] = article["title"] or item.get("title", "")
        article["press"] = article["press"] or item.get("press", "")
        article["posted"] = item.get("posted", "")
        article["original_url"] = item.get("original_url", "")
        article["snippet"] = item.get("snippet", "")
        articles.append(article)
        print(f"[{i}] {article['title']} ({article['press']}, {article['posted']})")
        time.sleep(delay)  # 서버에 부담을 주지 않도록 간격을 둔다
    return articles


EXCEL_COLUMNS = [
    ("제목", "title", 50), ("언론사", "press", 14), ("작성일", "date", 20),
    ("검색시간", "posted", 12), ("요약", "summary", 70), ("키워드", "keywords", 30), ("네이버 링크", "url", 45),
    ("원문 링크", "original_url", 45), ("검색 미리보기", "snippet", 60), ("본문", "content", 100),
]
EXCEL_CELL_LIMIT = 32767  # 엑셀 셀 하나에 넣을 수 있는 최대 글자 수


def cell_text(value):
    """표/CSV 셀에 넣을 문자열 (리스트는 쉼표로 이어 붙인다)."""
    return ", ".join(value) if isinstance(value, list) else str(value)


def save_excel(articles, path="news_result.xlsx"):
    """수집한 기사를 서식이 적용된 엑셀 파일(.xlsx)로 저장한다."""
    wb = Workbook()
    ws = wb.active
    ws.title = "뉴스"
    ws.append([name for name, _, _ in EXCEL_COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="3B63E0")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for art in articles:
        ws.append([cell_text(art.get(key, ""))[:EXCEL_CELL_LIMIT] for _, key, _ in EXCEL_COLUMNS])
    for idx, (_, _, width) in enumerate(EXCEL_COLUMNS, 1):
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row[0].row].height = 60  # 본문이 길어도 행 높이를 일정하게
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(path)


def save(articles, base="news_result"):
    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    with open(f"{base}.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "press", "date", "posted", "url", "original_url", "snippet", "summary", "keywords", "content"])
        writer.writeheader()
        writer.writerows({k: cell_text(v) for k, v in a.items()} for a in articles)
    save_excel(articles, f"{base}.xlsx")
    print(f"저장 완료: {base}.json, {base}.csv, {base}.xlsx")


def main():
    parser = argparse.ArgumentParser(description="네이버 뉴스 크롤러")
    parser.add_argument("query", nargs="?", help="검색어 (생략하면 저장된 기본 검색어)")
    parser.add_argument("--set-default", metavar="검색어", help="기본 검색어를 저장하고 종료")
    parser.add_argument("-n", "--limit", type=int, default=10, help="수집할 기사 수")
    parser.add_argument("--from", dest="date_from", help="검색 시작일 (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", help="검색 종료일 (YYYY-MM-DD, 생략하면 오늘)")
    args = parser.parse_args()

    if args.set_default:
        set_default_query(args.set_default)
        print(f"기본 검색어를 '{args.set_default.strip()}'(으)로 저장했습니다: {CONFIG_PATH}")
        return
    query = args.query or get_default_query()

    start = end = None
    if args.date_from:
        start = datetime.strptime(args.date_from, "%Y-%m-%d").date()
        end = datetime.strptime(args.date_to, "%Y-%m-%d").date() if args.date_to else date.today()
    articles = crawl(query, args.limit, start_date=start, end_date=end)
    if not articles:
        print("수집된 기사가 없습니다.")
        return
    save(articles)
    print("\n--- 첫 번째 기사 미리보기 ---")
    first = articles[0]
    print(first["title"])
    print(first["content"][:300], "...")


if __name__ == "__main__":
    main()
