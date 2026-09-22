# Supabase 설정 가이드

## 1. Supabase 계정 생성 및 프로젝트 설정

1. [Supabase](https://supabase.com)에서 계정 생성
2. 새 프로젝트 생성
3. 프로젝트 설정이 완료될 때까지 대기

## 2. 데이터베이스 테이블 생성

Supabase 대시보드의 SQL Editor에서 `supabase-setup.sql` 파일의 내용을 실행합니다:

1. Supabase 대시보드 → SQL Editor 클릭
2. "New Query" 버튼 클릭
3. `supabase-setup.sql` 파일의 SQL을 복사하여 붙여넣기
4. "Run" 버튼 클릭

또는 Supabase CLI를 사용하여:
```bash
supabase db push
```

## 3. API 키 및 URL 얻기

1. Supabase 대시보드 → Settings → API 클릭
2. 다음 정보를 복사:
   - `Project URL` → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## 4. 환경변수 설정

`.env.local` 파일을 생성하고 다음을 입력:

```env
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## 5. 패키지 설치 및 실행

```bash
# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

## 6. 기존 데이터 마이그레이션 (선택사항)

기존 `data/posts.json` 파일의 데이터를 Supabase로 마이그레이션하려면:

```bash
# Node.js 스크립트로 마이그레이션 가능
# migrate.js 파일을 생성하여 처리
```

## 주요 변경사항

- **저장소**: JSON 파일 → Supabase PostgreSQL
- **API**: 로컬 파일 시스템 → Supabase REST API
- **성능**: 더 빠른 쿼리 성능 및 확장성
- **신뢰성**: 전문적인 데이터베이스 관리

## 문제 해결

### 테이블이 생성되지 않음
- SQL Editor에서 오류 메시지 확인
- 권한 설정 확인 (Anonymous access 활성화 필요)

### API 키 오류
- `.env.local` 파일에서 URL과 KEY가 정확한지 확인
- 개발 서버 재시작 필요

### 쿼리 오류
- Supabase 대시보드의 Database 탭에서 테이블 구조 확인
- 콘솔의 오류 메시지 확인
