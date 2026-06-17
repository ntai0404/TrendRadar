---
title: TrendRadar System Analysis
date: 2024-01-15
version: 1.0.0
author: TrendRadar Analysis Team
description: Comprehensive architectural analysis of the TrendRadar news aggregation and analysis system
---

# TrendRadar System Analysis

## Document Metadata

- **Title**: TrendRadar System Analysis
- **Version**: 1.0.0
- **Date**: 2024-01-15
- **Status**: Draft
- **Purpose**: Comprehensive architectural analysis covering all three major modules (Core System, LLM Crawler Bot, MCP Server)

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture Overview](#2-system-architecture-overview)
   - 2.1 [High-Level Architecture](#21-high-level-architecture)
   - 2.2 [Module Relationships](#22-module-relationships)
   - 2.3 [Core Components](#23-core-components)
3. [TrendRadar Core System](#3-trendradar-core-system)
   - 3.1 [Architecture](#31-architecture)
   - 3.2 [Crawler Module](#32-crawler-module)
   - 3.3 [Filter Module](#33-filter-module)
   - 3.4 [AI Analysis Module](#34-ai-analysis-module)
   - 3.5 [Storage Manager](#35-storage-manager)
   - 3.6 [Notification Module](#36-notification-module)
   - 3.7 [Timeline Scheduler](#37-timeline-scheduler)
   - 3.8 [Technology Stack](#38-technology-stack)
4. [LLM News Crawler Bot](#4-llm-news-crawler-bot)
   - 4.1 [Architecture](#41-architecture)
   - 4.2 [Crawler Engine](#42-crawler-engine)
   - 4.3 [AI Agent](#43-ai-agent)
   - 4.4 [Authentication Handler](#44-authentication-handler)
   - 4.5 [Output Generator](#45-output-generator)
   - 4.6 [Technology Stack](#46-technology-stack)
   - 4.7 [Integration with Core System](#47-integration-with-core-system)
5. [MCP Server](#5-mcp-server)
   - 5.1 [Architecture](#51-architecture)
   - 5.2 [Tool Categories](#52-tool-categories)
   - 5.3 [Transport Modes](#53-transport-modes)
   - 5.4 [Resource Endpoints](#54-resource-endpoints)
   - 5.5 [Technology Stack](#55-technology-stack)
   - 5.6 [Integration Points](#56-integration-points)
6. [Data Flow Architecture](#6-data-flow-architecture)
   - 6.1 [Hot List Data Flow](#61-hot-list-data-flow)
   - 6.2 [RSS Feed Data Flow](#62-rss-feed-data-flow)
   - 6.3 [LLM Crawler Bot Integration Flow](#63-llm-crawler-bot-integration-flow)
   - 6.4 [Storage to Notification Flow](#64-storage-to-notification-flow)
7. [AI Mechanisms](#7-ai-mechanisms)
   - 7.1 [AI-Powered Smart Filtering](#71-ai-powered-smart-filtering)
   - 7.2 [AI Analysis and Summarization](#72-ai-analysis-and-summarization)
   - 7.3 [AI Translation](#73-ai-translation)
   - 7.4 [LLM Crawler Bot AI Mechanisms](#74-llm-crawler-bot-ai-mechanisms)
   - 7.5 [MCP Server AI Integration](#75-mcp-server-ai-integration)
8. [Deployment Strategies](#8-deployment-strategies)
   - 8.1 [GitHub Actions Deployment](#81-github-actions-deployment)
   - 8.2 [Docker Deployment](#82-docker-deployment)
   - 8.3 [Local Execution Deployment](#83-local-execution-deployment)
   - 8.4 [Storage Backend Options](#84-storage-backend-options)
   - 8.5 [Timeline System Configuration](#85-timeline-system-configuration)
9. [Storage and Query Architecture](#9-storage-and-query-architecture)
   - 9.1 [Storage Backend Architecture](#91-storage-backend-architecture)
   - 9.2 [MCP Server Query Capabilities](#92-mcp-server-query-capabilities)
   - 9.3 [Data Analysis Functions](#93-data-analysis-functions)
   - 9.4 [Remote Storage Synchronization](#94-remote-storage-synchronization)
10. [Notification and Output Mechanisms](#10-notification-and-output-mechanisms)
    - 10.1 [Notification Channels](#101-notification-channels)
    - 10.2 [Message Formatting and Adaptation](#102-message-formatting-and-adaptation)
    - 10.3 [HTML Report and GitHub Pages Deployment](#103-html-report-and-github-pages-deployment)
    - 10.4 [Email Notification with HTML Formatting](#104-email-notification-with-html-formatting)
11. [Filtering and Configuration](#11-filtering-and-configuration)
    - 11.1 [Keyword-Based Filtering System](#111-keyword-based-filtering-system)
    - 11.2 [AI-Powered Interest-Based Filtering](#112-ai-powered-interest-based-filtering)
    - 11.3 [Global Filter Keywords](#113-global-filter-keywords)

---

## 1. Introduction

[Placeholder: Introduction section will provide an overview of the TrendRadar project, its purpose, and the scope of this analysis document.]

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

TrendRadar is built on a modular architecture consisting of three primary components that work together to provide comprehensive news aggregation, analysis, and delivery capabilities. The system is designed with separation of concerns, allowing each module to operate independently while sharing a unified storage layer for data persistence and exchange.

```
┌─────────────────────────────────────────────────────────────────┐
│                      TrendRadar Ecosystem                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  TrendRadar      │  │  LLM Crawler     │  │  MCP Server  │  │
│  │  Core System     │◄─┤  Bot Module      │  │  (FastMCP)   │  │
│  │                  │  │                  │  │              │  │
│  │  - Crawling      │  │  - AI Selector   │  │  - Query API │  │
│  │  - Filtering     │  │  - Auth Support  │  │  - Analytics │  │
│  │  - Analysis      │  │  - Content       │  │  - Search    │  │
│  │  - Storage       │  │    Extraction    │  │  - Notify    │  │
│  │  - Notification  │  │                  │  │              │  │
│  └────────┬─────────┘  └──────────────────┘  └──────┬───────┘  │
│           │                                           │          │
│           │         ┌──────────────────┐            │          │
│           └────────►│  Storage Layer   │◄───────────┘          │
│                     │  - SQLite DB     │                        │
│                     │  - S3 Compatible │                        │
│                     └──────────────────┘                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

The architecture follows a hub-and-spoke pattern where the **TrendRadar Core System** acts as the central orchestrator, the **LLM Crawler Bot** provides specialized content extraction capabilities, and the **MCP Server** exposes AI-powered query and analysis interfaces. All three modules share access to a common **Storage Layer** that supports both local SQLite databases and remote S3-compatible cloud storage.

**Key Architectural Principles:**

1. **Modularity**: Each component can be deployed and scaled independently
2. **Shared Storage**: Unified data layer enables seamless data exchange between modules
3. **AI-First Design**: Artificial intelligence is integrated throughout the system for filtering, analysis, extraction, and querying
4. **Flexible Deployment**: Supports GitHub Actions, Docker containers, and local execution
5. **Multi-Channel Output**: Delivers news through 9+ notification channels and programmatic APIs

### 2.2 Module Relationships

The three modules interact through well-defined interfaces and shared resources:

**1. TrendRadar Core System** (Primary Module)

The core system serves as the main orchestrator for the entire news aggregation pipeline. It is responsible for:

- **Crawling**: Fetching trending news from 11+ hot list platforms (Zhihu, Weibo, Bilibili, etc.) and RSS/Atom feeds
- **Filtering**: Applying keyword-based and AI-powered interest-based filters to identify relevant content
- **AI Analysis**: Performing sentiment analysis, trend detection, and multi-language translation
- **Storage Management**: Persisting data to local SQLite databases and synchronizing with remote S3-compatible storage
- **Notification**: Pushing filtered and analyzed news to 9 notification channels (Feishu, DingTalk, Telegram, Email, etc.)
- **Scheduling**: Managing crawl, push, and analysis operations based on configurable timelines

The core system integrates with the LLM Crawler Bot when it encounters complex crawling scenarios that require authentication or advanced content extraction. It writes all collected data to the shared storage layer, making it available for the MCP Server to query and analyze.

**2. LLM News Crawler Bot** (Auxiliary Module)

The crawler bot is an autonomous web crawler that uses Large Language Models to intelligently navigate websites and extract content. It operates as:

- **On-Demand Service**: Invoked by the core system for complex extraction tasks
- **Standalone Tool**: Can be executed independently via CLI or API for custom crawling needs
- **AI-Powered Navigator**: Uses LLMs to infer selectors, plan login flows, and extract structured content
- **Authentication Handler**: Supports optional username/password authentication for protected content

The bot receives crawling requests (URL + optional credentials) from the core system, performs AI-driven extraction, and outputs structured data (metadata.json, article.txt, screenshot.png, page.html) that the core system consumes and integrates into its data pipeline.

**3. MCP Server** (Analysis Module)

The MCP (Model Context Protocol) Server provides a programmatic interface for AI clients and applications to query and analyze news data. It functions as:

- **Query Interface**: Exposes 27+ tools for retrieving news, searching content, and checking system status
- **Analytics Engine**: Provides trend analysis, sentiment analysis, topic tracking, and summary generation
- **AI Client Integration**: Supports stdio and HTTP transport modes for integration with Claude Desktop, Cursor, Cline, and other MCP-compatible clients
- **Notification Gateway**: Can trigger notifications through the core system's notification module

The MCP Server reads from the same SQLite databases and configuration files as the core system, ensuring data consistency. It can also trigger manual crawls and send notifications by invoking core system functionality.

**Data Flow Between Modules:**

```
┌─────────────┐
│ Hot List    │
│ Platforms   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     Complex      ┌─────────────┐
│ TrendRadar  │────Extraction────►│ LLM Crawler │
│ Core System │◄────Results───────│ Bot         │
└──────┬──────┘                   └─────────────┘
       │
       │ Write Data
       ▼
┌─────────────┐
│ Storage     │
│ Layer       │
└──────┬──────┘
       │
       │ Read Data
       ▼
┌─────────────┐
│ MCP Server  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AI Clients  │
│ (Claude,    │
│  Cursor,    │
│  Cline)     │
└─────────────┘
```

### 2.3 Core Components

This section provides a detailed overview of the core components within each of the three major modules: TrendRadar Core System, LLM News Crawler Bot, and MCP Server.

#### 2.3.1 TrendRadar Core System Components

The TrendRadar Core System is a Python-based monolithic application with a modular internal structure. It consists of six primary components:

**1. Crawler Module** (`trendradar/crawler/`)

- **Purpose**: Multi-platform news aggregation from 11+ hot list platforms and RSS/Atom feed support
- **Key Features**:
  - Platform-specific adapters for data normalization (Zhihu, Weibo, Bilibili, Douyin, Baidu, 36Kr, etc.)
  - RSS/Atom feed subscription support with GUID-based deduplication
  - Configurable request intervals and timeout settings
  - Automatic retry mechanisms for failed requests
  - URL-based deduplication to remove duplicate news items
- **Technology**: Python requests library, feedparser for RSS parsing

**2. Filter Module** (`trendradar/core/frequency.py`, `trendradar/ai/`)

- **Purpose**: Intelligent filtering of news based on keywords and AI-powered interest matching
- **Key Features**:
  - Keyword-based filtering using `config/frequency_words.txt`
  - AI-powered interest-based filtering using natural language descriptions from `config/ai_interests.txt`
  - Regex pattern support for advanced matching
  - Global filter keywords for content exclusion
  - Per-keyword display limits and sorting options (by weight or position)
  - Caching mechanism to avoid re-processing analyzed news
- **Technology**: LiteLLM for AI integration, regex for pattern matching

**3. AI Analysis Module** (`trendradar/ai/`)

- **Purpose**: Deep analysis, sentiment detection, and multi-language translation
- **Key Features**:
  - Integration with LiteLLM for multi-provider AI support (100+ providers)
  - Four-dimensional analysis: core trends, sentiment & controversy, signals & anomalies, outlook & strategy
  - Multi-language translation with batch processing
  - Customizable prompt engineering via configuration files
  - Model fallback support for reliability
  - Safety settings for Gemini models
- **Technology**: LiteLLM (supports OpenAI, Google Gemini, Anthropic Claude, DeepSeek, etc.)

**4. Storage Manager** (`trendradar/storage/`)

- **Purpose**: Unified interface for local and remote data persistence
- **Key Features**:
  - SQLite database for structured data storage with date-based organization
  - S3-compatible cloud storage support (Cloudflare R2, AWS S3, MinIO, etc.)
  - Automatic synchronization between local and remote storage
  - Date-based data retention policies and cleanup mechanisms
  - Separate storage tables for hot list data and RSS feed data
  - Transaction support for data integrity
- **Technology**: Python sqlite3, boto3 for S3-compatible storage

**5. Notification Module** (`trendradar/notification/`)

- **Purpose**: Multi-channel news delivery with format adaptation
- **Key Features**:
  - Support for 9 notification channels: Feishu (飞书), DingTalk (钉钉), WeWork (企业微信), Telegram, Email, ntfy, Bark, Slack, Generic Webhook
  - Automatic format adaptation per channel (Markdown → HTML/plain text)
  - Batch sending mechanism for message size limits
  - Multi-account support with semicolon-separated configuration
  - HTML report generation for email and GitHub Pages
  - Retry mechanisms for failed deliveries
- **Technology**: Python requests, SMTP for email, platform-specific APIs

**6. Timeline Scheduler** (`trendradar/core/scheduler.py`, `config/timeline.yaml`)

- **Purpose**: Unified scheduling system for crawl, push, and analysis operations
- **Key Features**:
  - 5 preset templates: always_on, morning_evening, office_hours, night_owl, custom
  - Weekday/weekend differentiation
  - Cross-midnight time period support
  - Per-period configuration for filters and AI analysis
  - Conflict detection for overlapping time periods
  - Visual configuration editor (web-based)
- **Technology**: Python datetime, pytz for timezone handling, PyYAML for configuration

**Technology Stack Summary**:
- **Language**: Python 3.12+
- **Core Libraries**: requests (HTTP), PyYAML (config), pytz (timezone)
- **Storage**: sqlite3 (local), boto3 (S3-compatible remote)
- **AI Integration**: litellm (multi-provider), json-repair (JSON parsing)
- **RSS Parsing**: feedparser
- **Async Support**: asyncio (for MCP integration)
- **Retry Logic**: tenacity

#### 2.3.2 LLM News Crawler Bot Components

The LLM News Crawler Bot is an autonomous web crawler with AI-driven navigation and content extraction capabilities. It operates as a separate module that can be invoked by the core system or used independently.

**1. Crawler Engine** (`news_crawler_bot/crawler.py`)

- **Purpose**: Browser automation for web page navigation and content capture
- **Key Features**:
  - Playwright-based browser automation
  - Support for bundled Chromium, system Chrome, and CDP (Chrome DevTools Protocol) mode
  - Headless and headed execution modes
  - Full-page screenshot capture
  - Raw HTML preservation
  - Cookie and session management
  - Viewport configuration for responsive testing
- **Technology**: Playwright (Python), Chromium browser

**2. AI Agent** (`news_crawler_bot/agent.py`)

- **Purpose**: Intelligent planning and execution of crawling tasks
- **Key Features**:
  - **Login Flow Planning**: Analyzes page HTML to detect login requirements, infers login URL and form selectors, plans pre-click actions and success indicators
  - **Crawl Strategy Planning**: Decomposes complex instructions into sub-goals, determines search vs. direct extraction approach, plans navigation sequences
  - **Selector Inference**: Analyzes HTML structure to find content selectors, adapts to dynamic page layouts, handles platform-specific patterns (YouTube, Facebook, etc.)
  - **Content Extraction**: Extracts article metadata (title, author, date, category), cleans and structures article content, generates summaries and tags
  - Multi-goal decomposition for complex tasks
  - Error recovery strategies
- **Technology**: LLM integration via 9Router or OpenAI-compatible endpoints (default: Gemini 3.1 Pro)

**3. Authentication Handler** (`news_crawler_bot/agent.py`, integrated)

- **Purpose**: Optional username/password authentication for protected content
- **Key Features**:
  - Platform-specific login flow adaptation
  - Automatic detection of login forms and fields
  - Session persistence across navigation
  - Fallback strategies for failed authentication
  - Support for common authentication patterns (username/password, email/password)
- **Technology**: Playwright for form interaction, AI for selector inference

**4. Output Generator** (`news_crawler_bot/models.py`, `news_crawler_bot/crawler.py`)

- **Purpose**: Structured output generation for downstream consumption
- **Key Features**:
  - **metadata.json**: Structured metadata including title, author, date, category, tags, summary, sentiment, language
  - **article.txt**: Clean article text with proper formatting and paragraph breaks
  - **screenshot.png**: Full-page screenshot for visual verification
  - **page.html**: Raw HTML for debugging and fallback processing
  - JSON schema validation for metadata
  - UTF-8 encoding for international content
- **Technology**: Python json, Pillow for image processing

**Technology Stack Summary**:
- **Language**: Python 3.8+
- **Browser Automation**: Playwright
- **AI Integration**: 9Router or OpenAI-compatible endpoints
- **API Mode**: FastAPI for REST API
- **CLI Mode**: argparse for command-line interface
- **HTML Processing**: BeautifulSoup4 (via html_utils.py)
- **Configuration**: python-dotenv for environment variables

**Integration with Core System**:
- Core system invokes crawler bot for complex extraction tasks requiring authentication
- Bot outputs (metadata.json, article.txt) are consumed by core system's data pipeline
- Shared AI model configuration via environment variables
- Can operate independently via CLI or API for standalone crawling tasks

#### 2.3.3 MCP Server Components

The MCP Server is a FastMCP 2.0-based server that provides AI-powered analysis tools and APIs for querying and analyzing news data. It exposes 27+ tools organized into 8 categories.

**1. Tool Categories** (27 tools in 8 categories)

**Date Resolution Tools** (1 tool):
- `resolve_date_range`: Natural language date parsing ("本周", "最近7天", "last week") → precise date ranges

**Data Query Tools** (3 tools):
- `get_latest_news`: Retrieve most recent news batch with platform filtering
- `get_news_by_date`: Historical news retrieval with date range support
- `get_trending_topics`: Hot topic statistics with keyword/auto-extract modes

**RSS Query Tools** (3 tools):
- `get_latest_rss`: Latest RSS feed items with multi-day support
- `search_rss`: Keyword search in RSS data across feeds
- `get_rss_feeds_status`: RSS source status and statistics

**Search Tools** (2 tools):
- `search_news`: Unified search with keyword/fuzzy/entity modes, supports hot list + RSS
- `find_related_news`: Similarity-based news discovery with configurable threshold

**Analytics Tools** (6 tools):
- `analyze_topic_trend`: Trend analysis with 4 modes (trend, lifecycle, viral, predict)
- `analyze_data_insights`: Data insights with 3 modes (platform_compare, platform_activity, keyword_cooccur)
- `analyze_sentiment`: Sentiment analysis with emotion distribution and trend detection
- `aggregate_news`: Cross-platform deduplication and aggregation
- `compare_periods`: Time period comparison (week-over-week, month-over-month)
- `generate_summary_report`: Daily/weekly summary generation

**System Management Tools** (4 tools):
- `get_current_config`: Configuration retrieval (crawler, push, keywords, weights)
- `get_system_status`: Health check and system statistics
- `check_version`: Version update check for TrendRadar and MCP Server
- `trigger_crawl`: Manual crawl execution with optional persistence

**Storage Sync Tools** (3 tools):
- `sync_from_remote`: Remote to local data synchronization (pull from S3)
- `get_storage_status`: Storage backend status (local/remote)
- `list_available_dates`: Available data dates in local/remote storage

**Article Reader Tools** (2 tools):
- `read_article`: Single article content via Jina AI Reader (Markdown output)
- `read_articles_batch`: Batch article reading (max 5, with rate limiting)

**Notification Tools** (3 tools):
- `get_notification_channels`: Channel status check (9 channels)
- `send_notification`: Multi-channel message sending with format adaptation
- `get_channel_format_guide`: Format strategy guide for each channel

**2. Transport Modes**

**stdio Mode**:
- Standard input/output for local AI clients
- Supported clients: Claude Desktop, Cherry Studio, Cursor IDE, Cline extension
- Zero network configuration required
- Ideal for local development and testing

**HTTP Mode**:
- REST API on port 3333 for remote access
- WebSocket support for real-time updates
- CORS enabled for web client integration
- Suitable for production deployments and multi-client access

**3. Resource Endpoints** (4 MCP resources)

MCP resources provide read-only access to configuration and metadata:
- `config://platforms`: Platform list with IDs and names
- `config://rss-feeds`: RSS feed list with status
- `data://available-dates`: Available data dates in storage
- `config://keywords`: Keyword configuration from frequency_words.txt

**4. Technology Stack Summary**:
- **Language**: Python 3.12+
- **Framework**: FastMCP 2.0 (MCP protocol implementation)
- **Async Runtime**: asyncio for concurrent operations
- **Storage Access**: Shared SQLite databases with core system
- **Configuration**: Shared config files with core system
- **Article Reading**: Jina AI Reader API (free tier, 100 RPM)
- **Date Parsing**: Custom DateParser utility with natural language support

**5. Integration Points**

The MCP Server integrates tightly with the TrendRadar Core System:
- **Shared Storage Layer**: Reads from same SQLite databases as core system (hot list and RSS)
- **Shared Configuration**: Accesses same config files (config.yaml, frequency_words.txt, timeline.yaml)
- **Notification Integration**: Can trigger notifications via core system's notification module
- **Crawl Triggering**: Can initiate crawl tasks via system management tools
- **Data Synchronization**: Can pull data from remote storage for local analysis

**Key Design Principles**:
- **Read-Only by Default**: Most tools are read-only to prevent data corruption
- **Async-First**: All tools use asyncio for non-blocking operations
- **Error Handling**: Comprehensive error handling with structured error responses
- **Rate Limiting**: Built-in rate limiting for external APIs (Jina AI Reader)
- **Token Optimization**: Optional parameters to reduce token usage (include_url, include_summary)
- **Natural Language Support**: Date expressions, search queries, and analysis parameters support both English and Chinese

---

## 3. TrendRadar Core System

### 3.1 Architecture

[Placeholder: Python-based monolithic application with modular internal structure]

### 3.2 Crawler Module

[Placeholder: Multi-platform news aggregation from 11+ hot list platforms and RSS/Atom feed support]

### 3.3 Filter Module

[Placeholder: Keyword-based and AI-powered interest-based filtering]

### 3.4 AI Analysis Module

[Placeholder: Integration with LiteLLM for multi-provider AI support, sentiment analysis, and translation]

### 3.5 Storage Manager

[Placeholder: Unified interface for local SQLite and remote S3-compatible storage]

### 3.6 Notification Module

[Placeholder: Multi-channel push support for 9 notification channels]

### 3.7 Timeline Scheduler

[Placeholder: Unified scheduling system with 5 preset templates]

### 3.8 Technology Stack

[Placeholder: Python 3.8+, SQLite, boto3, LiteLLM, Requests]

---

## 4. LLM News Crawler Bot

### 4.1 Architecture

[Placeholder: Autonomous crawler with AI-driven navigation and extraction]

### 4.2 Crawler Engine

[Placeholder: Playwright-based browser automation with multiple execution modes]

### 4.3 AI Agent

[Placeholder: Login flow planning, crawl strategy planning, selector inference, and content extraction]

### 4.4 Authentication Handler

[Placeholder: Optional username/password authentication with platform-specific adaptation]

### 4.5 Output Generator

[Placeholder: Structured metadata, clean article text, screenshots, and raw HTML]

### 4.6 Technology Stack

[Placeholder: Python 3.8+, Playwright, FastAPI, LLM integration]

### 4.7 Integration with Core System

[Placeholder: How core system invokes crawler bot and consumes outputs]

---

## 5. MCP Server

### 5.1 Architecture

[Placeholder: FastMCP 2.0-based server providing AI-powered analysis tools]

### 5.2 Tool Categories

[Placeholder: 27 tools organized into 8 categories - Date Resolution, Data Query, RSS Query, Search, Analytics, System Management, Storage Sync, Article Reader, Notification]

### 5.3 Transport Modes

[Placeholder: stdio for local AI clients and HTTP for remote access]

### 5.4 Resource Endpoints

[Placeholder: 4 MCP resources - platforms, rss-feeds, available-dates, keywords]

### 5.5 Technology Stack

[Placeholder: Python 3.8+, FastMCP 2.0, Asyncio]

### 5.6 Integration Points

[Placeholder: Shared storage layer, configuration files, and notification module]

---

## 6. Data Flow Architecture

### 6.1 Hot List Data Flow

[Placeholder: Data flow from 11 hot list platforms through crawling, filtering, storage, to notification]

### 6.2 RSS Feed Data Flow

The RSS feed data flow handles subscription-based news sources (RSS 2.0, Atom, and JSON Feed 1.1 formats) with distinct processing logic optimized for time-based content delivery. Unlike hot list platforms that provide trending snapshots, RSS feeds deliver chronological content streams that require freshness filtering and GUID-based deduplication.

**Data Flow Diagram:**

```
┌──────────────────┐
│ RSS/Atom Sources │
│ (Configurable    │
│  feeds)          │
└────────┬─────────┘
         │
         │ HTTP GET with Feed Headers
         ▼
┌──────────────────┐
│ RSS Parser       │
│ - Detect Format  │
│ - Parse XML/JSON │
│ - Extract Fields │
└────────┬─────────┘
         │
         │ ParsedRSSItem[]
         ▼
┌──────────────────┐
│ GUID-Based       │
│ Deduplication    │
│ - Priority: GUID │
│ - Fallback: URL  │
└────────┬─────────┘
         │
         │ Unique Items
         ▼
┌──────────────────┐
│ Freshness Filter │
│ - Max Age Check  │
│ - Per-Feed Config│
│ - Preserve No-Date│
└────────┬─────────┘
         │
         │ Fresh Items
         ▼
┌──────────────────┐
│ Keyword Grouping │
│ - Same as Hotlist│
│ - Regex Support  │
│ - Display Limits │
└────────┬─────────┘
         │
         │ Grouped Items
         ▼
┌──────────────────┐
│ RSS Storage      │
│ (Separate Tables)│
│ - rss_items      │
│ - rss_feeds      │
│ - rss_crawl_*    │
└────────┬─────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Notification │  │ MCP Server   │
│ (RSS Section)│  │ RSS Tools    │
└──────────────┘  └──────────────┘
```

#### RSS/Atom Parsing and Extraction

The RSS parser (`trendradar/crawler/rss/parser.py`) supports three feed formats with automatic format detection:

**1. Format Detection and Parsing**

```python
# Format detection logic
if content.startswith("{") and "jsonfeed.org" in content:
    # JSON Feed 1.1
    items = parse_json_feed(content)
else:
    # RSS 2.0 or Atom (using feedparser library)
    feed = feedparser.parse(content)
    items = [parse_entry(entry) for entry in feed.entries]
```

**Supported Formats:**
- **RSS 2.0**: Standard XML-based syndication format
- **Atom**: Modern XML-based alternative to RSS
- **JSON Feed 1.1**: JSON-based feed format (https://jsonfeed.org/)

**2. Field Extraction**

The parser extracts the following fields from each feed entry:

| Field | RSS 2.0 | Atom | JSON Feed | Priority |
|-------|---------|------|-----------|----------|
| **Title** | `<title>` | `<title>` | `title` | Required |
| **URL** | `<link>` | `<link rel="alternate">` | `url` or `external_url` | Required |
| **GUID** | `<guid>` | `<id>` | `id` | High (for deduplication) |
| **Published Date** | `<pubDate>` | `<published>` or `<updated>` | `date_published` or `date_modified` | Medium |
| **Summary** | `<description>` | `<summary>` or `<content>` | `summary` or `content_text` | Low |
| **Author** | `<author>` or `<dc:creator>` | `<author><name>` | `authors[].name` | Low |

**3. Content Cleaning**

All extracted text undergoes cleaning:
- HTML entity decoding (`&amp;` → `&`, `&lt;` → `<`)
- HTML tag removal (`<p>...</p>` → `...`)
- Whitespace normalization (multiple spaces → single space)
- Summary truncation (max 500 characters by default)

**Example Parsing Output:**

```python
ParsedRSSItem(
    title="New AI Model Achieves State-of-the-Art Results",
    url="https://example.com/article/123",
    guid="https://example.com/article/123",  # or unique ID
    published_at="2024-01-15T10:30:00+00:00",  # ISO 8601 format
    summary="Researchers announce breakthrough in natural language...",
    author="John Doe"
)
```

#### GUID-Based Deduplication

RSS feeds use a two-tier deduplication strategy to handle duplicate entries across multiple crawls:

**1. Deduplication Priority**

```sql
-- Priority 1: GUID (if present and non-empty)
CREATE UNIQUE INDEX idx_rss_guid_feed
    ON rss_items(guid, feed_id) WHERE guid != '';

-- Priority 2: URL (always present)
CREATE UNIQUE INDEX idx_rss_url_feed
    ON rss_items(url, feed_id);
```

**2. Deduplication Logic**

When saving an RSS item to the database:

```python
# Step 1: Check for existing item by GUID (if GUID exists)
if item.guid:
    existing = db.query("SELECT id FROM rss_items WHERE guid = ? AND feed_id = ?",
                       (item.guid, feed_id))

# Step 2: Fallback to URL check (if GUID not found or empty)
if not existing and item.url:
    existing = db.query("SELECT id FROM rss_items WHERE url = ? AND feed_id = ?",
                       (item.url, feed_id))

# Step 3: Insert or update
if existing:
    # Update: increment crawl_count, update last_crawl_time
    db.execute("UPDATE rss_items SET crawl_count = crawl_count + 1, ...")
else:
    # Insert: new item
    db.execute("INSERT INTO rss_items (...) VALUES (...)")
```

**3. Why GUID Priority?**

- **URL Changes**: Article URLs may change due to redirects, URL shorteners, or site restructuring
- **Canonical Identification**: GUID provides stable, canonical identification across URL changes
- **Feed Standard**: RSS/Atom specifications recommend GUID/ID as the primary identifier
- **Fallback Safety**: URL-based deduplication ensures no duplicates even when GUID is missing

**Example Scenarios:**

| Scenario | GUID | URL | Deduplication Result |
|----------|------|-----|---------------------|
| First crawl | `abc123` | `https://example.com/1` | **Insert** new item |
| Second crawl (same) | `abc123` | `https://example.com/1` | **Update** (matched by GUID) |
| URL changed | `abc123` | `https://example.com/new-url` | **Update** (matched by GUID, URL updated) |
| No GUID | - | `https://example.com/2` | **Insert** (no GUID, URL unique) |
| No GUID, re-crawl | - | `https://example.com/2` | **Update** (matched by URL) |

#### Freshness Filtering and Keyword Grouping

**1. Freshness Filtering**

RSS feeds implement time-based filtering to exclude outdated articles:

**Configuration:**

```yaml
# config/config.yaml
rss:
  freshness_filter:
    enabled: true           # Global enable/disable
    max_age_days: 3         # Default: articles within 3 days

  feeds:
    - id: hacker-news
      name: Hacker News
      url: https://news.ycombinator.com/rss
      max_age_days: 1       # Override: only 1-day-old articles

    - id: tech-blog
      name: Tech Blog
      url: https://blog.example.com/feed
      max_age_days: 0       # Override: disable filtering for this feed
```

**Filtering Logic:**

```python
def filter_by_freshness(items, feed_config, global_config):
    # Determine max_age_days for this feed
    if feed_config.max_age_days is not None:
        max_days = feed_config.max_age_days  # Per-feed override
    else:
        max_days = global_config.default_max_age_days  # Global default

    # If max_days == 0, disable filtering
    if max_days == 0:
        return items

    # Filter items
    filtered = []
    for item in items:
        if not item.published_at:
            # No publish date: keep (assume fresh)
            filtered.append(item)
        elif is_within_days(item.published_at, max_days):
            # Within max_days: keep
            filtered.append(item)
        # else: too old, discard

    return filtered
```

**Freshness Check Implementation:**

```python
def is_within_days(iso_datetime: str, max_days: int, timezone: str) -> bool:
    """
    Check if ISO 8601 datetime is within specified days

    Args:
        iso_datetime: ISO format datetime (e.g., "2024-01-15T10:30:00+00:00")
        max_days: Maximum age in days
        timezone: Timezone for current time (e.g., "Asia/Shanghai")

    Returns:
        True if within max_days, False otherwise
    """
    published = datetime.fromisoformat(iso_datetime)
    now = datetime.now(pytz.timezone(timezone))
    age = now - published
    return age.days <= max_days
```

**Filtering Behavior:**

- **Articles with no publish date**: Always kept (assumed fresh)
- **Articles within max_age_days**: Kept
- **Articles older than max_age_days**: Filtered out (not pushed, but still stored in database)
- **Per-feed override**: Individual feeds can override global settings
- **Disable filtering**: Set `max_age_days: 0` to disable for specific feeds

**2. Keyword Grouping**

RSS items use the same keyword-based grouping system as hot list platforms:

**Configuration Format** (`config/frequency_words.txt`):

```
# RSS items are grouped by keywords just like hot list items
AI|人工智能|机器学习|深度学习 [10]
区块链|比特币|加密货币 [5]
```

**Grouping Process:**

```python
# 1. Match RSS items against keywords (same as hot list)
for item in rss_items:
    for keyword_group in keywords:
        if keyword_group.matches(item.title):
            grouped_items[keyword_group].append(item)

# 2. Sort within each group by published_at (newest first)
for keyword, items in grouped_items.items():
    items.sort(key=lambda x: x.published_at or "", reverse=True)

# 3. Apply display limits (e.g., [10] = max 10 items per keyword)
for keyword, items in grouped_items.items():
    if keyword.limit > 0:
        grouped_items[keyword] = items[:keyword.limit]
```

**Sorting Differences:**

| Data Source | Sort Key | Sort Order | Rationale |
|-------------|----------|------------|-----------|
| **Hot List** | `rank` or `weight` | Ascending (rank 1 first) | Trending importance |
| **RSS Feed** | `published_at` | Descending (newest first) | Chronological freshness |

#### Separate Storage Tables

RSS data is stored in dedicated tables separate from hot list data to accommodate different data models and query patterns:

**1. RSS Storage Schema**

**rss_feeds Table** (RSS source metadata):

```sql
CREATE TABLE rss_feeds (
    id TEXT PRIMARY KEY,              -- Feed ID (e.g., "hacker-news")
    name TEXT NOT NULL,               -- Display name (e.g., "Hacker News")
    feed_url TEXT DEFAULT '',         -- RSS/Atom URL
    is_active INTEGER DEFAULT 1,      -- Enabled status
    last_fetch_time TEXT,             -- Last crawl time
    last_fetch_status TEXT,           -- "success" or "failed"
    item_count INTEGER DEFAULT 0,     -- Daily item count
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**rss_items Table** (RSS article data):

```sql
CREATE TABLE rss_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,              -- Article title
    feed_id TEXT NOT NULL,            -- Source feed ID
    url TEXT NOT NULL,                -- Article URL
    guid TEXT DEFAULT '',             -- GUID/ID (for deduplication)
    published_at TEXT,                -- Publish time (ISO 8601)
    summary TEXT,                     -- Article summary
    author TEXT,                      -- Author name
    first_crawl_time TEXT NOT NULL,   -- First seen time
    last_crawl_time TEXT NOT NULL,    -- Last seen time
    crawl_count INTEGER DEFAULT 1,    -- Times crawled
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id)
);

-- Deduplication indexes
CREATE UNIQUE INDEX idx_rss_guid_feed
    ON rss_items(guid, feed_id) WHERE guid != '';  -- GUID priority

CREATE UNIQUE INDEX idx_rss_url_feed
    ON rss_items(url, feed_id);                    -- URL fallback
```

**rss_crawl_records Table** (Crawl history):

```sql
CREATE TABLE rss_crawl_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_time TEXT NOT NULL UNIQUE,  -- Crawl time (HH:MM)
    total_items INTEGER DEFAULT 0,    -- Total items crawled
    created_at TIMESTAMP
);
```

**rss_crawl_status Table** (Per-feed crawl status):

```sql
CREATE TABLE rss_crawl_status (
    crawl_record_id INTEGER NOT NULL,
    feed_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
    error_message TEXT,               -- Error details if failed
    PRIMARY KEY (crawl_record_id, feed_id),
    FOREIGN KEY (crawl_record_id) REFERENCES rss_crawl_records(id),
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id)
);
```

**rss_push_records Table** (Push and analysis tracking):

```sql
CREATE TABLE rss_push_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,        -- Date (YYYY-MM-DD)
    pushed INTEGER DEFAULT 0,         -- Push status
    push_time TEXT,                   -- Push time
    ai_analyzed INTEGER DEFAULT 0,    -- AI analysis status
    ai_analysis_time TEXT,            -- AI analysis time
    ai_analysis_mode TEXT,            -- AI analysis mode
    created_at TIMESTAMP
);
```

**2. Storage Separation Rationale**

| Aspect | Hot List Tables | RSS Tables | Reason for Separation |
|--------|----------------|------------|----------------------|
| **Primary Key** | URL + platform_id | GUID (priority) or URL + feed_id | Different deduplication strategies |
| **Time Tracking** | Rank history, title changes | Crawl count, first/last seen | Different update patterns |
| **Metadata** | Rank, hot_value, weight | Published date, author, summary | Different content attributes |
| **Query Patterns** | Trending analysis, rank tracking | Chronological retrieval, freshness filtering | Different access patterns |
| **Data Lifecycle** | Snapshot-based (daily trending) | Stream-based (continuous feed) | Different data models |

**3. Data Organization**

```
output/
├── hotlist/
│   └── 2024-01-15.db          # Hot list data (news_items, platforms, etc.)
└── rss/
    └── 2024-01-15.db          # RSS data (rss_items, rss_feeds, etc.)
```

**Benefits of Separation:**
- **Schema Independence**: Each data source can evolve its schema independently
- **Query Optimization**: Indexes and queries optimized for specific access patterns
- **Data Integrity**: Separate foreign key constraints and validation rules
- **Backup Flexibility**: Can backup/restore hot list and RSS data independently
- **Performance**: Smaller table sizes improve query performance

#### RSS Data Flow Summary

**Key Characteristics:**

1. **Multi-Format Support**: RSS 2.0, Atom, and JSON Feed 1.1 with automatic detection
2. **Robust Deduplication**: GUID-priority with URL fallback ensures no duplicates
3. **Freshness Filtering**: Configurable per-feed age limits with global defaults
4. **Keyword Grouping**: Same system as hot list with chronological sorting
5. **Separate Storage**: Dedicated tables optimized for RSS data model
6. **Incremental Updates**: Tracks crawl count and first/last seen times
7. **Error Tracking**: Per-feed success/failure status with error messages

**Data Transformation Pipeline:**

```
Raw Feed (XML/JSON)
    ↓ [Parse]
ParsedRSSItem (title, url, guid, published_at, summary, author)
    ↓ [Deduplicate by GUID/URL]
Unique Items
    ↓ [Filter by Freshness]
Fresh Items (within max_age_days)
    ↓ [Group by Keywords]
Grouped Items (by keyword, sorted by published_at)
    ↓ [Store in rss_items table]
Persisted RSS Data
    ↓ [Query for Notification/MCP]
Delivered Content
```

This RSS data flow complements the hot list data flow by providing time-based subscription content alongside trending snapshots, giving users a comprehensive view of both trending topics and chronological news streams.

### 6.3 LLM Crawler Bot Integration Flow

The LLM Crawler Bot provides advanced content extraction capabilities for scenarios that require authentication, complex navigation, or AI-powered selector inference. While the core TrendRadar system handles standard hot list and RSS crawling, the crawler bot is designed for deep content extraction from individual news articles, especially those behind login walls or with dynamic layouts.

#### 6.3.1 Integration Architecture

The crawler bot operates as an **auxiliary service** that can be invoked in three modes:

1. **CLI Mode**: Direct command-line execution for standalone crawling tasks
2. **API Mode**: FastAPI server exposing REST endpoints for programmatic integration
3. **Library Mode**: Direct Python import and function calls (future integration point for core system)

```
┌─────────────────────────────────────────────────────────────────┐
│                  LLM Crawler Bot Integration Flow                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ TrendRadar Core  │                                            │
│  │ System           │                                            │
│  │                  │                                            │
│  │ - Identifies     │                                            │
│  │   complex URLs   │                                            │
│  │ - Needs auth     │                                            │
│  │ - Needs deep     │                                            │
│  │   extraction     │                                            │
│  └────────┬─────────┘                                            │
│           │                                                       │
│           │ Invocation (CLI/API/Library)                         │
│           │ Input: URL + username + password + instruction       │
│           ▼                                                       │
│  ┌──────────────────┐                                            │
│  │ LLM Crawler Bot  │                                            │
│  │ Entry Point      │                                            │
│  └────────┬─────────┘                                            │
│           │                                                       │
│           ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AI Planning Pipeline                         │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  Step 1: Login Flow Planning                             │   │
│  │  ┌────────────────────────────────────────┐              │   │
│  │  │ - Analyze HTML for login requirements │              │   │
│  │  │ - Infer login URL and form selectors  │              │   │
│  │  │ - Plan pre-click actions               │              │   │
│  │  │ - Define success indicators            │              │   │
│  │  └────────────────────────────────────────┘              │   │
│  │           │                                               │   │
│  │           ▼                                               │   │
│  │  Step 2: Crawl Strategy Planning                         │   │
│  │  ┌────────────────────────────────────────┐              │   │
│  │  │ - Decompose user instruction           │              │   │
│  │  │ - Determine search vs direct approach  │              │   │
│  │  │ - Plan navigation sequences            │              │   │
│  │  │ - Identify target content types        │              │   │
│  │  └────────────────────────────────────────┘              │   │
│  │           │                                               │   │
│  │           ▼                                               │   │
│  │  Step 3: Selector Inference                              │   │
│  │  ┌────────────────────────────────────────┐              │   │
│  │  │ - Analyze HTML structure               │              │   │
│  │  │ - Infer content selectors              │              │   │
│  │  │ - Adapt to platform patterns           │              │   │
│  │  │ - Generate CSS/XPath selectors         │              │   │
│  │  └────────────────────────────────────────┘              │   │
│  │           │                                               │   │
│  │           ▼                                               │   │
│  │  Step 4: Content Extraction                              │   │
│  │  ┌────────────────────────────────────────┐              │   │
│  │  │ - Extract article metadata             │              │   │
│  │  │ - Clean and structure content          │              │   │
│  │  │ - Generate summaries and tags          │              │   │
│  │  │ - Detect language and sentiment        │              │   │
│  │  └────────────────────────────────────────┘              │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│           │                                                       │
│           ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Browser Automation (Playwright)                 │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  - Launch browser (Chromium/Chrome/CDP)                  │   │
│  │  - Navigate to URL                                       │   │
│  │  - Execute login flow (if required)                      │   │
│  │  - Wait for page load and dynamic content               │   │
│  │  - Execute search/navigation (if needed)                 │   │
│  │  - Capture screenshot                                    │   │
│  │  - Extract HTML                                          │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│           │                                                       │
│           ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Output Generation                            │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  output/<job_id>/                                        │   │
│  │  ├── metadata.json      (structured metadata)            │   │
│  │  ├── article.txt        (clean article text)             │   │
│  │  ├── screenshot.png     (full-page screenshot)           │   │
│  │  └── page.html          (raw HTML)                       │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│           │                                                       │
│           │ Output: CrawlResult with metadata + file paths       │
│           ▼                                                       │
│  ┌──────────────────┐                                            │
│  │ TrendRadar Core  │                                            │
│  │ System           │                                            │
│  │                  │                                            │
│  │ - Parse metadata │                                            │
│  │ - Extract content│                                            │
│  │ - Integrate into │                                            │
│  │   data pipeline  │                                            │
│  │ - Store in DB    │                                            │
│  └──────────────────┘                                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.3.2 Invocation Methods

**1. CLI Mode (Command-Line Interface)**

The core system can invoke the crawler bot as a subprocess using the CLI interface:

```bash
python -m news_crawler_bot.cli \
  --url "https://example.com/news/article" \
  --username "user@example.com" \
  --password "secret" \
  --job-id "custom-job-id"
```

**Input Parameters:**
- `--url`: Target news article URL (required)
- `--username`: Login username/email (optional)
- `--password`: Login password (optional)
- `--job-id`: Custom job identifier for stable output directory naming (optional)
- `--verbose`: Enable debug logging (optional)

**Output:** JSON result printed to stdout containing job status, output paths, and metadata.

**2. API Mode (REST API)**

The crawler bot can run as a FastAPI server, allowing the core system to make HTTP requests:

```bash
# Start the API server
python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
```

**API Endpoints:**

- `POST /api/crawl`: Synchronous crawl (blocks until completion)
  ```json
  {
    "url": "https://example.com/news/article",
    "username": "user@example.com",
    "password": "secret",
    "instruction": "Extract the main article content",
    "browser_mode": "auto",
    "headless": true
  }
  ```

- `POST /api/jobs`: Asynchronous crawl (returns job_id immediately)
- `GET /api/jobs/{job_id}`: Check job status and retrieve results
- `POST /api/jobs/{job_id}/stop`: Stop a running job
- `POST /api/plan`: Preview crawl plan without execution

**3. Library Mode (Direct Import)**

For tighter integration, the core system can import and use the crawler bot directly:

```python
from news_crawler_bot.crawler import NewsCrawlerBot

bot = NewsCrawlerBot()
result = await bot.crawl(
    url="https://example.com/news/article",
    username="user@example.com",
    password="secret",
    instruction="Extract the main article content"
)
```

#### 6.3.3 AI Planning and Extraction Pipeline

The crawler bot uses a multi-stage AI planning pipeline to intelligently navigate and extract content:

**Stage 1: Login Flow Planning** (`plan_login`)

When authentication is required, the AI agent analyzes the page HTML to:
- Detect if login is required before content access
- Infer the login URL (may differ from article URL)
- Identify CSS selectors for username, password, and submit button fields
- Plan pre-click actions (e.g., clicking "Sign In" button to reveal form)
- Define success indicators to verify successful login

**AI Model Used:** Configurable via 9Router or OpenAI-compatible endpoints (default: Gemini 3.1 Pro)

**Example Login Plan:**
```json
{
  "requires_login": true,
  "login_url": "https://example.com/login",
  "pre_click_selector": "button.sign-in",
  "username_selector": "input[name='email']",
  "password_selector": "input[type='password']",
  "submit_selector": "button[type='submit']",
  "success_indicator_selector": ".user-profile",
  "reasoning": "Page shows login form with email/password fields"
}
```

**Stage 2: Crawl Strategy Planning** (`plan_crawl`)

The AI agent decomposes the user's instruction into an executable crawl plan:
- Determines if search is needed before extraction
- Identifies navigation URLs for specific pages/groups/categories
- Extracts search queries from natural language instructions
- Determines target count (number of items to collect)
- Identifies target type (article, video, post, profile, product, etc.)
- Decides whether to open each result individually
- Infers platform hints (YouTube, Facebook, Instagram, generic, etc.)

**Example Crawl Plan:**
```json
{
  "needs_search": true,
  "navigation_url": null,
  "search_query": "artificial intelligence news",
  "target_count": 5,
  "target_type": "article",
  "open_each_result": true,
  "platform_hint": "generic",
  "search_box_selector": "input[name='q']",
  "result_link_selector": "a.article-link",
  "reasoning": "User wants 5 AI news articles, requires search"
}
```

**Stage 3: Selector Inference** (`select_targets_from_html`)

After navigation or search, the AI agent analyzes the current page HTML to:
- Identify target URLs matching the requested content type
- Generate CSS selectors for result links
- Order targets by relevance and position
- Filter out navigation, footer, and unrelated links
- Adapt to platform-specific patterns (YouTube videos, Facebook posts, etc.)

**Example Target Selection:**
```json
{
  "target_urls": [
    "https://example.com/news/ai-breakthrough-2024",
    "https://example.com/news/machine-learning-trends",
    "https://example.com/news/neural-networks-explained"
  ],
  "result_link_selector": "article.news-item > a.title",
  "should_open_each": true,
  "reasoning": "Found 3 relevant AI news articles in search results"
}
```

**Stage 4: Content Extraction** (`extract_article`)

For each target page, the AI agent performs deep content extraction:

**Metadata Extraction Priority:**
1. **JSON-LD/Schema.org fields**: headline, author, publisher, datePublished, dateModified, articleSection, keywords
2. **OpenGraph/Twitter meta tags**: og:title, article:author, article:published_time, article:section, article:tag
3. **Semantic HTML**: `<h1>`, byline, `<time datetime>`, itemprop attributes, breadcrumbs
4. **Visible page text**: Inferred from visible content as fallback

**Content Cleaning:**
- Removes boilerplate: navigation, sidebars, ads, cookie banners, comments, footers
- Preserves main article text with proper paragraph breaks
- Extracts tables, lists, and structured data
- Maintains original language

**Output Schema:**
```json
{
  "source_url": "https://example.com/news/article",
  "final_url": "https://example.com/news/article?utm_source=...",
  "title": "AI Breakthrough: New Model Achieves Human-Level Performance",
  "author": "Jane Smith",
  "published_at": "2024-01-15T10:30:00Z",
  "category": "Technology",
  "summary": "Researchers announce a new AI model that achieves human-level performance on complex reasoning tasks.",
  "tags": ["AI", "Machine Learning", "Research"],
  "content": "Full article text with proper formatting...",
  "language": "en",
  "screenshot_path": "output/job-123/screenshot.png"
}
```

#### 6.3.4 Browser Automation Execution

The crawler bot uses **Playwright** for browser automation with multiple execution modes:

**Browser Modes:**

1. **Bundled Chromium** (Default): Uses Playwright's bundled Chromium browser
   - Pros: No external dependencies, consistent behavior
   - Cons: No session persistence across runs

2. **System Chrome**: Uses installed Chrome/Chromium browser
   - Pros: Can leverage existing browser profiles
   - Cons: Requires Chrome installation

3. **CDP (Chrome DevTools Protocol)**: Connects to a running Chrome instance
   - Pros: Session persistence, manual login support, debugging
   - Cons: Requires manual Chrome setup with `--remote-debugging-port=9222`

4. **Auto Mode**: Automatically selects the best browser mode based on URL and requirements

**Execution Flow:**

1. **Browser Launch**: Start browser in headless or headed mode
2. **Navigation**: Navigate to target URL with timeout handling
3. **Login Execution** (if required):
   - Navigate to login URL
   - Execute pre-click actions
   - Fill username and password fields
   - Submit form
   - Wait for success indicator
4. **Search Execution** (if needed):
   - Locate search box using inferred selector
   - Enter search query
   - Submit search
   - Wait for results page load
5. **Target Selection**:
   - Extract target URLs from results page
   - Open each target URL individually (if `open_each_result=true`)
6. **Content Capture**:
   - Wait for page load and dynamic content rendering
   - Capture full-page screenshot (PNG)
   - Extract complete HTML
7. **AI Extraction**: Send HTML to AI agent for content extraction
8. **Output Generation**: Write metadata.json, article.txt, screenshot.png, page.html

#### 6.3.5 Output Format and Consumption

The crawler bot generates structured output in a dedicated directory for each job:

**Output Directory Structure:**
```
output/
└── <job_id>/
    ├── metadata.json       # Structured metadata (ArticleMetadata schema)
    ├── article.txt         # Clean article text (UTF-8)
    ├── screenshot.png      # Full-page screenshot
    └── page.html           # Raw HTML after login/navigation
```

**metadata.json Schema:**
```json
{
  "source_url": "string",           // Original URL
  "final_url": "string",            // Final URL after redirects
  "title": "string",                // Article title
  "author": "string | null",        // Author name
  "published_at": "string | null",  // ISO 8601 date or original format
  "category": "string | null",      // Article category/section
  "summary": "string",              // 1-3 sentence summary
  "tags": ["string"],               // Keywords/tags
  "content": "string",              // Full article text
  "language": "string | null",      // Language code (en, vi, zh, etc.)
  "screenshot_path": "string"       // Relative path to screenshot
}
```

**article.txt Format:**
- UTF-8 encoded plain text
- Proper paragraph breaks (double newlines)
- No HTML tags or boilerplate
- Preserves original language
- Includes title, author, date (if available) as header

**Core System Consumption:**

The TrendRadar core system can consume crawler bot output in several ways:

1. **Parse metadata.json**: Extract structured metadata for database storage
2. **Read article.txt**: Use clean article text for AI analysis, translation, or summarization
3. **Store screenshot.png**: Archive visual evidence of article content
4. **Parse page.html**: Fallback extraction if AI extraction fails

**Integration Example:**
```python
import json
from pathlib import Path

# After invoking crawler bot via CLI/API/library
job_id = "job-123"
output_dir = Path(f"output/{job_id}")

# Load metadata
metadata_path = output_dir / "metadata.json"
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

# Extract fields for database
news_item = {
    "title": metadata["title"],
    "url": metadata["final_url"],
    "author": metadata.get("author"),
    "published_at": metadata.get("published_at"),
    "category": metadata.get("category"),
    "summary": metadata["summary"],
    "tags": metadata["tags"],
    "content": metadata["content"],
    "language": metadata.get("language"),
    "screenshot_path": str(output_dir / "screenshot.png")
}

# Store in TrendRadar database
storage_manager.save_news_item(news_item)

# Optional: Perform AI analysis on extracted content
ai_analysis = ai_analyzer.analyze(metadata["content"])
```

#### 6.3.6 Configuration and AI Model Integration

**Environment Variables:**
```env
# AI Model Configuration (shared with core system)
ROUTER_BASE_URL=http://127.0.0.1:20128/v1
ROUTER_API_KEY=sk-...
ROUTER_MODEL=openai/gh/gemini-3.1-pro-preview

# Browser Configuration
AUTO_CDP_FIRST_RUN_WAIT_SECONDS=30  # Wait time for manual login in CDP mode

# Output Configuration
OUTPUT_DIR=./output  # Output directory for crawl results
```

**AI Model Providers:**
- Default: Gemini 3.1 Pro via 9Router (cost-effective, high quality)
- Alternatives: OpenAI GPT-4, Anthropic Claude, DeepSeek, local models
- Configuration: Compatible with any OpenAI-compatible API endpoint

**Prompt Engineering:**
- Modular prompts for each AI task (login planning, crawl planning, selector inference, content extraction)
- Context-aware prompt construction with HTML samples
- Platform-specific hints and examples (YouTube, Facebook, Instagram, etc.)
- Error recovery strategies with fallback to heuristic extraction

#### 6.3.7 Error Handling and Fallback Mechanisms

**Login Failures:**
- If AI login planning fails, continue without login
- If login execution fails, retry with alternative selectors
- If authentication is impossible, extract public content only

**Selector Inference Failures:**
- Fallback to heuristic HTML parsing (BeautifulSoup)
- Use common selector patterns (article, main, .content, #article)
- Extract visible text as last resort

**Content Extraction Failures:**
- Fallback to heuristic article text extraction
- Use page title as article title
- Generate summary from first 350 characters
- Preserve raw HTML for manual review

**Browser Automation Failures:**
- Retry navigation with increased timeout
- Switch browser mode (bundled → chrome → CDP)
- Capture partial results (screenshot + HTML) even if extraction fails

#### 6.3.8 Use Cases and Integration Scenarios

**Use Case 1: Authenticated News Sites**
- Core system identifies news URL requiring login
- Invokes crawler bot with username/password
- Bot performs AI-driven login and extraction
- Core system receives clean article content

**Use Case 2: Dynamic Content Extraction**
- Core system encounters JavaScript-heavy news site
- Invokes crawler bot for browser-based rendering
- Bot waits for dynamic content load and extracts
- Core system receives fully rendered content

**Use Case 3: Multi-Article Collection**
- Core system needs multiple articles on a topic
- Invokes crawler bot with search instruction
- Bot performs search, opens each result, extracts content
- Core system receives multiple article metadata files

**Use Case 4: Platform-Specific Extraction**
- Core system needs content from YouTube, Facebook, Instagram
- Invokes crawler bot with platform-specific URL
- Bot uses platform hints for optimized extraction
- Core system receives structured metadata adapted to platform

**Current Integration Status:**
- Crawler bot is **fully functional** as standalone CLI/API service
- Core system integration is **planned** but not yet implemented
- Integration will use API mode for loose coupling and scalability
- Future enhancement: Direct library import for tighter integration

---

**Key Takeaways:**

1. **AI-Driven Intelligence**: The crawler bot uses LLMs at every stage (login planning, crawl strategy, selector inference, content extraction) to adapt to diverse website structures
2. **Flexible Invocation**: Supports CLI, API, and library modes for different integration scenarios
3. **Structured Output**: Generates consistent JSON metadata, clean text, screenshots, and raw HTML for downstream consumption
4. **Robust Error Handling**: Multiple fallback mechanisms ensure partial results even when AI extraction fails
5. **Platform Adaptability**: Handles diverse platforms (news sites, social media, video platforms) with platform-specific optimizations
6. **Authentication Support**: Optional username/password authentication with AI-driven login flow planning
7. **Browser Automation**: Playwright-based automation with multiple browser modes (bundled, system, CDP) for different deployment scenarios

### 6.4 Storage to Notification Flow

The storage to notification flow represents the final stage of the TrendRadar pipeline, transforming stored news data into formatted reports and delivering them through multiple notification channels. This process involves querying data from storage, generating reports, optionally enriching with AI analysis, adapting formats for different channels, and handling batch sending for size-limited platforms.

#### 6.4.1 Flow Overview

```
┌──────────────────┐
│ SQLite Storage   │
│ - Hot List DB    │
│ - RSS DB         │
│ - AI Filter DB   │
└────────┬─────────┘
         │
         │ Query by Date/Mode
         ▼
┌──────────────────┐
│ Data Loader      │
│ - read_today_    │
│   titles()       │
│ - get_rss_data() │
│ - detect_new_    │
│   titles()       │
└────────┬─────────┘
         │
         │ Raw Data
         ▼
┌──────────────────┐
│ Report Generator │
│ - prepare_report │
│   _data()        │
│ - count_         │
│   frequency()    │
│ - filter by mode │
└────────┬─────────┘
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│ AI Analysis      │          │ Format Adapter   │
│ (Optional)       │          │ - Markdown       │
│ - Sentiment      │          │ - HTML           │
│ - Trends         │          │ - Plain Text     │
│ - Summarization  │          │ - JSON           │
└────────┬─────────┘          └────────┬─────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
                ┌──────────────────┐
                │ Notification     │
                │ Dispatcher       │
                │ - Multi-account  │
                │ - Batch sending  │
                └────────┬─────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │ Delivery Channels (9)         │
         │ - Feishu, DingTalk, WeWork    │
         │ - Telegram, Email, ntfy       │
         │ - Bark, Slack, Webhook        │
         └───────────────────────────────┘
```

#### 6.4.2 Query and Data Loading Process

The data loading process retrieves news data from SQLite storage based on the configured report mode and applies initial filtering.

**Data Loading Methods**:

1. **Hot List Data Loading** (`read_today_titles()`):
   ```python
   # Load all titles for current day, filtered by monitored platforms
   all_results, id_to_name, title_info = ctx.read_today_titles(
       platform_ids=current_platform_ids,
       quiet=False
   )
   # Returns:
   # - all_results: {platform_id: {title: title_data}}
   # - id_to_name: {platform_id: platform_name}
   # - title_info: {platform_id: {title: {first_time, last_time, count, ranks, url}}}
   ```

2. **RSS Data Loading** (`get_rss_data()`):
   ```python
   # Load RSS data based on mode
   if mode == "current":
       rss_data = storage_manager.get_latest_rss_data(date)
   else:
       rss_data = storage_manager.get_rss_data(date)
   ```

3. **New Title Detection** (`detect_new_titles()`):
   ```python
   # Detect titles that appeared in current crawl but not in previous crawls
   new_titles = ctx.detect_new_titles(platform_ids, quiet=False)
   # Returns: {platform_id: {title: title_data}}
   ```

**Mode-Specific Data Filtering**:

- **Daily Mode** (`mode="daily"`): Loads all titles from the entire day
- **Current Mode** (`mode="current"`): Filters to only the latest crawl batch
- **Incremental Mode** (`mode="incremental"`): Focuses on newly detected titles

**Query Optimization**:
- Date-based database selection: `output/hotlist/YYYY-MM-DD.db`
- Platform filtering at query time to reduce memory usage
- Index-based lookups for fast retrieval
- Lazy loading of title metadata (ranks, URLs) only when needed

#### 6.4.3 Report Generation Process

The report generator transforms raw data into structured report data suitable for rendering and notification.

**Report Data Preparation** (`prepare_report_data()`):

```python
def prepare_report_data(
    stats: List[Dict],           # Keyword/platform statistics
    failed_ids: List,            # Failed platform IDs
    new_titles: Dict,            # New titles by platform
    id_to_name: Dict,            # Platform ID to name mapping
    mode: str,                   # Report mode (daily/current/incremental)
    rank_threshold: int,         # Rank threshold for highlighting
    matches_word_groups_func,    # Keyword matching function
    load_frequency_words_func,   # Frequency words loader
    show_new_section: bool,      # Whether to show new titles section
) -> Dict
```

**Report Data Structure**:
```python
{
    "stats": [                   # Keyword/platform statistics
        {
            "word": "AI",        # Keyword or platform name
            "count": 15,         # Number of matching titles
            "percentage": 12.5,  # Percentage of total
            "titles": [          # Matching titles
                {
                    "title": "...",
                    "source_name": "Zhihu",
                    "time_display": "08:00-12:00",
                    "count": 3,
                    "ranks": [1, 2, 3],
                    "rank_threshold": 3,
                    "url": "https://...",
                    "mobile_url": "https://...",
                    "is_new": False,
                    "rank_timeline": [(1, "08:00"), (2, "10:00")]
                }
            ]
        }
    ],
    "new_titles": [              # New titles by platform
        {
            "source_id": "zhihu",
            "source_name": "Zhihu",
            "titles": [...]
        }
    ],
    "failed_ids": ["platform1"], # Failed platforms
    "total_new_count": 25,       # Total new titles count
    "id_to_name": {...}          # Platform mapping
}
```

**Frequency Counting** (`count_frequency()`):

The frequency counting process analyzes titles and groups them by keywords or platforms:

1. **Keyword Matching Mode**:
   - Loads keyword groups from `frequency_words.txt`
   - Applies regex patterns for advanced matching
   - Filters by global exclusion keywords
   - Sorts by weight or position based on configuration
   - Limits display count per keyword

2. **AI Filtering Mode**:
   - Uses AI-powered interest-based filtering
   - Extracts tags from natural language descriptions
   - Scores titles against extracted tags
   - Falls back to keyword matching if AI fails

3. **Platform Display Mode**:
   - Groups titles by source platform instead of keywords
   - Applies weight-based sorting
   - Converts keyword stats to platform stats

**HTML Report Generation** (`generate_html_report()`):

```python
# Generate HTML report with multiple output locations
html_file = generate_html_report(
    stats=stats,
    total_titles=total_titles,
    failed_ids=failed_ids,
    new_titles=new_titles,
    id_to_name=id_to_name,
    mode=mode,
    update_info=update_info,
    rank_threshold=rank_threshold,
    output_dir="output",
    date_folder="2024-01-15",
    time_filename="08-00-00",
    render_html_func=ctx.render_html,
    report_metadata={
        "hotlist_total": 150,
        "platform_total": 11,
        "rss_matched_count": 25,
        "rss_total_count": 100,
        "rss_source_total": 5,
        "rss_source_failed": 0
    }
)

# Output locations:
# 1. output/html/2024-01-15/08-00-00.html (timestamped snapshot)
# 2. output/html/latest/daily.html (latest report by mode)
# 3. output/index.html (Docker volume access)
# 4. index.html (GitHub Pages root)
```

#### 6.4.4 AI Analysis Integration (Optional)

AI analysis can be optionally integrated into the notification flow to provide deeper insights and summaries.

**AI Analysis Trigger Conditions**:

```python
# AI analysis is triggered when:
# 1. AI_ANALYSIS.ENABLED = true in config
# 2. Schedule allows analysis (schedule.analyze = true)
# 3. Not already analyzed today (if once_analyze = true)

if analysis_config.get("ENABLED", False) and schedule.analyze:
    if schedule.once_analyze and schedule.period_key:
        if not scheduler.already_executed(schedule.period_key, "analyze", date_str):
            ai_analysis = _run_ai_analysis(...)
```

**AI Analysis Modes**:

The AI analysis can operate in different modes independent of the report mode:

1. **Follow Report Mode** (`MODE: "follow_report"`):
   - Uses the same data as the notification report
   - Analyzes daily/current/incremental data based on report mode

2. **Independent Mode** (`MODE: "daily"/"current"/"incremental"`):
   - Prepares separate data for AI analysis
   - Allows daily analysis even when sending incremental reports
   - Example: Send incremental updates but analyze full day trends

**AI Analysis Dimensions**:

```python
ai_analysis = AIAnalysisResult(
    success=True,
    core_trends="...",           # Dominant topics and evolution
    sentiment_controversy="...", # Sentiment distribution and controversies
    signals_anomalies="...",     # Sudden spikes and weak signals
    outlook_strategy="...",      # Predictions and recommendations
    standalone_summaries=[...],  # Per-topic summaries
    ai_mode="daily",             # Mode used for analysis
    error=None
)
```

**AI Analysis Data Preparation**:

```python
# Prepare data for AI analysis based on mode
ai_stats, ai_id_to_name = _prepare_ai_analysis_data(
    ai_mode="daily",
    current_results=current_crawl_results,
    current_id_to_name=id_to_name
)

# Extract metadata for AI context
platforms = list(ai_id_to_name.values())
keywords = [s.get("word", "") for s in ai_stats if s.get("word")]

# Run analysis
result = analyzer.analyze(
    stats=ai_stats,
    rss_stats=rss_items,
    report_mode=ai_mode,
    report_type=ai_report_type,
    platforms=platforms,
    keywords=keywords,
    standalone_data=standalone_data
)
```

**AI Analysis Integration Points**:

- **HTML Reports**: AI analysis embedded in HTML as expandable sections
- **Email Notifications**: AI insights included in email body
- **Webhook Notifications**: AI analysis available in JSON payload
- **Markdown Notifications**: AI summary formatted as Markdown sections

#### 6.4.5 Format Adaptation Per Channel

Different notification channels require different message formats. The system automatically adapts content based on channel capabilities.

**Format Types**:

1. **Markdown** (Feishu, DingTalk, WeWork, Telegram, ntfy, Bark, Slack):
   - Rich formatting with headers, bold, links
   - Emoji support for visual appeal
   - Code blocks for structured data
   - Nested lists for hierarchical content

2. **HTML** (Email):
   - Full HTML with CSS styling
   - Responsive design for mobile/desktop
   - Interactive elements (collapsible sections)
   - Embedded images and charts

3. **Plain Text** (Fallback):
   - Simple text formatting
   - ASCII art for structure
   - URL-only links (no anchor text)

4. **JSON** (Generic Webhook):
   - Structured data payload
   - Customizable template support
   - Full metadata preservation

**Format Adaptation Process**:

```python
# Notification dispatcher handles format adaptation
dispatcher = NotificationDispatcher(
    config=config,
    get_time_func=ctx.get_time,
    split_content_func=ctx.split_content,
    translator=translator
)

# Dispatch to all configured channels
results = dispatcher.dispatch_all(
    report_data=report_data,
    report_type="Daily Summary",
    update_info=update_info,
    proxy_url=proxy_url,
    mode="daily",
    html_file_path=html_file,
    rss_items=rss_items,
    rss_new_items=rss_new_items,
    ai_analysis=ai_analysis,
    standalone_data=standalone_data,
    skip_translation=False
)
```

**Channel-Specific Formatting**:

- **Feishu**: Markdown with card layout, supports interactive buttons
- **DingTalk**: Markdown with @ mentions, supports action cards
- **WeWork**: Markdown or plain text based on `WEWORK_MSG_TYPE` config
- **Telegram**: Markdown with inline links, supports HTML mode
- **Email**: Full HTML with embedded CSS, responsive layout
- **ntfy**: Markdown with priority levels and tags
- **Bark**: URL-encoded plain text with custom sounds
- **Slack**: Markdown with blocks API, supports attachments
- **Generic Webhook**: JSON payload with customizable template

**Display Region Filtering**:

The system supports selective display of content regions per channel:

```python
display_regions = config.get("DISPLAY", {}).get("REGIONS", {})
# {
#     "HOTLIST": True,        # Show hot list statistics
#     "RSS": True,            # Show RSS statistics
#     "NEW_ITEMS": True,      # Show new items section
#     "AI_ANALYSIS": True,    # Show AI analysis
#     "STANDALONE": False     # Show standalone display area
# }

# Apply filtering before sending
report_data, rss_items, rss_new_items, ai_analysis, standalone_data = \
    _apply_display_regions(report_data, display_regions, ...)
```

#### 6.4.6 Batch Sending and Multi-Account Support

To handle message size limits and support multiple notification accounts, the system implements batch sending and multi-account distribution.

**Batch Sending Mechanism**:

```python
# Split large content into batches based on channel limits
def send_to_feishu(
    webhook_url: str,
    report_data: Dict,
    batch_size: int = 29000,      # Feishu limit: ~30KB
    batch_interval: float = 1.0,   # Delay between batches
    split_content_func: Callable,
    ...
):
    # Render full content
    full_content = render_markdown(report_data, ...)
    
    # Split into batches if exceeds limit
    if len(full_content) > batch_size:
        batches = split_content_func(full_content, batch_size)
        
        for i, batch in enumerate(batches):
            # Send batch with header
            header = f"📊 Report (Part {i+1}/{len(batches)})"
            send_batch(webhook_url, header + batch)
            
            # Wait between batches to avoid rate limiting
            if i < len(batches) - 1:
                time.sleep(batch_interval)
    else:
        send_batch(webhook_url, full_content)
```

**Batch Size Limits by Channel**:

| Channel | Batch Size | Configurable |
|---------|-----------|--------------|
| Feishu | 29,000 chars | `FEISHU_BATCH_SIZE` |
| DingTalk | 20,000 chars | `DINGTALK_BATCH_SIZE` |
| WeWork | 4,000 chars | `MESSAGE_BATCH_SIZE` |
| Telegram | 4,000 chars | `MESSAGE_BATCH_SIZE` |
| ntfy | 3,800 chars | Fixed |
| Bark | 3,600 chars | `BARK_BATCH_SIZE` |
| Slack | 4,000 chars | `SLACK_BATCH_SIZE` |
| Email | No limit | N/A |
| Webhook | No limit | N/A |

**Multi-Account Support**:

The system supports sending to multiple accounts per channel using semicolon-separated configuration:

```yaml
# config.yaml
FEISHU_WEBHOOK_URL: "https://webhook1.feishu.cn/...;https://webhook2.feishu.cn/..."
TELEGRAM_BOT_TOKEN: "token1;token2;token3"
TELEGRAM_CHAT_ID: "chat1;chat2;chat3"
NTFY_TOPIC: "topic1;topic2"
NTFY_TOKEN: "token1;token2"  # Optional, must match topic count
```

**Multi-Account Processing**:

```python
def _send_to_multi_accounts(
    channel_name: str,
    config_value: str,
    send_func: Callable,
    **kwargs
) -> bool:
    # Parse semicolon-separated accounts
    accounts = parse_multi_account_config(config_value)
    
    # Limit to max accounts (default: 3)
    accounts = limit_accounts(accounts, max_accounts, channel_name)
    
    # Send to each account
    results = []
    for i, account in enumerate(accounts):
        account_label = f"Account {i+1}" if len(accounts) > 1 else ""
        result = send_func(account, account_label=account_label, **kwargs)
        results.append(result)
    
    # Return True if any account succeeded
    return any(results)
```

**Paired Configuration Validation**:

For channels requiring multiple configuration values (e.g., Telegram needs both token and chat_id), the system validates pairing:

```python
# Validate Telegram configuration
telegram_tokens = parse_multi_account_config(config["TELEGRAM_BOT_TOKEN"])
telegram_chat_ids = parse_multi_account_config(config["TELEGRAM_CHAT_ID"])

valid, count = validate_paired_configs(
    {"bot_token": telegram_tokens, "chat_id": telegram_chat_ids},
    "Telegram",
    required_keys=["bot_token", "chat_id"]
)

if not valid or count == 0:
    print("❌ Telegram configuration error: token and chat_id count mismatch")
    return False
```

**Account Limit Configuration**:

```yaml
# config.yaml
MAX_ACCOUNTS_PER_CHANNEL: 3  # Maximum accounts per channel (default: 3)
BATCH_SEND_INTERVAL: 1.0     # Delay between batches in seconds
```

**Error Handling**:

- Individual account failures don't block other accounts
- Retry logic for transient network errors
- Detailed logging with account labels for debugging
- Success if any account succeeds (partial success model)

#### 6.4.7 Translation Integration

The notification flow supports automatic translation of content before sending:

```python
# Translate content based on scope configuration
report_data, rss_items, rss_new_items, standalone_data = \
    dispatcher.translate_content(
        report_data=report_data,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        standalone_data=standalone_data,
        display_regions=display_regions,
        skip_rss=False  # Set to True if RSS already translated upstream
    )
```

**Translation Scope**:
- `HOTLIST`: Translate hot list titles
- `RSS`: Translate RSS feed titles
- `STANDALONE`: Translate standalone display area
- Respects `display_regions` to skip hidden sections

**Translation Optimization**:
- Batch translation to reduce API calls
- Skip already-translated content
- Preserve original text alongside translation
- Empty translation protection (keeps original if translation fails)

#### 6.4.8 Notification Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Storage to Notification Flow              │
└─────────────────────────────────────────────────────────────┘

1. Query Phase
   ┌──────────────┐
   │ SQLite DB    │
   │ - Hot List   │
   │ - RSS        │
   │ - AI Filter  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Load Data    │
   │ - By mode    │
   │ - By date    │
   │ - Filter     │
   └──────┬───────┘

2. Report Generation Phase
          │
          ▼
   ┌──────────────┐
   │ Prepare      │
   │ Report Data  │
   │ - Stats      │
   │ - New titles │
   └──────┬───────┘
          │
          ├─────────────────┐
          │                 │
          ▼                 ▼
   ┌──────────────┐  ┌──────────────┐
   │ AI Analysis  │  │ HTML Report  │
   │ (Optional)   │  │ Generation   │
   └──────┬───────┘  └──────┬───────┘
          │                 │
          └────────┬────────┘

3. Format Adaptation Phase
                   │
                   ▼
          ┌──────────────┐
          │ Translation  │
          │ (Optional)   │
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ Format       │
          │ Adapter      │
          │ - Markdown   │
          │ - HTML       │
          │ - JSON       │
          └──────┬───────┘

4. Dispatch Phase
                 │
                 ▼
          ┌──────────────┐
          │ Multi-Account│
          │ Dispatcher   │
          └──────┬───────┘
                 │
                 ├──────────────────────────────┐
                 │                              │
                 ▼                              ▼
          ┌──────────────┐            ┌──────────────┐
          │ Batch        │            │ Send to      │
          │ Splitter     │            │ Channels     │
          │ (if needed)  │            │ (9 types)    │
          └──────┬───────┘            └──────┬───────┘
                 │                           │
                 └───────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────┐
                  │ Delivery Results │
                  │ - Success/Fail   │
                  │ - Per account    │
                  └──────────────────┘
```

**Key Features**:

1. **Flexible Querying**: Supports multiple modes (daily/current/incremental) with efficient filtering
2. **Rich Report Generation**: Combines hot list, RSS, new titles, and AI analysis
3. **Optional AI Enhancement**: Deep insights and summaries when enabled
4. **Smart Format Adaptation**: Automatic conversion to channel-specific formats
5. **Batch Handling**: Splits large messages to respect channel limits
6. **Multi-Account Distribution**: Sends to multiple accounts per channel
7. **Translation Support**: Automatic translation with scope control
8. **Robust Error Handling**: Partial success model with detailed logging
9. **HTML Archiving**: Multiple output locations for different access patterns
10. **Configurable Display**: Selective region display per channel

This comprehensive flow ensures that news data stored in SQLite is efficiently transformed and delivered to users through their preferred notification channels with appropriate formatting and optional AI-powered insights.

---

## 7. AI Mechanisms

### 7.1 AI-Powered Smart Filtering

[Placeholder: Natural language interest descriptions, tag extraction, scoring, and fallback mechanisms]

### 7.2 AI Analysis and Summarization

[Placeholder: Four analysis dimensions - core trends, sentiment, signals, and outlook]

### 7.3 AI Translation

[Placeholder: Batch translation architecture, bilingual output, and token optimization]

### 7.4 LLM Crawler Bot AI Mechanisms

[Placeholder: Login flow planning, crawl strategy planning, selector inference, and content extraction]

### 7.5 MCP Server AI Integration

[Placeholder: AI client support, natural language processing, and AI-powered features]

---

## 8. Deployment Strategies

### 8.1 GitHub Actions Deployment

[Placeholder: Serverless execution using GitHub's infrastructure with workflow configuration]

### 8.2 Docker Deployment

[Placeholder: Dual-container architecture with Docker Compose configuration]

### 8.3 Local Execution Deployment

[Placeholder: Direct Python execution with virtual environment setup and scheduling options]

### 8.4 Storage Backend Options

[Placeholder: Local SQLite and remote S3-compatible storage configuration]

### 8.5 Timeline System Configuration

[Placeholder: Unified scheduling with 5 preset templates and custom time periods]

---

## 9. Storage and Query Architecture

### 9.1 Storage Backend Architecture

[Placeholder: Multi-backend support with SQLite database structure and data organization]

### 9.2 MCP Server Query Capabilities

[Placeholder: 27 tools for querying news data, RSS feeds, and system status]

### 9.3 Data Analysis Functions

[Placeholder: Trend analysis, sentiment analysis, topic tracking, and summary reports]

### 9.4 Remote Storage Synchronization

[Placeholder: Sync mechanism between local and remote storage]

---

## 10. Notification and Output Mechanisms

### 10.1 Notification Channels

[Placeholder: 9 supported channels - Feishu, DingTalk, WeWork, Telegram, Email, ntfy, Bark, Slack, Webhook]

### 10.2 Message Formatting and Adaptation

[Placeholder: Format adaptation per channel and batch sending mechanism]

### 10.3 HTML Report and GitHub Pages Deployment

[Placeholder: HTML report generation and GitHub Pages deployment workflow]

### 10.4 Email Notification with HTML Formatting

[Placeholder: Email-specific HTML formatting and SMTP configuration]

---

## 11. Filtering and Configuration

### 11.1 Keyword-Based Filtering System

[Placeholder: frequency_words.txt format, regex pattern support, and display limits]

### 11.2 AI-Powered Interest-Based Filtering

[Placeholder: ai_interests.txt configuration and natural language interest descriptions]

### 11.3 Global Filter Keywords

[Placeholder: Global exclusion mechanism and configuration format]

---

## Appendix

### A. Glossary

[Placeholder: Definitions of key terms used throughout the document]

### B. References

[Placeholder: Links to relevant documentation, repositories, and resources]

### C. Version History

[Placeholder: Document version history and change log]

---

**End of Document**
