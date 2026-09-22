-- NewsSearchCrawler용 articles 테이블 생성
CREATE TABLE IF NOT EXISTS articles (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  query VARCHAR(200) NOT NULL,
  title VARCHAR(500) NOT NULL,
  press VARCHAR(100),
  date TIMESTAMP,
  posted VARCHAR(50),
  url TEXT,
  original_url TEXT,
  snippet TEXT,
  summary TEXT,
  keywords VARCHAR(500),
  content TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_articles_query ON articles(query);
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date DESC);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at DESC);

-- updated_at 트리거
CREATE OR REPLACE FUNCTION update_articles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_articles_updated_at();
