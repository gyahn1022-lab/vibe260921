# NewsSearchCrawler - Supabase 통합 가이드

## 📋 개요
NewsSearchCrawler가 수집한 뉴스 기사를 JSON/CSV/Excel 파일뿐만 아니라 **Supabase PostgreSQL 데이터베이스**에도 저장합니다.

---

## 🔧 **설치 및 설정**

### **1단계: 필요한 패키지 설치**

```bash
pip install supabase python-dotenv
```

또는 전체 설치:
```bash
pip install requests beautifulsoup4 openpyxl supabase python-dotenv
```

### **2단계: Supabase 테이블 생성**

1. **Supabase 대시보시 접속**: https://app.supabase.com
2. 프로젝트 선택
3. **SQL Editor** → **"New Query"**
4. `supabase_articles_setup.sql` 파일의 SQL을 복사해서 실행
5. RLS: **"without"** (비활성화) 상태로 **Run** 클릭

### **3단계: 환경변수 설정**

1. `.env` 파일을 프로젝트 루트에 생성
2. 다음 내용 입력:

```env
SUPABASE_URL=https://aqpafyxbdyguimgxjyvd.supabase.co
SUPABASE_KEY=sb_publishable_kQnVTo5Oy31OZicLTppKKQ_0UcAYWU7
```

### **4단계: 실행**

```bash
python news_crawler.py 반도체 -n 10
```

---

## ✅ **확인 사항**

실행 후 다음을 확인하세요:

1. **파일 저장** ✅
   - `news_result.json`
   - `news_result.csv`
   - `news_result.xlsx`

2. **Supabase 저장** ✅
   - "Supabase 저장 완료: N개 기사" 메시지 표시
   - Supabase 대시보드 → **Table Editor** → `articles` 테이블 확인

---

## 📊 **articles 테이블 구조**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGINT | 자동 증가 ID |
| query | VARCHAR | 검색어 |
| title | VARCHAR | 기사 제목 |
| press | VARCHAR | 언론사 |
| date | TIMESTAMP | 기사 작성일 |
| posted | VARCHAR | 검색 시간 |
| url | TEXT | 네이버뉴스 링크 |
| original_url | TEXT | 원문 링크 |
| snippet | TEXT | 검색 미리보기 |
| summary | TEXT | 기사 요약 |
| keywords | VARCHAR | 키워드 (쉼표로 구분) |
| content | TEXT | 기사 본문 |
| created_at | TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | 업데이트 시간 |

---

## 🚀 **사용 예시**

### **기본 사용**
```bash
python news_crawler.py 반도체
```
→ 반도체 관련 기사 10개 크롤링 & 저장

### **기사 수 지정**
```bash
python news_crawler.py AI -n 20
```
→ AI 관련 기사 20개 크롤링

### **기간 지정**
```bash
python news_crawler.py 주식 --from 2026-09-01 --to 2026-09-15
```
→ 2026-09-01부터 09-15까지 주식 관련 기사

---

## ⚠️ **문제 해결**

### "Supabase 라이브러리가 설치되지 않음"
```bash
pip install supabase python-dotenv
```

### "Supabase 저장 실패: 인증 오류"
- `.env` 파일에 올바른 `SUPABASE_URL`과 `SUPABASE_KEY`가 설정되었는지 확인
- `.env` 파일이 프로젝트 루트에 있는지 확인

### "articles 테이블을 찾을 수 없음"
- Supabase SQL Editor에서 `supabase_articles_setup.sql`을 실행했는지 확인
- Table Editor에서 `articles` 테이블이 보이는지 확인

---

## 📌 **참고**

- 파일 저장과 Supabase 저장은 동시에 진행됩니다
- Supabase 연결이 실패해도 파일로는 정상 저장됩니다
- Supabase는 클라우드 기반이므로 네트워크 연결이 필요합니다
