<div align="center">

**Chinese** | **[English](README-MCP-FAQ-EN.md)**

</div>

# TrendRadar MCP Tool Usage FAQ

> AI Prompting Guide - How to use the news trending analysis tool via natural conversation (v3.1.7)

---

## 📋 Tool Overview

| Category | Tool Name | Feature Description |
|:----:|---------|---------|
| **Date** | `resolve_date_range` | Parse natural language like "this week", "last 7 days" into standard dates |
| **Query** | `get_latest_news` | Get the latest batch of crawled trending news |
| | `get_news_by_date` | Query historical news by date range |
| | `get_trending_topics` | Get trending topic statistics (supports automatic extraction) |
| **RSS** | `get_latest_rss` | Get the latest RSS feed content |
| | `search_rss` | Search for keywords in RSS data |
| | `get_rss_feeds_status` | View RSS feed configuration and data status |
| **Search** | `search_news` | Unified search (keyword/fuzzy/entity, can include RSS) |
| | `find_related_news` | Find news similar to a specified title |
| **Analysis** | `analyze_topic_trend` | Topic trend analysis (popularity/lifecycle/viral/prediction) |
| | `analyze_data_insights` | Data insights (platform comparison/activity/keyword co-occurrence) |
| | `analyze_sentiment` | News sentiment analysis |
| | `aggregate_news` | Cross-platform news aggregation and deduplication |
| | `compare_periods` | Period comparison analysis (week-over-week/month-over-month) |
| | `generate_summary_report` | Generate daily/weekly summary reports |
| **System** | `get_current_config` | Get current system configuration |
| | `get_system_status` | Get system running status |
| | `check_version` | Check for version updates (TrendRadar + MCP Server) |
| | `trigger_crawl` | Manually trigger a crawl task |
| **Storage** | `sync_from_remote` | Pull data from remote storage to local |
| | `get_storage_status` | Get storage configuration and status |
| | `list_available_dates` | List available dates locally/remotely |
| **Article** | `read_article` | Read single article content (Markdown format) |
| | `read_articles_batch` | Batch read multiple articles (up to 5 articles) |
| **Notification** | `get_notification_channels` | Get all configured notification channels and their status |
| | `send_notification` | Send messages to configured notification channels (automatic format conversion) |

---

## ⚙️ Default Settings Explanation (Important!)

The following optimization strategies are adopted by default, mainly to save AI token consumption:

| Default Setting | Explanation | How to Adjust |
| -------------- | --------------------------------------- | ------------------------------------- |
| **Limit Count** | Returns 50 news items by default | Say "return top 10" or "give me 100" in the chat |
| **Time Range** | Queries today's data by default | Say "query yesterday", "last week", or "Jan 1 to 7" |
| **URL Links** | Does not return links by default (saves ~160 tokens/item) | Say "need links" or "include URLs" |
| **Keyword List** | Does not use frequency_words.txt to filter news by default | Only used when calling the "trending topics" tool |

**⚠️ Important:** The choice of AI model directly affects the tool invocation effect; the smarter the AI, the more accurate the invocation. When you lift the above restrictions, such as expanding from today's query to a week's query, first you must have a week's worth of data locally, and second, token consumption may double.

**💡 Tip:** This project provides a dedicated date parsing tool that can accurately parse natural language date expressions like "last 7 days" and "this week", ensuring all AI models get a consistent date range. See Q18 below for details.


## 💰 AI Models

Below I use the **[SiliconFlow](https://cloud.siliconflow.cn)** platform as an example, which has many large models to choose from. During the development and testing of this project, I used this platform for many functional tests and verifications.

### 📊 Registration Method Comparison

| Registration Method | Direct Registration without Invitation Link | Registration with Invitation Link |
|:-------:|:-------:|:-----------------:|
| Registration Link | [siliconflow.cn](https://cloud.siliconflow.cn) | [Invitation Link](https://cloud.siliconflow.cn/i/fqnyVaIU) |
| Free Quota | 0 tokens | **20 million tokens** (≈14 RMB) |
| Extra Benefits | ❌ | ✅ Inviter also gets 20 million tokens |

> 💡 **Tip**: The gifted quota above should be enough for **over 200 queries**


### 🚀 Quick Start

#### 1️⃣ Register and Get API Key

1. Use the link above to complete registration
2. Visit the [API Key Management Page](https://cloud.siliconflow.cn/me/account/ak)
3. Click "Create New API Key"
4. Copy the generated key (please keep it safe)

#### 2️⃣ Configure in Cherry Studio

1. Open **Cherry Studio**
2. Go to "Model Service" settings
3. Find "SiliconFlow"
4. Paste the copied key into the **[API Key]** input box
5. Ensure the checkbox in the upper right corner is turned on and shows **green** ✅

---

### ✨ Configuration Complete!

Now you can start using this project and enjoy stable and fast AI services!

After you test a query, please immediately go to [SiliconFlow Bills](https://cloud.siliconflow.cn/me/bills) to check the consumption for this time, so you have an estimate in mind.


---

## Basic Queries

### Q1: How to view the latest news?

**You can ask like this:**

- "Show me the latest news"
- "Query today's hot news"
- "Get the latest 10 news from Zhihu and Weibo"
- "View the latest news, including links"

**Tool Return Behavior:**

- The tool will return the latest 50 news from all platforms
- URL links are not included by default (to save tokens)

**AI Display Behavior (Important):**

- ⚠️ **AI usually summarizes automatically**, showing only some news (e.g., TOP 10-20)
- ✅ If you want to see all 50, you need to explicitly request: "Show all news" or "List all 50 completely"
- 💡 This is the natural behavior of the AI model, not a limitation of the tool

**Can be adjusted:**

- Specify platform: e.g., "Only look at Zhihu"
- Adjust quantity: e.g., "Return the top 20"
- Include links: e.g., "need links"
- **Require full display**: e.g., "show all, do not summarize"

---

### Q2: How to query news for a specific date?

**You can ask like this:**

- "Query yesterday's news"
- "Look at Zhihu news from 3 days ago"
- "What is the news on 2025-10-10"
- "News from last Monday"
- "Show me the latest news" (automatically queries today)

**Supported date formats:**

- Relative dates: today, yesterday, the day before yesterday, 3 days ago
- Days of the week: last Monday, this Wednesday, last monday
- Absolute dates: 2025-10-10, October 10

**Tool return behavior:**

- Automatically queries today when no date is specified (saves tokens)
- The tool will return 50 news items from all platforms
- Does not include URL links by default

**AI display behavior (important):**

- ⚠️ **AI usually summarizes automatically**, only displaying some news (e.g., TOP 10-20 items)
- ✅ If you want to see everything, you need to explicitly request: "show all news, do not summarize"

---

### Q3: How to view trending topic statistics?

**You can ask like this:**

- "How many times did my followed words appear today" (uses preset followed words)
- "Automatically analyze what trending topics are in today's news" (automatic extraction)
- "See what the most popular words are in the news" (automatic extraction)

**Two extraction modes:**

| Mode | Description | Example Question |
|------|------|---------|
| **Preset followed words** | Counts your pre-set followed words (based on config file, default) | "How many times did my followed words appear" |
| **Automatic extraction** | Automatically extracts high-frequency words from news titles (no preset required) | "Automatically analyze trending topics" |

---

## RSS Subscription Query

### Q4.1: How to view the latest RSS subscription content?

**You can ask like this:**

- "View the latest RSS subscription content"
- "Get the latest articles from Hacker News"
- "View the latest 20 items from all RSS feeds"
- "Get RSS subscriptions, need to include summaries"
- "Look at the RSS content from the last week" (supports multi-day queries)
- "Get articles from Hacker News for the last 7 days"

**Tool return behavior:**

- Returns today's RSS items by default (up to 50 items)
- Supports the `days` parameter to get multi-day data (1-30 days)
- Excludes summaries by default (to save tokens)
- Sorted in descending order by publish time
- Automatically deduplicates across dates (by URL)

**AI Display Behavior (Important):**

- ⚠️ **AI usually summarizes automatically**, showing only a portion of the items
- ✅ If you want to see everything, you need to explicitly request: "Show all RSS content"

**You can adjust:**

- Specify RSS source: e.g., "Only show Hacker News"
- Specify number of days: e.g., "Last 7 days", "Last week"
- Adjust quantity: e.g., "Return top 20 items"
- Include summaries: e.g., "Need summaries"

---

### Q4.2: How to search for content in RSS feeds?

**You can ask like this:**

- "Search for 'AI' related articles in RSS"
- "Search for 'machine learning' content in RSS from the last 7 days"
- "Search for 'Python' in Hacker News"

**Tool Return Behavior:**

- Searches RSS item titles using keywords
- Searches data from the last 7 days by default
- The tool will return up to 50 results

**You can adjust:**

- Specify RSS source: e.g., "Only search Hacker News"
- Adjust number of days: e.g., "Search the last 14 days"
- Include summaries: e.g., "Need summaries"

---

### Q4.3: How to check the status of RSS feeds?

**You can ask like this:**

- "Check RSS feed status"
- "How much data has RSS fetched"
- "Which RSS feeds have data"

**Returned Information:**

| Field | Description |
|------|------|
| **Available Dates** | List of dates with RSS data |
| **Total Dates** | Total number of days with data |
| **Today's Source Stats** | Data statistics for each RSS feed today |
| **Generation Time** | Status generation time |

---

## Search and Retrieval

### Q4: How to search for news containing specific keywords?

**You can ask like this:**

- "Search for news containing 'artificial intelligence'"
- "Find reports about 'Tesla price cuts'"
- "Search for news related to Elon Musk, return the top 20"
- "Find news about 'iPhone 16' from the last 7 days"
- "Find news related to 'Tesla' from January 1 to 7, 2025"
- "Find the link to the news 'iPhone 16 release'"

**Tool return behavior:**

- Uses keyword mode for searching
- Searches today's data by default
- AI will automatically convert relative times like "last 7 days" or "last week" into specific date ranges
- The tool will return up to 50 results
- Does not include URL links by default

**AI display behavior (Important):**

- ⚠️ **AI usually summarizes automatically**, displaying only partial search results
- ✅ If you want to see everything, you need to explicitly request: "Show all search results"

**Adjustable:**

- Specify time range:
  - Relative method: "Search for the last week" (AI automatically calculates dates)
  - Absolute dates: "Search from January 1 to 7, 2025"
- Specify platform: e.g., "Only search Zhihu"
- Adjust sorting: e.g., "Sort by weight"
- Include links: e.g., "Need links"

---

### Q4.4: How to search both hotlists and RSS content simultaneously?

**You can ask like this:**

- "Search for 'AI' related content, including RSS"
- "Find news about 'Artificial Intelligence', and search RSS feeds at the same time"
- "Search for 'Tesla', both hotlists and RSS"

**Tool return behavior:**

- Hotlist results and RSS results are **displayed separately**
- Hotlists are sorted by ranking/relevance, RSS is sorted by publish time
- RSS results do not affect the ranking display of hotlists
- Returns 50 hotlist items + 20 RSS items by default

**Adjustable:**

- RSS quantity: e.g., "Return 10 RSS items"
- Only search hotlists: Do not say "including RSS" (default behavior)
- Only search RSS: Say "Only search in RSS"

---

### Q5: How to find related news?

**You can ask like this:**

- "Find news similar to 'Tesla price cuts'" (Today)
- "Find news related to 'Artificial Intelligence breakthrough' from yesterday" (Historical)
- "Search for related reports about 'ChatGPT' from last week" (Historical)
- "See if there are any reports similar to this news in the last 7 days" (History)

**Supported time ranges:**

| Method | Description | Example |
|------|------|------|
| Not specified | Only query today's data (default) | "Find similar news" |
| Preset values | Yesterday, last week, last month | "Find related news from yesterday" |
| Date range | Specify start and end dates | "Find related reports from January 1st to 7th" |

**Tool return behavior:**

- Similarity threshold 0.5 (adjustable)
- The tool will return up to 50 results
- Sorted by similarity
- Does not include URL links by default

**AI display behavior (Important):**

- ⚠️ **AI usually summarizes automatically**, only displaying some related news
- ✅ If you want to see all of them, you need to explicitly request: "Show all related news"

**Can be adjusted:**

- Specify time: e.g., "Find last week's"
- Adjust threshold: e.g., "Need all with similarity above 0.3"
- Include links: say "Need links"

---

## Trend Analysis

### Q6: How to analyze the popularity trend of a topic?

**You can ask like this:**

- "Analyze the popularity trend of 'Artificial Intelligence' over the past week"
- "See if the 'Tesla' topic is a flash in the pan or a sustained hot topic"
- "Detect which topics suddenly went viral today"
- "Predict potential upcoming hot topics"
- "Analyze the lifecycle of 'Bitcoin' in December 2024"

**Four analysis modes:**

| Mode | Description | Example Question |
|------|------|---------|
| **Popularity Trend** | Track changes in topic popularity | "Analyze the popularity trend of 'AI'" |
| **Lifecycle** | Complete cycle from emergence to disappearance | "See if 'XX' is a flash in the pan or a sustained hot topic" |
| **Anomaly Detection** | Identify suddenly viral topics | "Which topics suddenly went viral today" |
| **Prediction** | Predict potential future hot topics | "Predict potential upcoming hot topics" |

**Tool return behavior:**

- AI will automatically convert relative times like "past week" into specific date ranges
- Analyzes the last 7 days of data by default
- Statistics at a daily granularity

---

## Data Insights

### Q7: How to compare the attention given to a topic across different platforms?

**You can ask like this:**

- "Compare the attention given to the 'Artificial Intelligence' topic across various platforms"
- "See which platform updates most frequently"
- "Analyze which keywords frequently appear together"

**Three insight modes:**

| Mode | Function | Example Question |
| -------------- | ---------------- | -------------------------- |
| **Platform Comparison** | Compare attention across platforms | "Compare attention to 'AI' across platforms" |
| **Activity Statistics** | Count platform publishing frequency | "See which platform updates most frequently" |
| **Keyword Co-occurrence** | Analyze keyword associations | "Which keywords frequently appear together" |

**Tool return behavior:**

- Defaults to platform comparison mode
- Analyzes today's data
- Minimum keyword co-occurrence frequency is 3 times

---

## Sentiment Analysis

### Q8: How to analyze the sentiment of news?

**You can ask like this:**

- "Analyze the sentiment of today's news"
- "See if news related to 'Tesla' is positive or negative"
- "Analyze the sentiment attitude of various platforms towards 'Artificial Intelligence'"
- "See the sentiment of 'Bitcoin' over the past week, select the top 20 most important ones"

**Tool return behavior:**

- Defaults to analyzing today's data
- The tool will return up to 50 news items
- Sorted by weight (prioritizes showing important news)
- Defaults to not including URL links

**AI display behavior (Important):**

- ⚠️ This tool returns **AI prompts**, not direct sentiment analysis results
- AI will generate a sentiment analysis report based on the prompts
- Usually displays sentiment distribution, key findings, and representative news

**Can be adjusted:**

- Specify topic: e.g., "About 'Tesla'"
- Specify time: e.g., "In the last week"
- Adjust quantity: e.g., "Return the top 20"

---

### Q9: How to get deduplicated cross-platform news?

**You can ask like this:**

- "Help me aggregate today's news and remove duplicates"
- "See which news is reported on multiple platforms"
- "Show me the deduplicated trending news"
- "Which news are cross-platform trends"

**Tool functions:**

- Automatically identifies the same event reported by different platforms
- Merges similar news into a single aggregated news item
- Show the platform coverage for each news item
- Calculate the comprehensive popularity weight

**Returned Information:**

| Field | Description |
|------|------|
| **Representative Title** | The representative title of this group of news |
| **Covered Platforms** | Which platforms reported this news |
| **Platform Count** | How many platforms are covered |
| **Is Cross-Platform** | Whether it is a cross-platform hot topic |
| **Best Ranking** | The best ranking across platforms |
| **Comprehensive Weight** | Comprehensive popularity score |
| **Platform Sources** | Detailed information from each platform |

**You can adjust:**

- Specify time: e.g., "from the last week"
- Adjust similarity threshold: e.g., "stricter match" or "loose match"
- Specify platforms: e.g., "only look at Zhihu and Weibo"

---

### Q10: How to generate daily or weekly hot topic summaries?

**You can ask:**

- "Generate today's news summary report"
- "Give me a hot topic summary for this week"
- "Generate a news analysis report for the past 7 days"

**Report Types:**

- Daily summary: Summarize the hot news of the day
- Weekly summary: Summarize the hot trends of the week

---

### Q11: How to compare hot topic changes across different periods?

**You can ask:**

- "Compare the hot topic changes between this week and last week"
- "See what's different between this month and last month"
- "Analyze the popularity difference of 'Artificial Intelligence' between the two periods"
- "Compare the changes in platform activity"

**Three Comparison Modes:**

| Mode | Description | Applicable Scenarios |
|------|------|---------|
| **General Overview** | Changes in news volume, keyword changes, TOP news comparison | Quickly understand overall changes |
| **Topic Changes** | Rising topics, declining topics, newly emerged topics | Analyze hot topic shifts |
| **Platform Activity** | Changes in the number of news items across platforms | Understand platform dynamics |

**Time Period Presets:**

- Today / Yesterday
- This week / Last week
- This month / Last month
- Or use a custom date range

---

## System Management

### Q12: How to view the system configuration?

**You can ask:**

- "View current system configuration"
- "Show configuration file content"
- "What platforms are available?"
- "What is the current weight configuration?"

**You can query:**

- List of available platforms
- Crawler configuration (request interval, timeout settings)
- Weight configuration (ranking weight, frequency weight)
- Notification configuration (Feishu, DingTalk, WeCom, Telegram, Email, ntfy, Bark, Slack, General Webhook)

---

### Q13: How to check the system running status?

**You can ask:**

- "Check system status"
- "Is the system running normally?"
- "When was the last crawl?"
- "How many days of historical data are there?"

**Returns:**

- System version and status
- Last crawl time
- Days of historical data
- Health check results

---

### Q13.1: How to check for version updates?

**You can ask:**

- "Check for version updates"
- "Is there a new version?"
- "Is the current version the latest?"

**Returns:**

It will check the versions of both components:

| Component | Description |
|------|------|
| **TrendRadar** | Core crawler and analysis engine |
| **MCP Server** | AI conversation tool service |

For each component, it will tell you:
- Currently installed version
- Latest available version
- Whether an update is needed
- Update suggestions

**You can adjust:**

- If accessing GitHub is slow, you can say "Check for version updates, use proxy http://127.0.0.1:10801"

---

### Q14: How to manually trigger a crawl task?

**You can ask:**

- "Please crawl the current Toutiao news" (Temporary query)
- "Help me fetch the latest news from Zhihu and Weibo and save it" (Persistent)
- "Trigger a crawl and save the data" (Persistent)
- "Get real-time data from 36Kr but don't save it" (Temporary query)

**Two modes:**

| Mode | Purpose | Example |
| -------------- | -------------------- | -------------------- |
| **Temporary Crawl** | Returns data only, does not save | "Crawl Toutiao news" |
| **Persistent Crawl** | Saves to the output folder | "Fetch and save Zhihu news" |

**Tool return behavior:**

- Defaults to temporary crawl mode (does not save)
- Defaults to crawling all platforms
- Defaults to not including URL links

**AI display behavior (Important):**

- ⚠️ **AI usually summarizes the crawl results**, displaying only a portion of the news
- ✅ If you want to see everything, you need to explicitly request: "Display all crawled news"

**You can adjust:**

- Specify platform: e.g., "Only crawl Zhihu"
- Save data: say "and save" or "save locally"
- Include links: say "need links"

---

## Storage Synchronization

### Q15: How to synchronize data from remote storage to local?

**You can ask:**

- "Synchronize the last 7 days of data from remote"
- "Pull data from remote storage to local"
- "Synchronize the last 30 days of news data"

**Use cases:**

- Crawler is deployed in the cloud (e.g., GitHub Actions), and data is stored remotely (e.g., Cloudflare R2)
- MCP Server is deployed locally and needs to pull data from remote for analysis

**Return information:**

- Number of successfully synchronized files
- List of successfully synchronized dates
- Skipped dates (already exist locally)
- Failed dates and error messages

**Prerequisites:**

Need to configure remote storage in the configuration file or set environment variables:
- Service endpoint URL
- Bucket name
- Access key ID
- Access key

---

### Q16: How to check the storage status?

**You can ask:**

- "Check current storage status"
- "What is the storage configuration"
- "How much data is stored locally"
- "Is remote storage configured"

**Returned information:**

| Category | Information |
|------|------|
| **Local Storage** | Data directory, total size, number of dates, date range |
| **Remote Storage** | Whether configured, endpoint address, bucket name, number of dates |
| **Pull Configuration** | Whether auto-pull is enabled, pull days |

---

### Q17: How to check available data dates?

**You can ask:**

- "What dates of data are available locally"
- "What dates are in remote storage"
- "Compare local and remote data dates"
- "Which dates are only available remotely"

**Three query modes:**

| Mode | Description | Example Question |
|------|------|---------|
| **Local** | View local only | "What dates are available locally" |
| **Remote** | View remote only | "What dates are available remotely" |
| **Compare** | Compare both (default) | "Compare local and remote data" |

**Returned information (Compare mode):**

- Dates that only exist locally
- Dates that only exist remotely (can be used to decide which dates to sync)
- Dates that exist in both

---

### Q18: How to parse natural language date expressions? (Recommended to use first)

**You can ask:**

- "Parse which days are in 'this week'"
- "What is the date range for the last 7 days"
- "Date range for last month"
- "Help me convert 'last 30 days' to specific dates"

**Why is this tool needed?**

Users often use natural language like "this week" or "last 7 days" to express dates, but different AI models may produce inconsistent results when calculating dates themselves. This tool uses precise server-side time calculation to ensure all AI models get a consistent date range.

**Supported date expressions:**

| Type | Chinese Expression | English Expression |
|------|---------|---------|
| Single day | Today, Yesterday | today, yesterday |
| Week | This week, Last week | this week, last week |
| Month | This month, Last month | this month, last month |
| Last N days | Last 7 days, Last 30 days | last 7 days, last 30 days |
| Dynamic | Last N days (any number) | last N days |

**Advantages:**

- ✅ **Consistency**: All AI models get the same date range
- ✅ **Accuracy**: Based on precise server-side time calculation
- ✅ **Standardization**: Returns standard date format
- ✅ **Flexibility**: Supports Chinese and English, dynamic number of days

---

## Article Content Reading

### Q19: How to read the main content of a news article?

**You can ask like this:**

- "Help me read the content of this news: https://example.com/news/123"
- "Get the article body of this link"
- "Read the detailed content of this report"

**Tool features:**

- Converts web pages to clean Markdown format via Jina AI Reader
- Automatically removes noise content such as ads, navigation bars, and sidebars
- Returns LLM-friendly structured content

**Typical usage flow:**

1. First use `search_news(include_url=True)` to search for news and get links
2. Then use `read_article(url=link)` to read the main content
3. AI analyzes, summarizes, translates, etc., the Markdown content

**Returned information:**

| Field | Description |
|------|------|
| **content** | Article body in Markdown format |
| **url** | Original link |
| **content_length** | Content length (number of characters) |

**Adjustable:**

- Timeout: e.g., "set timeout to 60 seconds" (default 30 seconds, max 60 seconds)

**Notes:**

- 5 seconds interval between each request (built-in rate control)
- Uses Jina AI Reader free service (100 RPM limit)
- Some paywall/login wall pages may not be fully retrieved

---

### Q20: How to read multiple articles in batch?

**You can ask like this:**

- "Help me read the content of these news articles"
- "Batch get the article bodies of these links"
- "Read the detailed content of the top 3 articles in the search results"

**Typical usage flow:**

1. First use `search_news(include_url=True)` to search for news and get multiple links
2. Then use `read_articles_batch(urls=[...])` to read the main content in batch
3. AI conducts comparative analysis and comprehensive reporting on multiple articles

**Tool Limits:**

| Limit | Value |
|------|------|
| Max articles per request | **5 articles** |
| Request interval | **5 seconds** |
| Estimated time (5 articles) | **25-30 seconds** |

**Response Information:**

| Field | Description |
|------|------|
| **summary** | Statistics of batch reading |
| **articles** | Content and status of each article |
| **note** | Reason for skipped articles, if any |

**Notes:**

- Articles exceeding the 5-article limit will be automatically skipped
- Failure of a single article does not affect the reading of others
- The more articles, the longer it takes. Please be patient

---

## Notification Push

### Q21: How to send notification messages via MCP?

**You can ask like this:**

- "Check which notification channels are currently configured"
- "Send a test message to all channels"
- "Push this content to Feishu"
- "Send today's news summary to DingTalk and Telegram"

**Supported Notification Channels (9):**

| Channel | Message Format | Configuration Source |
|------|---------|---------|
| **Feishu** (feishu) | Plain Text | `FEISHU_WEBHOOK_URL` |
| **DingTalk** (dingtalk) | Markdown | `DINGTALK_WEBHOOK_URL` |
| **WeCom** (wework) | Markdown | `WEWORK_WEBHOOK_URL` |
| **Telegram** | HTML | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| **Email** | HTML | `EMAIL_FROM` + `EMAIL_PASSWORD` + `EMAIL_TO` |
| **ntfy** | Markdown | `NTFY_SERVER_URL` + `NTFY_TOPIC` |
| **Bark** | Markdown | `BARK_URL` |
| **Slack** | mrkdwn | `SLACK_WEBHOOK_URL` |
| **Generic Webhook** | Markdown | `GENERIC_WEBHOOK_URL` |

**Configuration Method:**

- Configure the corresponding channel in `notification.channels` of `config.yaml`
- Or set the corresponding environment variables in the `.env` file (higher priority)
- The two methods will be automatically merged, and values in `.env` will overwrite those in `config.yaml`

**Two Tools:**

| Tool | Function | Example Question |
|------|------|---------|
| `get_notification_channels` | Check configured channels and their status | "Check notification channel configuration" |
| `send_notification` | Send messages to specified or all channels | "Send a message to Feishu" |

**Typical Usage Flow:**

1. First, check the channel status: "Check which notification channels are currently configured"
2. Send after confirming the channel is available: "Push the following content to DingTalk: Today's hot topics summary..."
3. Or specify multiple channels: "Send to Feishu and Telegram"
4. If no channel is specified, it will be sent to all configured channels

**Message Format:**

- The tool accepts message content in **Markdown format**
- Automatically converts formats according to channel requirements (Feishu to plain text, Telegram to HTML, Slack to mrkdwn, etc.)
- No need to manually handle format differences

**Multi-account Support:**

- Separate multiple URLs/Tokens with `;` in the configuration value to send to multiple accounts
- For example: `FEISHU_WEBHOOK_URL=url1;url2` will send to two Feishu groups simultaneously

---

## 💡 Usage Tips

### 1. How to make the AI display all data instead of automatically summarizing?

**Background**: Sometimes the AI will automatically summarize the data and only display partial content, even if the tool returned the complete 50 items.

**If the AI still summarizes, you can**:

- **Method 1 - Explicit Request**: "Please show all news, do not summarize"
- **Method 2 - Specify Quantity**: "Show all 50 news items"
- **Method 3 - Question Behavior**: "Why did you only show 15 items? I want to see all of them"
- **Method 4 - State in Advance**: "Query today's news, fully display all results"

**Note**: The AI may still adjust the display method based on context.


### 2. How to use multiple tools in combination?

**Example: In-depth analysis of a topic**

1. Search first: "Search for news related to 'artificial intelligence'"
2. Then analyze trends: "Analyze the popularity trend of 'artificial intelligence'"
3. Finally, sentiment analysis: "Analyze the sentiment of 'artificial intelligence' news"

**Example: Tracking an event**

1. Check the latest: "Query today's news about 'iPhone'"
2. Find history: "Find historical news related to 'iPhone' from last week"
3. Find similar reports: "Find news similar to 'iPhone launch event'"

