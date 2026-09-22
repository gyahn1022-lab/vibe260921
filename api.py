"""FastAPI Web서버로 NewsSearchCrawler를 노출합니다."""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import news_crawler

app = FastAPI(
    title="NewsSearchCrawler API",
    description="네이버 뉴스 크롤러 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API 정보"""
    return {
        "title": "NewsSearchCrawler API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "GET /api/crawl": "뉴스 크롤링",
        }
    }


@app.get("/api/crawl")
async def crawl(
    query: str = Query(..., description="검색어"),
    limit: int = Query(10, ge=1, le=50, description="수집할 기사 수"),
):
    """
    뉴스를 크롤링하고 Supabase에 저장합니다.

    - **query**: 검색어 (예: 반도체)
    - **limit**: 수집할 기사 수 (1-50, 기본값: 10)

    반환: 크롤링된 기사 목록
    """
    try:
        articles = news_crawler.crawl(query, limit)

        # Supabase에 저장
        if news_crawler.SUPABASE_CLIENT:
            news_crawler.save_to_supabase(articles, query)
            source = "Supabase + 파일"
        else:
            source = "파일 저장 (Supabase 미설정)"

        return {
            "status": "success",
            "query": query,
            "count": len(articles),
            "source": source,
            "articles": articles,
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e),
        }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
