--AI intelligently filters related table structures
-- Created in the news library, the same library as news_items

-- ============================================
--AI filter interest tag table
--Storage structured tags extracted by AI from user interest descriptions
-- Managed by version, when the prompt word changes, the old version mark is deprecated
--Support multi-interest file isolation (interests_file tag set to distinguish different files)
-- ============================================
CREATE TABLE IF NOT EXISTS ai_filter_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL, -- tag name, such as "AI/Large Model"
    description TEXT DEFAULT '', -- tag description, reference for AI classification
    priority INTEGER NOT NULL DEFAULT 9999, -- tag priority (the smaller the value, the higher the priority)
    status TEXT DEFAULT 'active',        -- active / deprecated
    deprecated_at TEXT, -- deprecated time
    version INTEGER NOT NULL, -- version number, +1 when prompt word changes
    prompt_hash TEXT NOT NULL, -- the hash of the interest description file (format: filename:md5)
    interests_file TEXT NOT NULL DEFAULT 'ai_interests.txt', -- associated interest file name
    created_at TEXT NOT NULL
);

-- ============================================
--AI filtering classification result table
-- Each news × each label = one row
-- Reference news_items.id or rss_items.id (distinguished by source_type)
-- ============================================
CREATE TABLE IF NOT EXISTS ai_filter_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER NOT NULL, -- Reference news_items.id or rss_items.id
    source_type TEXT NOT NULL DEFAULT 'hotlist',  -- hotlist / rss
    tag_id INTEGER NOT NULL, -- Reference ai_filter_tags.id
    relevance_score REAL DEFAULT 0, -- relevance 0.0 ~ 1.0
    status TEXT DEFAULT 'active',        -- active / deprecated
    deprecated_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(news_item_id, source_type, tag_id)
);

-- ============================================
-- AI filtering of analyzed news records table
-- Record all news that has been analyzed by AI (regardless of matching or not)
-- Used for deduplication to avoid wasting tokens by repeatedly sending them to AI.
-- ============================================
CREATE TABLE IF NOT EXISTS ai_filter_analyzed_news (
    news_item_id INTEGER NOT NULL, -- Reference news_items.id or rss_items.id
    source_type TEXT NOT NULL DEFAULT 'hotlist',  -- hotlist / rss
    interests_file TEXT NOT NULL DEFAULT 'ai_interests.txt', -- associated interest files
    prompt_hash TEXT NOT NULL, -- label set hash used during analysis
    matched INTEGER NOT NULL DEFAULT 0, -- whether to match: 0=no match, 1=match
    created_at TEXT NOT NULL,
    PRIMARY KEY (news_item_id, source_type, interests_file)
);

-- ============================================
-- index
-- ============================================
CREATE INDEX IF NOT EXISTS idx_ai_filter_tags_status ON ai_filter_tags(status);
CREATE INDEX IF NOT EXISTS idx_ai_filter_tags_version ON ai_filter_tags(version);
CREATE INDEX IF NOT EXISTS idx_ai_filter_tags_file ON ai_filter_tags(interests_file, status);
CREATE INDEX IF NOT EXISTS idx_ai_filter_tags_priority ON ai_filter_tags(interests_file, status, priority);
CREATE INDEX IF NOT EXISTS idx_ai_filter_results_status ON ai_filter_results(status);
CREATE INDEX IF NOT EXISTS idx_ai_filter_results_news ON ai_filter_results(news_item_id, source_type);
CREATE INDEX IF NOT EXISTS idx_ai_filter_results_tag ON ai_filter_results(tag_id);
CREATE INDEX IF NOT EXISTS idx_analyzed_news_lookup ON ai_filter_analyzed_news(source_type, interests_file);
CREATE INDEX IF NOT EXISTS idx_analyzed_news_hash ON ai_filter_analyzed_news(interests_file, prompt_hash);
