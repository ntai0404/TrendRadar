# TrendRadar Architecture Diagrams

This document contains ASCII art diagrams for visualizing the TrendRadar system architecture, data flows, and component interactions.

## Table of Contents

1. [High-Level Ecosystem Diagram](#high-level-ecosystem-diagram)
2. [Hot List Data Flow](#hot-list-data-flow)
3. [RSS Feed Data Flow](#rss-feed-data-flow)
4. [LLM Crawler Bot Data Flow](#llm-crawler-bot-data-flow)
5. [Storage Architecture](#storage-architecture)
6. [Notification Flow](#notification-flow)
7. [AI Mechanisms Architecture](#ai-mechanisms-architecture)
8. [Deployment Architecture](#deployment-architecture)

---

## High-Level Ecosystem Diagram

This diagram shows the three major modules of TrendRadar and their relationships:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TrendRadar Ecosystem                                 │
│                                                                               │
│  ┌───────────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│  │  TrendRadar Core      │  │  LLM Crawler     │  │  MCP Server        │   │
│  │  System               │  │  Bot Module      │  │  (FastMCP 2.0)     │   │
│  │                       │  │                  │  │                    │   │
│  │  ┌─────────────────┐ │  │  ┌────────────┐ │  │  ┌──────────────┐  │   │
│  │  │ Crawler Module  │ │  │  │ AI Agent   │ │  │  │ Query Tools  │  │   │
│  │  │ - Hot Lists     │ │  │  │ - Planning │ │  │  │ - 27 Tools   │  │   │
│  │  │ - RSS Feeds     │ │  │  │ - Selector │ │  │  │ - 8 Categories│ │   │
│  │  └─────────────────┘ │  │  │   Inference│ │  │  └──────────────┘  │   │
│  │                       │  │  └────────────┘ │  │                    │   │
│  │  ┌─────────────────┐ │  │                  │  │  ┌──────────────┐  │   │
│  │  │ Filter Module   │ │  │  ┌────────────┐ │  │  │ Analytics    │  │   │
│  │  │ - Keywords      │ │  │  │ Browser    │ │  │  │ - Trends     │  │   │
│  │  │ - AI Filter     │ │  │  │ Automation │ │  │  │ - Sentiment  │  │   │
│  │  └─────────────────┘ │  │  │ (Playwright)│ │  │  └──────────────┘  │   │
│  │                       │  │  └────────────┘ │  │                    │   │
│  │  ┌─────────────────┐ │  │                  │  │  ┌──────────────┐  │   │
│  │  │ AI Analysis     │ │  │  ┌────────────┐ │  │  │ Notification │  │   │
│  │  │ - Summarization │ │  │  │ Content    │ │  │  │ Tools        │  │   │
│  │  │ - Translation   │ │  │  │ Extraction │ │  │  └──────────────┘  │   │
│  │  └─────────────────┘ │  │  └────────────┘ │  │                    │   │
│  │                       │  │                  │  │  ┌──────────────┐  │   │
│  │  ┌─────────────────┐ │  │  Output:         │  │  │ Transport    │  │   │
│  │  │ Notification    │ │  │  - metadata.json │  │  │ - stdio      │  │   │
│  │  │ - 9 Channels    │ │  │  - article.txt   │  │  │ - HTTP:3333  │  │   │
│  │  └─────────────────┘ │  │  - screenshot.png│  │  └──────────────┘  │   │
│  └───────────┬───────────┘  └──────┬───────────┘  └──────────┬─────────┘   │
│              │                     │                           │             │
│              │  Invokes for       │                           │             │
│              │  complex crawling  │                           │             │
│              └────────────────────►│                           │             │
│                                    │                           │             │
│              ┌─────────────────────┴───────────────────────────┘             │
│              │                                                                │
│              ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │                      Unified Storage Layer                         │      │
│  │                                                                     │      │
│  │  ┌──────────────────────┐         ┌──────────────────────┐        │      │
│  │  │  Local SQLite        │         │  Remote S3-Compatible│        │      │
│  │  │  - hotlist/*.db      │◄───────►│  - Cloudflare R2     │        │      │
│  │  │  - rss/*.db          │  Sync   │  - AWS S3            │        │      │
│  │  │  - Date-based org    │         │  - MinIO, etc.       │        │      │
│  │  └──────────────────────┘         └──────────────────────┘        │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Hot List Data Flow

This diagram illustrates how news data flows from hot list platforms through the system:

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Hot List Platforms (11 Sources)                  │
│  Zhihu │ Weibo │ Bilibili │ Baidu │ Douyin │ 36Kr │ V2EX │ ...       │
└────────┬─────────────────────────────────────────────────────────────┘
         │
         │ HTTP GET Requests
         │ (Platform-specific APIs/Scraping)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Crawler Module                                  │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Platform Adapters                                            │     │
│  │  - Parse platform-specific JSON/HTML                          │     │
│  │  - Extract: title, url, hot_value, position                  │     │
│  │  - Normalize to unified schema                                │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Deduplication                                                │     │
│  │  - URL-based deduplication                                    │     │
│  │  - Remove exact duplicates within same crawl                  │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Raw News Items
         │ [{title, url, platform, hot_value, position, ...}]
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Filter Module                                   │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Keyword-Based Filtering                                      │     │
│  │  - Load frequency_words.txt                                   │     │
│  │  - Match keywords (regex support)                             │     │
│  │  - Apply global exclusion filters                             │     │
│  │  - Group by keyword                                           │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  AI-Powered Filtering (Optional)                              │     │
│  │  - Extract tags from ai_interests.txt                         │     │
│  │  - Score news items against interest tags                     │     │
│  │  - Filter by relevance threshold                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Enrichment                                                    │     │
│  │  - Calculate weight (position + hot_value)                    │     │
│  │  - Add ranking metadata                                       │     │
│  │  - Add crawl timestamp                                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Filtered & Enriched Items
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Storage Manager                                    │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Local SQLite Storage                                         │     │
│  │  - Save to output/hotlist/YYYY-MM-DD.db                       │     │
│  │  - Create news table with schema                              │     │
│  │  - Insert/update records                                      │     │
│  │  - Create indexes for fast queries                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Remote S3 Sync (Optional)                                    │     │
│  │  - Upload database to S3-compatible storage                   │     │
│  │  - Maintain date-based organization                           │     │
│  │  - Enable multi-instance access                               │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────┬─────────────────────────────┐
         │                                 │                             │
         ▼                                 ▼                             ▼
┌────────────────────┐         ┌──────────────────────┐    ┌────────────────────┐
│ Notification       │         │ MCP Server           │    │ HTML Report        │
│ Module             │         │ Query Tools          │    │ Generator          │
│                    │         │                      │    │                    │
│ - Generate reports │         │ - get_latest_news    │    │ - GitHub Pages     │
│ - Format per       │         │ - get_news_by_date   │    │ - Static HTML      │
│   channel          │         │ - search_news        │    │ - Timeline view    │
│ - Push to 9        │         │ - analyze_trends     │    │                    │
│   channels         │         │                      │    │                    │
└────────────────────┘         └──────────────────────┘    └────────────────────┘
```


## RSS Feed Data Flow

This diagram shows how RSS/Atom feeds are processed:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RSS/Atom Feed Sources                              │
│  (Configurable feeds from config/config.yaml)                         │
│  Tech Blogs │ News Sites │ Podcasts │ YouTube Channels │ ...         │
└────────┬─────────────────────────────────────────────────────────────┘
         │
         │ HTTP GET Requests
         │ (RSS/Atom XML)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         RSS Parser Module                               │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  XML Parsing                                                  │     │
│  │  - Parse RSS 2.0 / Atom 1.0 formats                          │     │
│  │  - Extract: title, link, description, pubDate, guid          │     │
│  │  - Handle malformed XML gracefully                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  GUID-Based Deduplication                                     │     │
│  │  - Priority: guid > url                                       │     │
│  │  - Track seen GUIDs per feed                                  │     │
│  │  - Remove duplicates within same feed                         │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Parsed RSS Items
         │ [{title, url, guid, summary, published_at, feed_id, ...}]
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Filter Module                                   │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Freshness Filtering                                          │     │
│  │  - Check published_at timestamp                               │     │
│  │  - Filter by max_age_days (configurable)                      │     │
│  │  - Keep only recent items                                     │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Keyword-Based Filtering                                      │     │
│  │  - Match against frequency_words.txt                          │     │
│  │  - Group by keyword (similar to hot list)                     │     │
│  │  - Apply per-keyword display limits                           │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Sorting                                                       │     │
│  │  - Sort by published_at (newest first)                        │     │
│  │  - Maintain chronological order within keywords               │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Filtered RSS Items
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Storage Manager                                    │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Separate RSS Tables                                          │     │
│  │  - Save to output/rss/YYYY-MM-DD.db                           │     │
│  │  - Create rss_items table (separate from hot list)            │     │
│  │  - Store guid, feed_id, published_at                          │     │
│  │  - UNIQUE constraint on (date, feed_id, guid)                 │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Remote S3 Sync (Optional)                                    │     │
│  │  - Upload RSS database to S3                                  │     │
│  │  - Separate path from hot list data                           │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────┬─────────────────────────────┐
         │                                 │                             │
         ▼                                 ▼                             ▼
┌────────────────────┐         ┌──────────────────────┐    ┌────────────────────┐
│ Notification       │         │ MCP Server           │    │ HTML Report        │
│ Module             │         │ RSS Query Tools      │    │ (RSS Section)      │
│                    │         │                      │    │                    │
│ - RSS section in   │         │ - get_latest_rss     │    │ - Separate RSS     │
│   reports          │         │ - search_rss         │    │   section          │
│ - Grouped by       │         │ - get_rss_feeds_     │    │ - Grouped by feed  │
│   keyword          │         │   status             │    │                    │
└────────────────────┘         └──────────────────────┘    └────────────────────┘
```


## LLM Crawler Bot Data Flow

This diagram shows the autonomous crawler bot's operation:

```
┌──────────────────────────────────────────────────────────────────────┐
│                      User Request / Core System Invocation            │
│  Input: URL, optional username/password, crawl instructions           │
└────────┬─────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         AI Planning Agent                               │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Login Flow Planning (if credentials provided)                │     │
│  │  - Analyze page HTML                                          │     │
│  │  - Detect login requirements                                  │     │
│  │  - Infer login URL and form selectors                         │     │
│  │  - Plan pre-click actions                                     │     │
│  │  - Define success indicators                                  │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Crawl Strategy Planning                                      │     │
│  │  - Decompose complex instructions into sub-goals              │     │
│  │  - Determine search vs. direct extraction approach            │     │
│  │  - Plan navigation sequence                                   │     │
│  │  - Identify target content types                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Execution Plan
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Browser Automation (Playwright)                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Browser Launch                                               │     │
│  │  - Bundled Chromium / System Chrome / CDP mode               │     │
│  │  - Headless or headed mode                                    │     │
│  │  - Configure viewport, user agent                             │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Authentication (if required)                                 │     │
│  │  - Navigate to login page                                     │     │
│  │  - Fill username/password fields                              │     │
│  │  - Execute pre-click actions                                  │     │
│  │  - Submit login form                                          │     │
│  │  - Verify success indicators                                  │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Page Navigation                                               │     │
│  │  - Navigate to target URL                                     │     │
│  │  - Wait for page load                                         │     │
│  │  - Handle dynamic content                                     │     │
│  │  - Execute search if needed                                   │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Page HTML + Screenshot
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         AI Extraction Agent                             │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Selector Inference                                           │     │
│  │  - Analyze HTML structure                                     │     │
│  │  - Identify content containers                                │     │
│  │  - Generate CSS/XPath selectors                               │     │
│  │  - Adapt to platform-specific patterns                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Content Extraction                                           │     │
│  │  - Extract article metadata (title, author, date, category)  │     │
│  │  - Extract main content text                                  │     │
│  │  - Clean and structure content                                │     │
│  │  - Generate summary and tags                                  │     │
│  │  - Detect language and sentiment                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Extracted Data
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Output Generator                                │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  metadata.json                                                │     │
│  │  {                                                            │     │
│  │    "title": "...",                                            │     │
│  │    "author": "...",                                           │     │
│  │    "published_date": "...",                                   │     │
│  │    "category": "...",                                         │     │
│  │    "tags": [...],                                             │     │
│  │    "summary": "...",                                          │     │
│  │    "language": "...",                                         │     │
│  │    "sentiment": "..."                                         │     │
│  │  }                                                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  article.txt                                                  │     │
│  │  - Clean article content                                      │     │
│  │  - Structured text format                                     │     │
│  │  - Markdown formatting                                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  screenshot.png                                               │     │
│  │  - Full-page screenshot                                       │     │
│  │  - Visual verification                                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  page.html                                                    │     │
│  │  - Raw HTML preservation                                      │     │
│  │  - Debugging and analysis                                     │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ Output Files
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    TrendRadar Core System Integration                   │
│  - Consume metadata.json for structured data                           │
│  - Use article.txt for content analysis                                │
│  - Store in unified storage layer                                      │
│  - Apply filtering and enrichment                                      │
│  - Push to notification channels                                       │
└─────────────────────────────────────────────────────────────────────────┘
```


## Storage Architecture

This diagram shows the unified storage layer with local and remote backends:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Storage Manager (Unified Interface)                  │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Storage Abstraction Layer                                         │     │
│  │  - Unified API for read/write operations                           │     │
│  │  - Automatic backend selection (local/remote)                      │     │
│  │  - Transparent sync between backends                               │     │
│  │  - Connection pooling and caching                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  ┌─────────────────────────────┐      ┌──────────────────────────────┐     │
│  │  Local SQLite Backend       │      │  Remote S3-Compatible        │     │
│  │                             │      │  Backend                     │     │
│  │  ┌───────────────────────┐ │      │  ┌────────────────────────┐ │     │
│  │  │ Hot List Databases    │ │      │  │ Cloudflare R2          │ │     │
│  │  │                       │ │      │  │ - Global CDN           │ │     │
│  │  │ output/hotlist/       │ │      │  │ - Zero egress fees     │ │     │
│  │  │   2024-01-15.db       │ │◄────►│  │ - S3 API compatible    │ │     │
│  │  │   2024-01-16.db       │ │ Sync │  └────────────────────────┘ │     │
│  │  │   2024-01-17.db       │ │      │                              │     │
│  │  │   ...                 │ │      │  ┌────────────────────────┐ │     │
│  │  └───────────────────────┘ │      │  │ AWS S3                 │ │     │
│  │                             │      │  │ - Scalable storage     │ │     │
│  │  ┌───────────────────────┐ │      │  │ - Versioning support   │ │     │
│  │  │ RSS Databases         │ │      │  │ - Lifecycle policies   │ │     │
│  │  │                       │ │      │  └────────────────────────┘ │     │
│  │  │ output/rss/           │ │      │                              │     │
│  │  │   2024-01-15.db       │ │◄────►│  ┌────────────────────────┐ │     │
│  │  │   2024-01-16.db       │ │ Sync │  │ MinIO / Self-hosted    │ │     │
│  │  │   2024-01-17.db       │ │      │  │ - On-premise option    │ │     │
│  │  │   ...                 │ │      │  │ - Full control         │ │     │
│  │  └───────────────────────┘ │      │  │ - S3 API compatible    │ │     │
│  │                             │      │  └────────────────────────┘ │     │
│  │  Features:                  │      │                              │     │
│  │  - Fast read/write          │      │  Features:                   │     │
│  │  - No network latency       │      │  - Persistent storage        │     │
│  │  - No configuration needed  │      │  - Multi-instance access     │     │
│  │  - Date-based organization  │      │  - Automatic backups         │     │
│  │  - Automatic cleanup        │      │  - Geographic distribution   │     │
│  │  - Full-text search indexes │      │  - Disaster recovery         │     │
│  └─────────────────────────────┘      └──────────────────────────────┘     │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Database Schema (SQLite)                                          │     │
│  │                                                                     │     │
│  │  Hot List Tables:                                                  │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │ news                                                         │  │     │
│  │  │ - id (INTEGER PRIMARY KEY)                                  │  │     │
│  │  │ - date (TEXT NOT NULL)                                      │  │     │
│  │  │ - platform (TEXT NOT NULL)                                  │  │     │
│  │  │ - title (TEXT NOT NULL)                                     │  │     │
│  │  │ - url (TEXT)                                                │  │     │
│  │  │ - position (INTEGER)                                        │  │     │
│  │  │ - hot_value (INTEGER)                                       │  │     │
│  │  │ - weight (REAL)                                             │  │     │
│  │  │ - crawl_time (TEXT)                                         │  │     │
│  │  │ - UNIQUE(date, platform, url)                               │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  │                                                                     │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │ push_records                                                │  │     │
│  │  │ - id (INTEGER PRIMARY KEY)                                  │  │     │
│  │  │ - date (TEXT NOT NULL)                                      │  │     │
│  │  │ - title (TEXT NOT NULL)                                     │  │     │
│  │  │ - platform (TEXT)                                           │  │     │
│  │  │ - push_time (TEXT)                                          │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  │                                                                     │     │
│  │  RSS Tables:                                                       │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │ rss_items                                                   │  │     │
│  │  │ - id (INTEGER PRIMARY KEY)                                  │  │     │
│  │  │ - date (TEXT NOT NULL)                                      │  │     │
│  │  │ - feed_id (TEXT NOT NULL)                                   │  │     │
│  │  │ - guid (TEXT)                                               │  │     │
│  │  │ - title (TEXT NOT NULL)                                     │  │     │
│  │  │ - url (TEXT NOT NULL)                                       │  │     │
│  │  │ - summary (TEXT)                                            │  │     │
│  │  │ - published_at (TEXT)                                       │  │     │
│  │  │ - crawl_time (TEXT)                                         │  │     │
│  │  │ - UNIQUE(date, feed_id, guid)                               │  │     │
│  │  │ - UNIQUE(date, feed_id, url)                                │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Data Organization                                                 │     │
│  │                                                                     │     │
│  │  output/                                                           │     │
│  │  ├── hotlist/                                                      │     │
│  │  │   ├── 2024-01-15.db                                             │     │
│  │  │   ├── 2024-01-16.db                                             │     │
│  │  │   └── 2024-01-17.db                                             │     │
│  │  ├── rss/                                                          │     │
│  │  │   ├── 2024-01-15.db                                             │     │
│  │  │   ├── 2024-01-16.db                                             │     │
│  │  │   └── 2024-01-17.db                                             │     │
│  │  └── reports/                                                      │     │
│  │      ├── 2024-01-15.html                                           │     │
│  │      ├── 2024-01-16.html                                           │     │
│  │      └── 2024-01-17.html                                           │     │
│  │                                                                     │     │
│  │  Retention Policy:                                                 │     │
│  │  - Configurable retention period (default: 30 days)                │     │
│  │  - Automatic cleanup of old databases                              │     │
│  │  - Remote storage can have different retention                     │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Notification Flow

This diagram illustrates how news data flows from storage to various notification channels:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SQLite Database (Storage Layer)                      │
│  ┌────────────────────────────┐    ┌────────────────────────────┐          │
│  │ Hot List Data              │    │ RSS Feed Data              │          │
│  │ - Filtered news items      │    │ - RSS items                │          │
│  │ - Grouped by keyword       │    │ - Grouped by keyword       │          │
│  │ - Ranked by weight         │    │ - Sorted by published_at   │          │
│  └────────────┬───────────────┘    └────────────┬───────────────┘          │
└───────────────┼──────────────────────────────────┼──────────────────────────┘
                │                                  │
                │ Query by Date/Platform/Keyword   │
                └──────────────┬───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Report Generator                                     │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Data Aggregation                                                  │     │
│  │  - Fetch news items for current time period                        │     │
│  │  - Group by keyword categories                                     │     │
│  │  - Apply display limits per keyword                                │     │
│  │  - Sort by weight/ranking                                          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Format Generation                                                 │     │
│  │  - Generate Markdown format (base format)                          │     │
│  │  - Generate HTML format (for email/web)                            │     │
│  │  - Generate plain text format (for simple channels)                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└────────┬────────────────────────────────────────────────────────────────────┘
         │
         ├──────────────────────┬──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ AI Analysis        │  │ Translation      │  │ Format Adapter   │
│ (Optional)         │  │ (Optional)       │  │                  │
│                    │  │                  │  │ Per-channel      │
│ ┌────────────────┐ │  │ ┌──────────────┐ │  │ adaptation       │
│ │ Sentiment      │ │  │ │ Batch        │ │  │                  │
│ │ Analysis       │ │  │ │ Translation  │ │  │ - Markdown       │
│ └────────────────┘ │  │ └──────────────┘ │  │ - HTML           │
│ ┌────────────────┐ │  │ ┌──────────────┐ │  │ - Plain Text     │
│ │ Trend          │ │  │ │ Bilingual    │ │  │ - JSON           │
│ │ Summarization  │ │  │ │ Output       │ │  │                  │
│ └────────────────┘ │  │ └──────────────┘ │  │ Size limits:     │
│ ┌────────────────┐ │  │                  │  │ - Feishu: 30KB   │
│ │ Key Insights   │ │  │                  │  │ - DingTalk: 20KB │
│ └────────────────┘ │  │                  │  │ - Telegram: 4KB  │
└────────┬───────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                       │                      │
         └───────────────────────┴──────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Notification Dispatcher                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Channel Router                                                    │     │
│  │  - Select enabled channels from config                             │     │
│  │  - Apply channel-specific formatting                               │     │
│  │  - Handle multi-account configurations                             │     │
│  │  - Implement batch sending for size limits                         │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└────────┬────────────────────────────────────────────────────────────────────┘
         │
         ├──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
         │      │      │      │      │      │      │      │      │
         ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│ Feishu   │ │Ding│ │WeWk│ │Tele│ │Mail│ │ntfy│ │Bark│ │Slck│ │Hook│
│          │ │Talk│ │    │ │gram│ │    │ │    │ │    │ │    │ │    │
│ ┌──────┐ │ │    │ │    │ │    │ │    │ │    │ │    │ │    │ │    │
│ │Webhook│ │ │Web │ │Web │ │Bot │ │SMTP│ │HTTP│ │HTTP│ │Web │ │HTTP│
│ │  URL  │ │ │hook│ │hook│ │API │ │    │ │POST│ │POST│ │hook│ │POST│
│ └──────┘ │ │    │ │    │ │    │ │    │ │    │ │    │ │    │ │    │
│          │ │    │ │    │ │    │ │    │ │    │ │    │ │    │ │    │
│ Features:│ │Feat│ │Feat│ │Feat│ │Feat│ │Feat│ │Feat│ │Feat│ │Feat│
│ - Rich   │ │Rich│ │Rich│ │Msg │ │HTML│ │Push│ │Push│ │Rich│ │Cust│
│   cards  │ │text│ │text│ │fmt │ │fmt │ │ntfy│ │iOS │ │fmt │ │JSON│
│ - @      │ │@   │ │@   │ │Btn │ │Att │ │    │ │    │ │Thrd│ │    │
│   mention│ │    │ │    │ │Inln│ │Embd│ │    │ │    │ │    │ │    │
│ - Buttons│ │    │ │    │ │kbd │ │img │ │    │ │    │ │    │ │    │
│ - Multi  │ │Mult│ │Mult│ │    │ │    │ │    │ │    │ │    │ │    │
│   account│ │acct│ │acct│ │    │ │    │ │    │ │    │ │    │ │    │
└──────────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Additional Output Channels                           │
│                                                                               │
│  ┌────────────────────────────┐         ┌────────────────────────────┐     │
│  │  HTML Report Generation    │         │  GitHub Pages Deployment   │     │
│  │                            │         │                            │     │
│  │  - Static HTML file        │────────►│  - Automatic deployment    │     │
│  │  - Timeline view           │         │  - Public web access       │     │
│  │  - Responsive design       │         │  - Historical archive      │     │
│  │  - Search functionality    │         │  - RSS feed generation     │     │
│  │  - Category filtering      │         │                            │     │
│  │                            │         │  URL: username.github.io/  │     │
│  │  Saved to:                 │         │       TrendRadar           │     │
│  │  output/reports/           │         │                            │     │
│  │    YYYY-MM-DD.html         │         │                            │     │
│  └────────────────────────────┘         └────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Batch Sending Strategy                               │
│                                                                               │
│  When message size exceeds channel limits:                                   │
│                                                                               │
│  1. Calculate message size                                                   │
│  2. If size > limit:                                                         │
│     a. Split content by keyword groups                                       │
│     b. Send multiple messages sequentially                                   │
│     c. Add "Part X/Y" indicators                                             │
│     d. Maintain context between parts                                        │
│  3. Track sent items to avoid duplicates                                     │
│  4. Log delivery status per channel                                          │
│                                                                               │
│  Example for Feishu (30KB limit):                                            │
│  - Message 1: Keywords 1-5 (28KB)                                            │
│  - Message 2: Keywords 6-10 (27KB)                                           │
│  - Message 3: Keywords 11-12 (15KB)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```


## AI Mechanisms Architecture

This diagram shows all AI-powered components and their interactions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI Provider Layer (LiteLLM)                          │
│                                                                               │
│  Supports 100+ AI providers through unified interface:                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ DeepSeek │ │ OpenAI   │ │ Google   │ │Anthropic │ │ 9Router  │         │
│  │          │ │ GPT-4    │ │ Gemini   │ │ Claude   │ │ (Multi)  │         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │
│       └────────────┴────────────┴────────────┴────────────┘                 │
│                                 │                                             │
└─────────────────────────────────┼─────────────────────────────────────────────┘
                                  │
                                  │ Unified API
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI Mechanism Orchestrator                            │
│                                                                               │
│  Configuration:                                                               │
│  - config/config.yaml → ai.model, ai.api_key, ai.base_url                   │
│  - Prompt templates in config/ directory                                     │
│  - Token optimization settings                                               │
│  - Fallback model configuration                                              │
└────────┬────────────────────────────────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┬──────────────┐
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
┌────────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ Smart Filter   │ │ Analysis & │ │Translation │ │ Crawler Bot│ │ MCP Server │
│                │ │Summarizatn │ │            │ │ AI         │ │ AI         │
└────────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. AI-Powered Smart Filtering                        │
│                                                                               │
│  Input: ai_interests.txt                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ "I want to follow AI developments, especially LLMs and AGI.        │     │
│  │  Also interested in renewable energy and climate tech."            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Tag Extraction (AI)                                                │     │
│  │ Prompt: config/ai_filter/extract_prompt.txt                        │     │
│  │                                                                     │     │
│  │ Output: ["AI", "LLM", "AGI", "GPT", "renewable energy",           │     │
│  │          "climate tech", "solar", "wind power"]                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ News Scoring (AI)                                                  │     │
│  │ Prompt: config/ai_filter/prompt.txt                                │     │
│  │                                                                     │     │
│  │ For each news item:                                                │     │
│  │   Input: news_title + extracted_tags                               │     │
│  │   Output: relevance_score (0-100)                                  │     │
│  │                                                                     │     │
│  │ Example:                                                           │     │
│  │   "OpenAI releases GPT-5" → Score: 95 (high relevance)            │     │
│  │   "New solar panel efficiency record" → Score: 85                 │     │
│  │   "Celebrity gossip" → Score: 5 (low relevance)                   │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Filtering & Caching                                                │     │
│  │ - Filter items with score < threshold (default: 60)               │     │
│  │ - Cache analyzed items to avoid re-processing                     │     │
│  │ - Incremental tag updates for minor interest changes              │     │
│  │ - Fallback to keyword matching if AI fails                        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         2. AI Analysis & Summarization                       │
│                                                                               │
│  Input: Filtered news items (hot list + RSS)                                 │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Data Preparation                                                   │     │
│  │ - Aggregate news by platform and keyword                           │     │
│  │ - Include ranking timeline data                                    │     │
│  │ - Add cross-platform correlation                                   │     │
│  │ - Format as structured JSON                                        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ AI Analysis (LLM)                                                  │     │
│  │ Prompt: config/ai_analysis_prompt.txt                              │     │
│  │                                                                     │     │
│  │ Analysis Dimensions:                                               │     │
│  │                                                                     │     │
│  │ 1. Core Trends (核心热点态势)                                        │     │
│  │    - Identify dominant topics                                      │     │
│  │    - Track topic evolution                                         │     │
│  │    - Detect emerging themes                                        │     │
│  │                                                                     │     │
│  │ 2. Sentiment & Controversy (舆论风向争议)                            │     │
│  │    - Positive/negative sentiment distribution                      │     │
│  │    - Controversial topics identification                           │     │
│  │    - Public opinion trends                                         │     │
│  │                                                                     │     │
│  │ 3. Signals & Anomalies (异动与弱信号)                                │     │
│  │    - Sudden popularity spikes                                      │     │
│  │    - Weak signals detection                                        │     │
│  │    - Anomaly identification                                        │     │
│  │                                                                     │     │
│  │ 4. Outlook & Strategy (研判策略建议)                                 │     │
│  │    - Trend predictions                                             │     │
│  │    - Strategic recommendations                                     │     │
│  │    - Risk assessments                                              │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Output (Structured JSON)                                           │     │
│  │ {                                                                  │     │
│  │   "core_trends": "AI continues to dominate...",                   │     │
│  │   "sentiment_controversy": "Mixed reactions to...",               │     │
│  │   "signals_anomalies": "Sudden spike in...",                      │     │
│  │   "outlook_strategy": "Expect continued growth...",               │     │
│  │   "standalone_summaries": [...]                                   │     │
│  │ }                                                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. AI Translation                                    │
│                                                                               │
│  Input: News items (Chinese)                                                 │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Batch Grouping                                                     │     │
│  │ - Group multiple items for batch translation                       │     │
│  │ - Optimize token usage                                             │     │
│  │ - Skip already-translated items                                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ AI Translation (LLM)                                               │     │
│  │ Prompt: config/ai_translation_prompt.txt                           │     │
│  │                                                                     │     │
│  │ Input: [                                                           │     │
│  │   {"id": 1, "title": "OpenAI发布GPT-5"},                           │     │
│  │   {"id": 2, "title": "新能源汽车销量创新高"}                         │     │
│  │ ]                                                                  │     │
│  │                                                                     │     │
│  │ Output: [                                                          │     │
│  │   {"id": 1, "translation": "OpenAI Releases GPT-5"},              │     │
│  │   {"id": 2, "translation": "New Energy Vehicle Sales Hit Record"} │     │
│  │ ]                                                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Bilingual Output                                                   │     │
│  │ - Original title preserved                                         │     │
│  │ - Translation added as separate field                              │     │
│  │ - Empty translation protection (keeps original)                    │     │
│  │ - Configurable per region (hot list, RSS, standalone)             │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         4. LLM Crawler Bot AI                                │
│                                                                               │
│  AI Provider: 9Router or OpenAI-compatible endpoint                          │
│  Model: Gemini 3.1 Pro (default) or configurable                             │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Login Flow Planning                                                │     │
│  │                                                                     │     │
│  │ Input: Page HTML + URL                                             │     │
│  │                                                                     │     │
│  │ AI Tasks:                                                          │     │
│  │ 1. Detect if login is required                                     │     │
│  │ 2. Infer login URL                                                 │     │
│  │ 3. Identify username/password field selectors                      │     │
│  │ 4. Plan pre-click actions (e.g., click "Login" button)            │     │
│  │ 5. Define success indicators (e.g., profile icon appears)         │     │
│  │                                                                     │     │
│  │ Output: LoginPlan {                                                │     │
│  │   login_url: "https://...",                                        │     │
│  │   username_selector: "#username",                                  │     │
│  │   password_selector: "#password",                                  │     │
│  │   pre_click_actions: ["button.login-btn"],                         │     │
│  │   success_indicators: [".user-profile"]                            │     │
│  │ }                                                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Crawl Strategy Planning                                            │     │
│  │                                                                     │     │
│  │ Input: User instructions + Page context                            │     │
│  │                                                                     │     │
│  │ AI Tasks:                                                          │     │
│  │ 1. Decompose complex instructions into sub-goals                   │     │
│  │ 2. Determine search vs. direct extraction approach                 │     │
│  │ 3. Plan navigation sequence                                        │     │
│  │ 4. Identify target content types                                   │     │
│  │                                                                     │     │
│  │ Example:                                                           │     │
│  │   Instruction: "Find latest AI news on TechCrunch"                │     │
│  │   Plan:                                                            │     │
│  │     1. Navigate to TechCrunch homepage                             │     │
│  │     2. Search for "AI" in search box                               │     │
│  │     3. Click first result                                          │     │
│  │     4. Extract article content                                     │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Selector Inference                                                 │     │
│  │                                                                     │     │
│  │ Input: Page HTML + Target content description                      │     │
│  │                                                                     │     │
│  │ AI Tasks:                                                          │     │
│  │ 1. Analyze HTML structure                                          │     │
│  │ 2. Identify content containers                                     │     │
│  │ 3. Generate CSS/XPath selectors                                    │     │
│  │ 4. Adapt to platform-specific patterns                             │     │
│  │                                                                     │     │
│  │ Platform-Specific Hints:                                           │     │
│  │ - YouTube: #video-title, #description                              │     │
│  │ - Facebook: [data-ad-preview="message"]                            │     │
│  │ - Twitter: [data-testid="tweetText"]                               │     │
│  │ - Generic: article, .content, .post-body                           │     │
│  │                                                                     │     │
│  │ Output: {                                                          │     │
│  │   title_selector: "h1.article-title",                              │     │
│  │   content_selector: "div.article-content",                         │     │
│  │   author_selector: "span.author-name",                             │     │
│  │   date_selector: "time[datetime]"                                  │     │
│  │ }                                                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Content Extraction & Cleaning                                      │     │
│  │                                                                     │     │
│  │ Input: Raw HTML content                                            │     │
│  │                                                                     │     │
│  │ AI Tasks:                                                          │     │
│  │ 1. Extract article metadata (title, author, date, category)       │     │
│  │ 2. Clean and structure article content                            │     │
│  │ 3. Generate summary (3-5 sentences)                                │     │
│  │ 4. Extract tags/keywords                                           │     │
│  │ 5. Detect language                                                 │     │
│  │ 6. Analyze sentiment                                               │     │
│  │                                                                     │     │
│  │ Output: metadata.json {                                            │     │
│  │   "title": "...",                                                  │     │
│  │   "author": "...",                                                 │     │
│  │   "published_date": "2024-01-15",                                  │     │
│  │   "category": "Technology",                                        │     │
│  │   "tags": ["AI", "LLM", "GPT"],                                    │     │
│  │   "summary": "...",                                                │     │
│  │   "language": "en",                                                │     │
│  │   "sentiment": "positive"                                          │     │
│  │ }                                                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         5. MCP Server AI Integration                         │
│                                                                               │
│  AI Client Support: Claude Desktop, Cherry Studio, Cursor, Cline, etc.       │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Natural Language Processing                                        │     │
│  │                                                                     │     │
│  │ Date Expression Parsing:                                           │     │
│  │   "last week" → 2024-01-08 to 2024-01-14                          │     │
│  │   "yesterday" → 2024-01-14                                         │     │
│  │   "本周" (this week) → 2024-01-15 to 2024-01-21                    │     │
│  │   "上个月" (last month) → 2023-12-01 to 2023-12-31                 │     │
│  │                                                                     │     │
│  │ Tool: resolve_date_range                                           │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ AI-Powered Analytics                                               │     │
│  │                                                                     │     │
│  │ 1. Trend Analysis (analyze_topic_trend)                            │     │
│  │    Modes:                                                          │     │
│  │    - lifecycle: Track topic from emergence to decline             │     │
│  │    - viral: Identify viral spread patterns                         │     │
│  │    - platform_comparison: Compare trends across platforms          │     │
│  │    - predictive: Forecast future trends                            │     │
│  │                                                                     │     │
│  │ 2. Sentiment Analysis (analyze_sentiment)                          │     │
│  │    - Multi-dimensional sentiment scoring                           │     │
│  │    - Platform-specific sentiment comparison                        │     │
│  │    - Temporal sentiment trends                                     │     │
│  │                                                                     │     │
│  │ 3. Data Insights (analyze_data_insights)                           │     │
│  │    Modes:                                                          │     │
│  │    - overview: High-level summary                                  │     │
│  │    - deep_dive: Detailed analysis                                  │     │
│  │    - comparative: Cross-period comparison                          │     │
│  │                                                                     │     │
│  │ 4. Smart Summarization (generate_summary_report)                   │     │
│  │    - Daily/weekly report generation                                │     │
│  │    - Key insight extraction                                        │     │
│  │    - Trend narrative construction                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Intelligent Search                                                 │     │
│  │                                                                     │     │
│  │ Tool: search_news                                                  │     │
│  │                                                                     │     │
│  │ Search Modes:                                                      │     │
│  │ - keyword: Exact keyword matching                                  │     │
│  │ - fuzzy: Fuzzy text matching                                       │     │
│  │ - entity: Named entity recognition                                 │     │
│  │                                                                     │     │
│  │ Features:                                                          │     │
│  │ - Relevance scoring                                                │     │
│  │ - Cross-platform aggregation                                       │     │
│  │ - Deduplication                                                    │     │
│  │ - Ranking by weight/hot_value                                      │     │
│  │                                                                     │     │
│  │ Tool: find_related_news                                            │     │
│  │ - Similarity-based discovery                                       │     │
│  │ - Topic clustering                                                 │     │
│  │ - Related article recommendations                                  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Context-Aware Tool Selection                                       │     │
│  │                                                                     │     │
│  │ AI clients automatically select appropriate tools based on:        │     │
│  │ - User query intent                                                │     │
│  │ - Available data                                                   │     │
│  │ - Tool descriptions and parameters                                 │     │
│  │ - Previous conversation context                                    │     │
│  │                                                                     │     │
│  │ Example:                                                           │     │
│  │   User: "What were the trending AI topics last week?"             │     │
│  │   AI Client selects:                                               │     │
│  │     1. resolve_date_range("last week")                             │     │
│  │     2. get_news_by_date(start_date, end_date)                      │     │
│  │     3. search_news(keyword="AI")                                   │     │
│  │     4. analyze_topic_trend(topic="AI", mode="lifecycle")           │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Deployment Architecture

This diagram shows the three deployment strategies and their configurations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Deployment Strategy Overview                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. GitHub Actions Deployment                         │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ GitHub Repository                                                  │     │
│  │                                                                     │     │
│  │  ┌──────────────────────────────────────────────────────────┐     │     │
│  │  │ .github/workflows/crawler.yml                            │     │     │
│  │  │                                                           │     │     │
│  │  │ on:                                                       │     │     │
│  │  │   schedule:                                               │     │     │
│  │  │     - cron: '0 */2 * * *'  # Every 2 hours               │     │     │
│  │  │   workflow_dispatch:        # Manual trigger             │     │     │
│  │  │                                                           │     │     │
│  │  │ jobs:                                                     │     │     │
│  │  │   crawl:                                                  │     │     │
│  │  │     runs-on: ubuntu-latest                                │     │     │
│  │  │     steps:                                                │     │     │
│  │  │       - Checkout code                                     │     │     │
│  │  │       - Setup Python 3.11                                 │     │     │
│  │  │       - Install dependencies                              │     │     │
│  │  │       - Run crawler (python main.py)                      │     │     │
│  │  │       - Deploy to GitHub Pages                            │     │     │
│  │  └──────────────────────────────────────────────────────────┘     │     │
│  │                                                                     │     │
│  │  ┌──────────────────────────────────────────────────────────┐     │     │
│  │  │ GitHub Secrets (Configuration)                           │     │     │
│  │  │                                                           │     │     │
│  │  │ - FEISHU_WEBHOOK_URL                                      │     │     │
│  │  │ - DINGTALK_WEBHOOK_URL                                    │     │     │
│  │  │ - WEWORK_WEBHOOK_URL                                      │     │     │
│  │  │ - TELEGRAM_BOT_TOKEN                                      │     │     │
│  │  │ - EMAIL_SMTP_SERVER                                       │     │     │
│  │  │ - S3_ENDPOINT_URL                                         │     │     │
│  │  │ - S3_ACCESS_KEY_ID                                        │     │     │
│  │  │ - S3_SECRET_ACCESS_KEY                                    │     │     │
│  │  │ - AI_API_KEY                                              │     │     │
│  │  │ - ... (all sensitive configuration)                       │     │     │
│  │  └──────────────────────────────────────────────────────────┘     │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Execution Environment (GitHub-hosted runner)                       │     │
│  │                                                                     │     │
│  │ - Ubuntu latest                                                    │     │
│  │ - Python 3.11                                                      │     │
│  │ - 2 CPU cores, 7 GB RAM                                            │     │
│  │ - 14 GB SSD storage                                                │     │
│  │ - 6-hour maximum execution time                                    │     │
│  │                                                                     │     │
│  │ Storage Strategy:                                                  │     │
│  │ - Local SQLite (temporary, cleared after run)                     │     │
│  │ - Remote S3 (persistent, required for data retention)             │     │
│  │ - GitHub Pages (HTML reports, public access)                      │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Output Channels                                                    │     │
│  │                                                                     │     │
│  │ - Notification channels (Feishu, DingTalk, etc.)                  │     │
│  │ - GitHub Pages: https://username.github.io/TrendRadar             │     │
│  │ - Remote S3 storage                                                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  Advantages:                                                                  │
│  ✓ Zero infrastructure cost                                                   │
│  ✓ Automatic scaling                                                          │
│  ✓ Built-in CI/CD                                                             │
│  ✓ Easy setup (fork and configure)                                            │
│                                                                               │
│  Limitations:                                                                 │
│  ✗ 6-hour maximum execution time                                              │
│  ✗ Limited to scheduled intervals                                             │
│  ✗ No persistent local storage                                                │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         2. Docker Deployment                                 │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Docker Compose Configuration                                       │     │
│  │                                                                     │     │
│  │  version: '3.8'                                                    │     │
│  │  services:                                                         │     │
│  │                                                                     │     │
│  │    trendradar:                                                     │     │
│  │      image: wantcat/trendradar:latest                              │     │
│  │      volumes:                                                      │     │
│  │        - ./output:/app/output                                      │     │
│  │        - ./config:/app/config                                      │     │
│  │      environment:                                                  │     │
│  │        - FEISHU_WEBHOOK_URL=${FEISHU_WEBHOOK_URL}                  │     │
│  │        - S3_ENDPOINT_URL=${S3_ENDPOINT_URL}                        │     │
│  │        - ... (all env vars)                                        │     │
│  │      restart: unless-stopped                                       │     │
│  │                                                                     │     │
│  │    mcp-server:                                                     │     │
│  │      image: wantcat/trendradar-mcp:latest                          │     │
│  │      ports:                                                        │     │
│  │        - "3333:3333"                                               │     │
│  │      volumes:                                                      │     │
│  │        - ./output:/app/output                                      │     │
│  │        - ./config:/app/config                                      │     │
│  │      environment:                                                  │     │
│  │        - MCP_TRANSPORT=http                                        │     │
│  │      restart: unless-stopped                                       │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Container Architecture                            │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────┐      ┌──────────────────────────┐    │    │
│  │  │ TrendRadar Core          │      │ MCP Server               │    │    │
│  │  │ Container                │      │ Container                │    │    │
│  │  │                          │      │                          │    │    │
│  │  │ - Python 3.11-slim       │      │ - Python 3.11-slim       │    │    │
│  │  │ - Crawler module         │      │ - FastMCP 2.0            │    │    │
│  │  │ - Filter module          │      │ - 27 tools               │    │    │
│  │  │ - AI analysis            │      │ - HTTP server :3333      │    │    │
│  │  │ - Notification           │      │ - stdio support          │    │    │
│  │  │ - Timeline scheduler     │      │                          │    │    │
│  │  │                          │      │                          │    │    │
│  │  │ CMD: python main.py      │      │ CMD: python -m           │    │    │
│  │  │                          │      │      mcp_server           │    │    │
│  │  └────────────┬─────────────┘      └────────────┬─────────────┘    │    │
│  │               │                                  │                  │    │
│  │               └──────────────┬───────────────────┘                  │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │               ┌──────────────────────────────┐                     │    │
│  │               │ Shared Volumes               │                     │    │
│  │               │                              │                     │    │
│  │               │ ./output (Host)              │                     │    │
│  │               │   ├── hotlist/*.db           │                     │    │
│  │               │   ├── rss/*.db               │                     │    │
│  │               │   └── reports/*.html         │                     │    │
│  │               │                              │                     │    │
│  │               │ ./config (Host)              │                     │    │
│  │               │   ├── config.yaml            │                     │    │
│  │               │   ├── frequency_words.txt    │                     │    │
│  │               │   └── timeline.yaml          │                     │    │
│  │               └──────────────────────────────┘                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Deployment Targets                                                 │     │
│  │                                                                     │     │
│  │ 1. Linux Server                                                    │     │
│  │    - docker-compose up -d                                          │     │
│  │    - systemd service for auto-start                                │     │
│  │                                                                     │     │
│  │ 2. NAS (Synology, QNAP, Unraid)                                    │     │
│  │    - Docker UI for container management                            │     │
│  │    - Environment variable configuration                            │     │
│  │    - Volume mapping through UI                                     │     │
│  │                                                                     │     │
│  │ 3. Cloud VPS (AWS, DigitalOcean, Linode)                           │     │
│  │    - Docker + Docker Compose                                       │     │
│  │    - Persistent volumes                                            │     │
│  │    - Security groups for port 3333                                 │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  Storage Options:                                                             │
│  1. Local SQLite (default)                                                    │
│     - Data in ./output volume                                                 │
│     - No additional configuration                                             │
│     - Suitable for single-instance                                            │
│                                                                               │
│  2. Remote S3-Compatible                                                      │
│     - Cloudflare R2, AWS S3, MinIO                                            │
│     - Environment variables for configuration                                 │
│     - Enables multi-instance deployments                                      │
│     - Automatic sync                                                          │
│                                                                               │
│  Advantages:                                                                  │
│  ✓ Consistent environment                                                     │
│  ✓ Easy updates (pull new image)                                              │
│  ✓ Multi-architecture support (amd64, arm64)                                  │
│  ✓ Isolated dependencies                                                      │
│  ✓ Persistent local storage                                                   │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. Local Execution Deployment                        │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Setup Process                                                      │     │
│  │                                                                     │     │
│  │ 1. Clone repository                                                │     │
│  │    git clone https://github.com/sansan0/TrendRadar.git            │     │
│  │    cd TrendRadar                                                   │     │
│  │                                                                     │     │
│  │ 2. Create virtual environment                                      │     │
│  │    python -m venv .venv                                            │     │
│  │    source .venv/bin/activate  # Linux/Mac                          │     │
│  │    .venv\Scripts\activate     # Windows                            │     │
│  │                                                                     │     │
│  │ 3. Install dependencies                                            │     │
│  │    pip install -r requirements.txt                                 │     │
│  │                                                                     │     │
│  │ 4. Configure                                                       │     │
│  │    - Edit config/config.yaml                                       │     │
│  │    - Edit config/frequency_words.txt                               │     │
│  │    - Edit config/timeline.yaml                                     │     │
│  │    - Optional: Create .env file                                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Execution Modes                                                    │     │
│  │                                                                     │     │
│  │ 1. Single Run                                                      │     │
│  │    python main.py                                                  │     │
│  │                                                                     │     │
│  │ 2. Custom Config                                                   │     │
│  │    python main.py --config custom_config.yaml                      │     │
│  │                                                                     │     │
│  │ 3. MCP Server (stdio mode)                                         │     │
│  │    python -m mcp_server                                            │     │
│  │                                                                     │     │
│  │ 4. MCP Server (HTTP mode)                                          │     │
│  │    python -m mcp_server --transport http --port 3333               │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Scheduling Options                                                 │     │
│  │                                                                     │     │
│  │ Linux/Mac (cron):                                                  │     │
│  │   crontab -e                                                       │     │
│  │   0 */2 * * * cd /path/to/TrendRadar && .venv/bin/python main.py  │     │
│  │                                                                     │     │
│  │ Windows (Task Scheduler):                                          │     │
│  │   - Create new task                                                │     │
│  │   - Trigger: Every 2 hours                                         │     │
│  │   - Action: Run Python script                                      │     │
│  │   - Start in: TrendRadar directory                                 │     │
│  │                                                                     │     │
│  │ Linux (systemd service):                                           │     │
│  │   [Unit]                                                           │     │
│  │   Description=TrendRadar News Crawler                              │     │
│  │   After=network.target                                             │     │
│  │                                                                     │     │
│  │   [Service]                                                        │     │
│  │   Type=simple                                                      │     │
│  │   User=trendradar                                                  │     │
│  │   WorkingDirectory=/opt/TrendRadar                                 │     │
│  │   ExecStart=/opt/TrendRadar/.venv/bin/python main.py              │     │
│  │   Restart=on-failure                                               │     │
│  │                                                                     │     │
│  │   [Install]                                                        │     │
│  │   WantedBy=multi-user.target                                       │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  Advantages:                                                                  │
│  ✓ Full control over execution environment                                    │
│  ✓ Easy debugging and development                                             │
│  ✓ No container overhead                                                      │
│  ✓ Direct file system access                                                  │
│                                                                               │
│  Limitations:                                                                 │
│  ✗ Requires manual dependency management                                      │
│  ✗ Platform-specific setup                                                    │
│  ✗ No automatic scaling                                                       │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         Timeline System Configuration                        │
│                                                                               │
│  Unified scheduling for crawl, push, and analysis operations                 │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Preset Templates                                                   │     │
│  │                                                                     │     │
│  │ 1. always_on (Default)                                             │     │
│  │    - 24/7 operation                                                │     │
│  │    - Continuous crawling and pushing                               │     │
│  │                                                                     │     │
│  │ 2. morning_evening                                                 │     │
│  │    - Morning: 7:00-9:00                                            │     │
│  │    - Evening: 18:00-20:00                                          │     │
│  │                                                                     │     │
│  │ 3. office_hours                                                    │     │
│  │    - Weekday: 9:00-18:00                                           │     │
│  │    - Weekend: Off                                                  │     │
│  │                                                                     │     │
│  │ 4. night_owl                                                       │     │
│  │    - 22:00-02:00                                                   │     │
│  │                                                                     │     │
│  │ 5. custom                                                          │     │
│  │    - Fully customizable                                            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Time Period Configuration Example                                  │     │
│  │                                                                     │     │
│  │ periods:                                                           │     │
│  │   - name: "Morning Digest"                                         │     │
│  │     days: [1, 2, 3, 4, 5]  # Monday-Friday                         │     │
│  │     start_time: "07:00"                                            │     │
│  │     end_time: "09:00"                                              │     │
│  │     actions:                                                       │     │
│  │       crawl: true                                                  │     │
│  │       push: true                                                   │     │
│  │       ai_analysis: true                                            │     │
│  │     filter_mode: "keyword"  # or "ai"                              │     │
│  │     filter_config: "morning_keywords.txt"                          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│  Features:                                                                    │
│  - Cross-midnight time periods                                                │
│  - Per-period filter configuration                                            │
│  - Independent AI analysis settings                                           │
│  - Conflict detection                                                         │
│  - Visual configuration editor (web-based)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

These ASCII art diagrams provide comprehensive visualization of the TrendRadar system architecture:

1. **High-Level Ecosystem**: Shows the three-module architecture and unified storage layer
2. **Hot List Data Flow**: Illustrates news aggregation from 11 platforms through filtering to storage
3. **RSS Feed Data Flow**: Shows RSS/Atom feed processing with GUID-based deduplication
4. **LLM Crawler Bot**: Details the AI-powered autonomous crawling pipeline
5. **Storage Architecture**: Explains the multi-backend storage with SQLite and S3-compatible options
6. **Notification Flow**: Shows how data flows from storage through formatting to 9 notification channels
7. **AI Mechanisms**: Comprehensive view of all AI components (filtering, analysis, translation, crawler, MCP)
8. **Deployment Architecture**: Details three deployment strategies (GitHub Actions, Docker, Local)

These diagrams can be embedded directly in Markdown documentation and provide clear visual understanding of the system's architecture and data flows.

