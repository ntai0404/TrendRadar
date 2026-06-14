-- TrendRadar RSS database table structure
-- Used to store RSS/Atom feed data

-- ============================================
-- RSS feed configuration table
--Storing basic information about feeds
-- ============================================
CREATE TABLE IF NOT EXISTS rss_feeds (
    id TEXT PRIMARY KEY, -- source ID (such as "hacker-news")
    name TEXT NOT NULL, -- display name (e.g. "Hacker News")
    feed_url TEXT DEFAULT '', -- RSS/Atom URL (optional, already in the configuration file)
    is_active INTEGER DEFAULT 1, -- whether to enable
    last_fetch_time TEXT, -- last fetch time
    last_fetch_status TEXT, -- the last fetch status (success/failed)
    item_count INTEGER DEFAULT 0, -- number of items on the day
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- RSS entry table
-- Use URL + feed_id as the unique identifier to support deduplication storage
-- ============================================
CREATE TABLE IF NOT EXISTS rss_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, -- title
    feed_id TEXT NOT NULL, -- RSS feed to which it belongs
    url TEXT NOT NULL, -- article link
    guid TEXT DEFAULT '', -- GUID/ID (RSS guid or Atom id)
    published_at TEXT, -- RSS publishing time (ISO format)
    summary TEXT, -- summary/description
    author TEXT, -- author
    first_crawl_time TEXT NOT NULL, -- first crawl time
    last_crawl_time TEXT NOT NULL, -- last crawl time
    crawl_count INTEGER DEFAULT 1, -- number of crawls
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id)
);

-- ============================================
-- Fetch record table
-- Record the time and quantity of each crawl
-- ============================================
CREATE TABLE IF NOT EXISTS rss_crawl_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_time TEXT NOT NULL UNIQUE, -- crawl time (HH:MM)
    total_items INTEGER DEFAULT 0, -- total number of items
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Fetch source status table
-- Record the success/failure status of each RSS source fetched
-- ============================================
CREATE TABLE IF NOT EXISTS rss_crawl_status (
    crawl_record_id INTEGER NOT NULL,
    feed_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
    error_message TEXT, -- error message on failure
    PRIMARY KEY (crawl_record_id, feed_id),
    FOREIGN KEY (crawl_record_id) REFERENCES rss_crawl_records(id),
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id)
);

-- ============================================
-- Push record table
-- for push_window once_per_day function
-- and the ai_analysis analysis_window once_per_day function
-- ============================================
CREATE TABLE IF NOT EXISTS rss_push_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE, -- date (YYYY-MM-DD)
    pushed INTEGER DEFAULT 0, -- whether it has been pushed
    push_time TEXT, -- push time
    ai_analyzed INTEGER DEFAULT 0, -- Whether AI analysis has been performed
    ai_analysis_time TEXT, -- AI analysis time
    ai_analysis_mode TEXT, -- AI analysis mode
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Index definition
-- ============================================

-- RSS feed index
CREATE INDEX IF NOT EXISTS idx_rss_feed ON rss_items(feed_id);

-- Release time index (for sorting by time)
CREATE INDEX IF NOT EXISTS idx_rss_published ON rss_items(published_at DESC);

-- Fetch time index (used to query the latest data)
CREATE INDEX IF NOT EXISTS idx_rss_crawl_time ON rss_items(last_crawl_time);

-- Title index (for title search)
CREATE INDEX IF NOT EXISTS idx_rss_title ON rss_items(title);

-- URL + feed_id unique index (to achieve deduplication)
CREATE UNIQUE INDEX IF NOT EXISTS idx_rss_url_feed
    ON rss_items(url, feed_id);

-- GUID + feed_id partial unique index (guid is used first to remove duplicates when guid is not empty)
CREATE UNIQUE INDEX IF NOT EXISTS idx_rss_guid_feed
    ON rss_items(guid, feed_id) WHERE guid != '';

-- Fetch status index
CREATE INDEX IF NOT EXISTS idx_rss_crawl_status_record ON rss_crawl_status(crawl_record_id);
