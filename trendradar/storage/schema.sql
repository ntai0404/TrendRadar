-- TrendRadar database table structure

-- ============================================
--Platform information table
-- Core: id remains unchanged, name is variable
-- ============================================
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- News item table
-- Use URL + platform_id as the unique identifier to support deduplication storage
-- ============================================
CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    url TEXT DEFAULT '',
    mobile_url TEXT DEFAULT '',
    first_crawl_time TEXT NOT NULL, -- first crawl time
    last_crawl_time TEXT NOT NULL, -- last crawl time
    crawl_count INTEGER DEFAULT 1, -- number of crawls
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- ============================================
-- Title change history table
--Record title changes under the same URL
-- ============================================
CREATE TABLE IF NOT EXISTS title_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER NOT NULL,
    old_title TEXT NOT NULL,
    new_title TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_item_id) REFERENCES news_items(id)
);

-- ============================================
-- Ranking history table
-- Record ranking changes for each crawl
-- ============================================
CREATE TABLE IF NOT EXISTS rank_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    crawl_time TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_item_id) REFERENCES news_items(id)
);

-- ============================================
-- Fetch record table
-- Record the time and quantity of each crawl
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_time TEXT NOT NULL UNIQUE,
    total_items INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Fetch source status table
-- Record the success/failure status of each platform crawled each time
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_source_status (
    crawl_record_id INTEGER NOT NULL,
    platform_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
    PRIMARY KEY (crawl_record_id, platform_id),
    FOREIGN KEY (crawl_record_id) REFERENCES crawl_records(id),
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- ============================================
-- Time period execution record table
-- Record the execution status of each action dimension in each time period of each day (used for once function)
-- Replace the old push_records table
-- ============================================
CREATE TABLE IF NOT EXISTS period_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_date TEXT NOT NULL,          -- YYYY-MM-DD
    period_key TEXT NOT NULL, -- the stable key of period
    action TEXT NOT NULL,                  -- analyze | push
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(execution_date, period_key, action)
);

-- ============================================
-- Index definition
-- ============================================

-- Platform index
CREATE INDEX IF NOT EXISTS idx_news_platform ON news_items(platform_id);

-- Time index (used to query the latest data)
CREATE INDEX IF NOT EXISTS idx_news_crawl_time ON news_items(last_crawl_time);

-- Title index (for title search)
CREATE INDEX IF NOT EXISTS idx_news_title ON news_items(title);

-- URL + platform_id unique index (only for non-empty URLs, deduplication is achieved)
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url_platform
    ON news_items(url, platform_id) WHERE url != '';

-- Fetch status index
CREATE INDEX IF NOT EXISTS idx_crawl_status_record ON crawl_source_status(crawl_record_id);

--Ranking history index
CREATE INDEX IF NOT EXISTS idx_rank_history_news ON rank_history(news_item_id);

-- Time period execution record index
CREATE INDEX IF NOT EXISTS idx_period_exec_lookup
ON period_executions(execution_date, period_key, action);
