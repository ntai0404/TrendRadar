<div align="center" id="trendradar">

<a href="https://github.com/sansan0/TrendRadar" title="TrendRadar">
  <img src="/_image/banner.webp" alt="TrendRadar Banner" width="80%">
</a>

The fastest trending topic assistant deployed in <strong>30 seconds</strong> — say goodbye to endless scrolling, only read the news you truly care about

<a href="https://trendshift.io/repositories/14726" target="_blank"><img src="https://trendshift.io/api/badge/repositories/14726" alt="sansan0%2FTrendRadar | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>


[![GitHub Stars](https://img.shields.io/github/stars/sansan0/TrendRadar?style=flat-square&logo=github&color=yellow)](https://github.com/sansan0/TrendRadar/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/sansan0/TrendRadar?style=flat-square&logo=github&color=blue)](https://github.com/sansan0/TrendRadar/network/members)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-v6.8.0-blue.svg)](https://github.com/sansan0/TrendRadar)
[![MCP](https://img.shields.io/badge/MCP-v4.0.4-green.svg)](https://github.com/sansan0/TrendRadar)
[![RSS](https://img.shields.io/badge/RSS-Feed_Support-orange.svg?style=flat-square&logo=rss&logoColor=white)](https://github.com/sansan0/TrendRadar)
[![AI Translation](https://img.shields.io/badge/AI-Multilingual_Push-purple.svg?style=flat-square)](https://github.com/sansan0/TrendRadar)

[![WeCom Notification](https://img.shields.io/badge/WeCom-Notification-00D4AA?style=flat-square)](https://work.weixin.qq.com/)
[![WeChat Notification](https://img.shields.io/badge/WeChat-Notification-00D4AA?style=flat-square)](https://weixin.qq.com/)
[![Telegram Notification](https://img.shields.io/badge/Telegram-Notification-00D4AA?style=flat-square)](https://telegram.org/)
[![DingTalk Notification](https://img.shields.io/badge/DingTalk-Notification-00D4AA?style=flat-square)](#)
[![Feishu Notification](https://img.shields.io/badge/Feishu-Notification-00D4AA?style=flat-square)](https://www.feishu.cn/)
[![Email Notification](https://img.shields.io/badge/Email-Notification-00D4AA?style=flat-square)](#)
[![ntfy Notification](https://img.shields.io/badge/ntfy-Notification-00D4AA?style=flat-square)](https://github.com/binwiederhier/ntfy)
[![Bark Notification](https://img.shields.io/badge/Bark-Notification-00D4AA?style=flat-square)](https://github.com/Finb/Bark)
[![Slack Notification](https://img.shields.io/badge/Slack-Notification-00D4AA?style=flat-square)](https://slack.com/)
[![Custom Webhook](https://img.shields.io/badge/Custom-Webhook-607D8B?style=flat-square&logo=webhook&logoColor=white)](#)


[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automation-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/sansan0/TrendRadar)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Deployment-4285F4?style=flat-square&logo=github&logoColor=white)](https://sansan0.github.io/TrendRadar)
[![Docker](https://img.shields.io/badge/Docker-Deployment-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/wantcat/trendradar)
[![MCP Support](https://img.shields.io/badge/MCP-AI_Analysis_Support-FF6B6B?style=flat-square&logo=ai&logoColor=white)](https://modelcontextprotocol.io/)
[![AI Analysis Push](https://img.shields.io/badge/AI-Analysis_Push-FF6B6B?style=flat-square&logo=openai&logoColor=white)](#)
[![AI Smart Filtering](https://img.shields.io/badge/AI-Smart_News_Filtering-9B59B6?style=flat-square&logo=openai&logoColor=white)](#)

</div>

<div align="center">

**Chinese** | **[English](README-EN.md)**

</div>

> This project aims to be lightweight and easy to deploy

<br>

## 📑 Quick Navigation

> 💡 **Click the links below** to quickly jump to the corresponding sections. For deployment, it is recommended to start with "**Quick Start**". For detailed customization, please see "**Configuration Details**"

<div align="center">

|   |   |   |
|:---:|:---:|:---:|
| [🚀 **Quick Start**](#-Quick Start) | [AI Smart Analysis](#-ai-Intelligent Analysis) | [⚙️ **Configuration Details**](#Configuration Details) |
| [Docker Deployment](#6-docker-deployment) | [MCP Client](#-mcp-client) | [📝 **Changelog**](#-Update log) |
| [🎯 **Core Features**](#-Core Features) | [☕ **Support the Project**](#-Support the Project) | [📚 **Project Related**](#-Project Related) |

</div>

<br>

- Thanks to everyone who **starred the project**. **Forking** is what you want, **starring** is what I want, and having both 😍 is the best support for the open-source spirit

<details>
<summary>👉 Click to expand: <strong>Acknowledgments</strong> (Angel Round Honor Roll 🔥73+🔥 members)</summary>

### Acknowledgments to Early Supporters

> 💡 **Special Note**:
>
> 1. **About the list**: The table below records the supporters during the project's initial stage (angel round). Due to the tedious manual tracking in the early days, **there may inevitably be omissions or incomplete records. If you were missed, it was truly unintentional, and we beg your understanding**.
> 2. **Future plans**: In order to refocus our limited energy on code and feature iteration, **we will no longer manually maintain this list from today onwards**.
>
> Whether your name is on the list or not, every bit of your support is the cornerstone that has allowed TrendRadar to reach where it is today. 🙏

### Infrastructure Support

Thanks to **GitHub** for providing free infrastructure, which is the biggest prerequisite for this project to run conveniently with a **one-click fork**.

### Data Support

This project uses the API of the [newsnow](https://github.com/ourongxing/newsnow) project to obtain multi-platform data. Special thanks to the author for providing this service.

After contacting the author, they stated there is no need to worry about server pressure, but this is based on their goodwill and trust. Please:
- **Go to the [newsnow project](https://github.com/ourongxing/newsnow) and leave a star to support it**
- When deploying with Docker, please reasonably control the push frequency and do not abuse the API

### Promotion Support

> Thanks to the following platforms and individuals for their recommendations (in chronological order)

- [Appinn](https://mp.weixin.qq.com/s/fvutkJ_NPUelSW9OGK39aA) - Open source software recommendation platform
- [LinuxDo Community](https://linux.do/) - A gathering place for tech enthusiasts
- [Ruan Yifeng's Weekly](https://github.com/ruanyf/weekly) - An influential weekly newsletter in the tech community

### Audience Support

> Thanks to the friends who **provided financial support**. Your generosity has turned into snacks and drinks next to the keyboard, accompanying every iteration of the project.
>
> **Regarding the return of "One Yuan Like"**:
> With the release of version v5.0.0, the project has entered a new stage. To support the growing API costs and caffeine consumption, the "One Yuan Like" channel has now been reopened. Every bit of your support will be transformed into Tokens and motivation in the coding world. 🚀 [Go to support](#-support project)

|           Supporter            |  Amount  |  Date  |             Remarks             |
| :-------------------------: | :----: | :----: | :-----------------------: |
|           D*5          |  1.8 * 3 | 2025.11.24  |    | 
|           *Gui          |  1 | 2025.11.17  |    |
|           *Chao          |  10 | 2025.11.17  |    |
|           R*w          |  10 | 2025.11.17  | This agent is awesome, bro    |
|           J*o          |  1 | 2025.11.17  | Thanks for open sourcing, wishing you success in your career    |
|           *Chen          |  8.88  | 2025.11.16  | Good project, studying and learning from it    |
|           *Hai          |  1  | 2025.11.15  |    |
|           *De          |  1.99  | 2025.11.15  |    |
|           *Shu          |  8.8  | 2025.11.14  |  Thanks for open sourcing, great project, supporting it   |
|           M*e          |  10  | 2025.11.14  |  Open source is not easy, thanks for your hard work   |
|           **Ke          |  1  | 2025.11.14  |     |
|           *Yun          |  88  | 2025.11.13  |    Good project, thanks for open sourcing  |
|           *W          |  6  | 2025.11.13  |      | 
|           *Kai          |  1  | 2025.11.13  |      |
|           Dui*.          |  1  | 2025.11.13  |    Thanks for your TrendRadar  |
|           s*y          |  1  | 2025.11.13  |      | 
|           **Xiang          |  10  | 2025.11.13  |   Good project, wish I found it sooner, thanks for open sourcing!     |
|           *Wei          |  9.9  | 2025.11.13  |   TrendRadar is awesome, buying you a coffee~     |
|           h*p          |  5  | 2025.11.12  |   Support Chinese open source power, keep it up!     |
|           c*r          |  6  | 2025.11.12  |        | 
|           a*n          |  5  | 2025.11.12  |        | 
|           .*c          |  1  | 2025.11.12  |    Thanks for open source sharing    |
|           *Ji          |  1  | 2025.11.11  |        |
|           *Zhu          |  1  | 2025.11.10  |        |
|           *Le          |  10  | 2025.11.09  |        |
|           *Jie          |  5  | 2025.11.08  |        |
|           *Dian          |  8.80  | 2025.11.07  |   Development is not easy, supporting you.     |
|           Q*Q          |  6.66  | 2025.11.07  |   Thanks for open sourcing!     |
|           C*e          |  1  | 2025.11.05  |        | 
|           Peter Fan          |  20  | 2025.10.29  |        | 
|           M*n          |  1  | 2025.10.27  |      Thanks for open sourcing  |
|           *Xu          |  8.88  | 2025.10.23  |      Teacher, I'm a newbie, been trying for a few days but still haven't set it up, please advise  |
|           Eason           |  1  | 2025.10.22  |      Haven't figured it out yet, but you are doing a good thing  |
|           P*n           |  1  | 2025.10.20  |          |
|           *Jie           |  1  | 2025.10.19  |          |
|           *Xu           |  1  | 2025.10.18  |          |
|           *Zhi           |  1  | 2025.10.17  |          |
|           *😀           |  10  | 2025.10.16  |     Like     |
|           **Jie           |  10  | 2025.10.16  |          |
|           *Xiao           |  10  | 2025.10.16  |          |
|           *Ji           |  5  | 2025.10.14  | TrendRadar         |
|           J*d           |  1  | 2025.10.14  | Thanks for your tool, it's very fun...          |
|           *H           |  1  | 2025.10.14  |           |
|           Na*O           |  10  | 2025.10.13  |           |
|           *Yuan           |  1  | 2025.10.13  |           |
|           P*g           |  6  | 2025.10.13  |           |
|           Ocean           |  20  | 2025.10.12  |  ...really awesome!!! Even beginners can use it directly...         |
|           **Pei           |  5.2  | 2025.10.2  |  github-yzyf1312: Long live open source         |
|           *Chun           |  3  | 2025.9.23  |  Keep it up, very good         |
|           *🍍           |  10  | 2025.9.21  |           |
|           E*f           |  1  | 2025.9.20  |           |
|           *Ji            |  1  | 2025.9.20  |           |
|           z*u            |  2  | 2025.9.19  |           |
|           **Hao            |  5  | 2025.9.17  |           |
|           *Hao            |  1  | 2025.9.15  |           |
|           T*T            |  2  | 2025.9.15  |  Thumbs up         |
|           *Jia            |  10  | 2025.9.10  |           |
|           *X            |  1.11  | 2025.9.3  |           |
|           *Biao            |  20  | 2025.8.31  |  Thanks from Lao Tong         |
|           *Xia            |  1  | 2025.8.30  |           |
|           2*D            |  88  | 2025.8.13 PM |           |
|           2*D            |  1  | 2025.8.13 AM |           |
|           S*o            |  1  | 2025.8.05 |   Support        |
|           *Xia            |  10  | 2025.8.04 |           |
|           x*x            |  2  | 2025.8.03 |  trendRadar good project thumbs up          |
|           *Yuan            |  1  | 2025.8.01 |            |
|           *Xie            |  5  | 2025.8.01 |            |
|           *Meng            |  0.1  | 2025.7.30 |            |
|           **Long            |  10  | 2025.7.29 |      Support      |


</details>

<br>

## 🪄 Sponsors

<div align="center">

> **Available**

</div>

<br>

<a name="-support-the-project"></a>

### ❤️ Find it useful? Support us

> If TrendRadar has captured value for you, why not inject some power into it to help it continue to evolve
>
> Any amount is welcome, even 1 yuan is an encouragement for open source. Feel free to leave a message when donating (´▽`ʃ♡ƪ)

<div align="center">

| WeChat Pay | Alipay |
|:---:|:---:|
| <img src="https://cdn-1258574687.cos.ap-shanghai.myqcloud.com/img/%2F2025%2F07%2F17%2F2ae0a88d98079f7e876c2b4dc85233c6-9e8025.JPG" width="240" alt="WeChat Pay"> | <img src="https://cdn-1258574687.cos.ap-shanghai.myqcloud.com/img/%2F2025%2F07%2F17%2F1ed4f20ab8e35be51f8e84c94e6e239b4-fe4947.JPG" width="240" alt="Alipay"> |

</div>


### 🤝 Secondary Development and Citation

If you use or refer to the ideas or core code of this project in your project, you are **very welcome** to indicate the source in the README or documentation and attach the link to this repository.

This will help the continuous maintenance of the project and community development. Thank you for your respect and support! ❤️


### 💬 Communication and Feedback

- **GitHub Issues**: Suitable for specific technical problems. Please provide complete information (screenshots, error logs, etc.) when asking questions to help quickly locate the issue.
- **WeChat Official Account Communication**: It is recommended to communicate in the comment section under related articles first. If you need to ask questions in the background, **liking/recommending** the article first is the best "stepping stone", I can feel this kindness in the background (´▽`ʃ♡ƪ).
- **QQ Group Communication**: Follow the official account and reply "**Communication Group**" to join. Whether you are an AI beginner or a hardcore developer, want to ask for help with technical problems or share your tinkering experience, you are welcome here. The group focuses on mutual help and inspiration collision. Please read the group announcement first when joining; describe the problem clearly and attach screenshots when asking questions. Group members will help when they have time. Everyone's practical experience is often faster and more comprehensive than mine alone 🤝

> **Friendly Reminder**:
> This project is an open-source sharing, not a commercial product. Treating the author as a friend rather than customer service will make communication much more efficient!

<div align="center">

| WeChat Official Account |
|:---:|
| <img src="_image/weixin.png" width="500" title="Silicon-based Tea Room"/> |

</div>

<br>

## 📝 Changelog

> **📌 View Latest Updates**: **[Original Repository Changelog](https://github.com/sansan0/TrendRadar?tab=readme-ov-file#-Update Log)**:
- **Tip**: It is recommended to check [Historical Updates] to clarify specific [Feature Content]


### 2026/05/23 - v6.8.0

- **Comprehensive HTML Report Enhancements**: Added report metadata display (generation time, data source, version number), automatic dark mode adaptation, Tab bar interaction optimization, and trend arrow visualization, significantly improving the browser reading experience
- **Version Check CDN Multi-source Fallback**: The version check interface supports automatic fallback across multiple CDN sources like GitHub → jsDelivr → Cloudflare, ensuring stable update notifications even in domestic network environments
- **Display Region Switches Effective**: HTML reports and emails now correctly respect the `display.regions.ai_analysis` and `display.regions.standalone` switches; they will not be rendered if turned off
- **Export Button Fix**: Fixed the issue where the dropdown menu icon disappeared after clicking the export button
- **Markdown Export Fix**: Fixed JS newline character escaping errors in the HTML report Markdown export

### 2026/02/09 - mcp-v4.0.0

- **🔥 AI Message Direct Push to All Channels**: Push AI-generated content with one click to 9 channels including Feishu, DingTalk, Telegram, and Email. Markdown automatically adapts to each platform's format, so you don't have to worry about formatting differences
- **New Formatting Strategy Guide**: Added the `get_channel_format_guide` tool to tell AI what formats each channel supports and what limitations they have, resulting in better-formatted generated content
- **Smart Batch Sending**: Overly long messages are automatically split according to the byte limits of each channel (Feishu 30KB, DingTalk 20KB, etc.), with configurations read from config.yaml
- **Channel False Detection Fix**: ntfy is no longer falsely reported as "configured" due to the default address
- **Code Reuse Optimization**: Batch processing functions directly reuse the trendradar core module, avoiding reinventing the wheel


<details>
<summary>👉 Click to expand: <strong>Historical Updates</strong></summary>

### 2026/05/15 - v6.7.0

- **Markdown Export**: Added Markdown format to the report export dropdown menu, generating structured text with links in one click, facilitating LLM secondary processing and cross-platform sharing ([#1121](https://github.com/sansan0/TrendRadar/issues/1121))
- **RSS guid Deduplication**: Added a guid field to RSS storage, changing the deduplication priority to guid > url, solving the issue of duplicate entries for the same article caused by URL changes
- **Empty Title Protection**: Added fallback logic for empty titles across the entire chain of parser, rendering layer, and translation backfill, ensuring items without titles can also be displayed normally
- **Translation Quality Enhancement**: Translation prompts now require preserving the numbering order, and empty translation results will no longer overwrite the original title

### 2026/03/28 - v6.6.0

- **HTML Report Browser Enhancements**: Opening the report in a browser automatically switches to a widescreen layout. Both keyword groups and independent display areas support quick Tab switching, and the search box filters news titles in real-time. Email clients still display the original narrow-screen layout with zero regressions
- **Dark Mode**: One-click switch to a dark theme, automatically remembering preferences, suitable for night reading
- **One-click Copy News**: Hover over the news number to copy the title and link, making quick sharing easy
- **Export Optimization**: Full-page screenshots and segmented screenshots are merged into a dropdown export button, automatically restoring a clean layout when taking screenshots
- **Shortcut Key System**: Supports `W` for widescreen toggle, `D` for dark mode, `/` for search, and `?` to view shortcut key tips
- **Reading Progress Bar**: Real-time display of reading progress at the top of the page

### 2026/03/12 - v6.5.0

- **AI Smart Filtering System**: No need to manually set keywords anymore! Write down your areas of interest in everyday language in `ai_interests.txt` (e.g., "I want to see news related to AI and new energy"), and AI will automatically extract tags and score each piece of news, only pushing content truly relevant to you. In case the AI filtering encounters an issue, it will automatically switch back to keyword matching, ensuring pushing is not interrupted
- **Different Filtering Methods and Focus Areas Supported for Each Time Period**: Each time period in the Timeline can now be independently configured with its filtering method and the type of news to watch. For example: use "tech keywords" for quick filtering in the morning, and switch to "financial AI interest descriptions" for deep filtering at night—the same system, different content at different times
- **AI Analysis Scope Independent of Pushing**: The data scope for AI analysis can be different from the pushed content. For example, pushing only sends new messages (to avoid repeated interruptions), but AI analyzes all news of the day (to see the complete trend). Each time period can also have its AI analysis mode set individually
- **AI Filtering Smart Cost-saving**: Previously analyzed news will not repeatedly consume tokens; after modifying the interest description, AI automatically judges the extent of the change—small changes only update affected tags, while large changes trigger a full re-classification
- **Multi-file Configuration and Tag Isolation**: Custom keyword files are placed in `config/custom/keyword/`, and AI interest files in `config/custom/ai/`. Tags generated from different files are independent and do not interfere with each other
- **Precise Control of AI Translation**: You can separately control whether trending lists, RSS, and independent display areas are translated. Areas not enabled for display are automatically skipped, avoiding token waste
- **Remote Storage Batch Upload**: Multiple write operations are accumulated and submitted to the cloud at once, reducing the number of API calls
- **Display Quantity Limit per Keyword/Tag Group**: Control the maximum number of news items displayed per group via `max_news_per_keyword`, preventing a single hot topic from occupying the entire push
- **Time Period Conflict Smart Detection**: If two time periods overlap, the system will automatically report an error and prompt for modification, avoiding unexpected behavior caused by configuration conflicts
- Fixed several bugs

### 2026/02/09 - v6.0.0

> **Breaking Change**: Configuration file upgrade (config.yaml 2.0.0). The old `push_window` and `analysis_window` configurations are no longer compatible. Please refer to the new config.yaml for migration

- **Unified Scheduling System**: Added `timeline.yaml`, using a single set of configurations to control "when to collect / push / AI analyze"
- **5 preset templates**: `always_on` (24/7, default), `morning_evening` (morning and evening summary), `office_hours` (office hours), `night_owl` (night owl), `custom` (custom); also supports adding your own templates under `presets:` as long as the key is unique, then just fill in your template name in config.yaml
- **Flexible time period configuration**: supports weekday/weekend differentiation, cross-midnight time periods, per-period once deduplication
- **Visual configuration editor**:
  - Added `timeline.yaml` edit tab, alongside config.yaml / frequency_words.txt
  - Preset mode card selection: click to switch, automatically syncs `schedule.preset` in config.yaml
  - Weekly view timeline: 7 days × 24 hours horizontal bars, using colors to distinguish push/analysis/collection status
  - Interactive controls: switches, dropdowns, time selectors, modifications on the right sync in real-time to the YAML on the left
  - Weekly mapping dropdown selection: dynamically populated based on daily plans, drag and click to complete scheduling configuration
- **AI prompt stability optimization** (ai_analysis_prompt.txt v2.0.0):
  - Independent format specification instructions: extracted line breaks/tags/numbers/prohibitions from JSON values into an independent section
  - JSON template simplification: field descriptions shortened to one sentence + word limit, reducing AI output format confusion
  - Removed Markdown formatting from system prompt, consistent with the "No Markdown" instruction
  - All JSON fields declared as optional, missing any field will not cause an error, enhancing fault tolerance
- **Added AI summary analysis for standalone display area** (`ai_analysis.include_standalone`):
  - Added independent switch, when enabled AI generates a core summary for each standalone source
  - Decoupled AI analysis and push display: AI can independently analyze complete trending data without enabling push display for the standalone display area
  - Supports trending platforms and RSS feeds, including ranking/time/trajectory data
  - Trajectory analysis linked with `include_rank_timeline`: when enabled, uses trajectory data for deep trend analysis; when disabled, makes brief judgments based on rankings
  - Added `standalone_summaries` JSON field (quick overview of standalone sources), all push channels have been adapted for rendering


### 2026/01/28 - v5.5.0

> Just like the mcp feature, I won't open a new repository to maintain this little tool either, since it's pure frontend, let's put them all together

- Added visual configuration editor for trendradar


### 2026/02/02 - mcp-v3.2.0

- **Added read_article tool**: reads the body of a single article via Jina AI Reader (Markdown format)
- **Added read_articles_batch tool**: reads multiple articles in batch (up to 5 articles, automatic rate limiting)
- **Recommended workflow**: `search_news(query="keyword", include_url=True)` → `read_article(url=...)` to read the body
- **Documentation update**: Added Q19-Q20 article reading related instructions in README-MCP-FAQ.md and README-MCP-FAQ-EN.md


### 2026/01/10 - mcp-v3.0.0~v3.1.5

- **Breaking Change**: All tool return values unified to `{success, summary, data, error}` structure
- **Asynchronous consistency**: All 21 tool functions use `asyncio.to_thread()` to wrap synchronous calls
- **MCP Resources**: Added 4 resources (platforms, rss-feeds, available-dates, keywords)
- **RSS enhancement**: `get_latest_rss` supports multi-day queries (days parameter), cross-date URL deduplication
- **Regex matching fix**: `get_trending_topics` supports `/pattern/` regex syntax and `display_name`
- **Cache optimization**: Added `make_cache_key()` function, parameter sorting + MD5 hashing to ensure consistency
- **Added check_version tool**: supports checking TrendRadar and MCP Server version updates simultaneously


### 2026/01/23 - v5.4.0

- Added independent control function for AI analysis mode, options include follow_report | daily | current | incremental
- Added AI analysis time window control, supports custom running periods and daily frequency limits
- Added configuration file version management function
- Fixed several bugs


### 2026/01/19 - v5.3.0

> **Major refactoring: AI module migrated to LiteLLM**

- **Unified AI interface**: uses LiteLLM instead of manual implementation, supports 100+ AI providers
- **Simplified configuration**: removed `provider` field, switched to `model: "provider/model_name"` format
- **New features**: automatic retries (`num_retries`), fallback models (`fallback_models`)
- **Configuration Changes**:
  - `ai.provider` → Removed (merged into model)
  - `ai.base_url` → `ai.api_base`
  - `AI_PROVIDER` environment variable → Removed
  - `AI_BASE_URL` environment variable → `AI_API_BASE`
- **Model Format Example**:
  - DeepSeek: `deepseek/deepseek-chat`
  - OpenAI: `openai/gpt-4o`
  - Gemini: `gemini/gemini-2.5-flash`
  - Anthropic: `anthropic/claude-3-5-sonnet`

### 2026/01/17 - v5.2.0

> Mainly see the description in config.yaml

**🌐 AI Translation Feature**

- **Multilingual Translation**: Supports translating push content into any language
- **Batch Translation**: Intelligent batch processing to reduce API calls
- **Custom Prompts**: Supports customizing translation styles

**🔧 Configuration Architecture Optimization**

- **Independent AI Model Configuration**: Analysis and translation share model configurations
- **Unified Section Switches**: Unified management of push section display
- **Custom Section Sorting**: Supports customizing the display order of each section

**✨ AI Analysis Enhancements**

- **AI Analysis Embedded in HTML**: Analysis results are directly embedded into HTML reports, ready for email notifications
- **Rich-Style AI Block**: Gradient blue background card layout, clearly separating each analysis dimension
- **Ranking Timeline Support**: AI can obtain the exact ranking of each news item at every scraping time point
- **Section Reorganization (7→4)**: Consolidated into core hotspot trends, public opinion controversies, anomalies and weak signals, and judgment strategy suggestions

**🔧 Multi-Model Adaptation**

- **Universal Parameter Passthrough**: Supports passing any advanced parameters to the API
- **Gemini Adaptation**: Native parameter support, built-in relaxation of safety policies

**🐛 Bug Fixes**

- Fixed several known issues to improve system stability

### 2026/01/10 - v5.0.0

> **Development Anecdote**:
> A tribute to a certain Company C's model that accompanied me for over two years, only to pop up `"This organization has been disabled"` right after I renewed my subscription

**✨ Push Content "Five Major Sections" Refactoring**

This update refactored the push messages into sections. Now the push content is clearly divided into five core sections:

1.  **📊 Trending News**: Aggregation of network-wide hotspots precisely filtered based on your keywords.
2.  **📰 RSS Subscriptions**: Your personalized subscription feed content, supporting grouping by keywords.
3.  **🆕 Newly Added**: Real-time capture of brand new hotspots since the last run (marked with 🆕).
4.  **📋 Independent Display Area**: Complete trending lists or RSS feeds of specified platforms, **completely unaffected by keyword filtering**.
5.  **✨ AI Analysis Section**: Deep insights driven by AI, including trend overviews, popularity trends, and **extremely important** sentiment analysis.

**✨ AI Intelligent Analysis Push Feature**

- **AI Analysis Integration**: Uses large AI models to deeply analyze push content, automatically generating hotspot trend overviews, keyword popularity analysis, cross-platform correlations, potential impact assessments, etc.
- **Sentiment Analysis**: Added deep sentiment recognition to accurately capture positive/negative, controversial, or concerned public opinions
- **Multiple AI Providers Support**: Supports DeepSeek (default, highly cost-effective), OpenAI, Google Gemini, and any OpenAI-compatible interfaces
- **Two Push Modes**: `only_analysis` (AI analysis only), `both` (push both)
- **Custom Prompts**: Customize the AI analysis role and output format via the `config/ai_analysis_prompt.txt` file
- **Multi-dimensional Data Analysis**: AI can analyze ranking changes, popularity duration, cross-platform performance, trend predictions, etc.

**📋 Independent Display Area Features**

- **Complete Trending List Display**: The complete trending list of specified platforms is displayed independently, unaffected by keyword filtering
- **Independent RSS Display**: RSS feed content can be displayed completely, suitable for feeds with less content
- **Flexible Configuration**: Supports configuring the display platform list, RSS feed list, and maximum number of items to display

**📊 Push Experience Refactoring**

- **Layout Upgrade**: Redesigned and unified the statistics header for all channels, strengthened block organization, making the message hierarchy clear at a glance
- **Configuration Simplification**: Optimized the configuration logic for notification channels like Feishu, making it easier to get started
- **Popularity Trend Arrows**: Added 🔺(Up), 🔻(Down), ➖(Flat) trend indicators to visually display popularity changes
- **Universal Webhook**: Supports custom Webhook URLs and JSON templates, easily adapting to any platform like Discord, Matrix, IFTTT, etc.

**🔧 Configuration Optimization**

- **Frequency Word Configuration Enhancement**: Added `[Group Name]` syntax, supports `#` comment lines, making configuration clearer (Thanks to [@songge8](https://github.com/sansan0/TrendRadar/issues/752) for the suggestion)
- **Environment Variable Support**: AI analysis related configurations support environment variable overrides (`AI_API_KEY`, `AI_PROVIDER`, etc.)

> 💡 For detailed configuration tutorials, see [Let AI Help Me Analyze Trending Topics](#12-Let-ai-help me analyze hot spots)


### 2026/01/02 - v4.7.0

- **Fix RSS HTML Display**: Fixed rendering issues caused by RSS data format mismatch, now correctly displayed grouped by keywords
- **New Regular Expression Syntax**: Keyword configuration supports `/pattern/` regex syntax, solving the issue of false matches with English substrings (e.g., `ai` matching `training`) [📖 View Syntax Details](#Keyword Basic Syntax)
- **New Display Name Syntax**: Use `=> Remark` to give complex regular expressions an easy-to-remember name, making push messages clearer (e.g., `/\bai\b/ => AI Related`)
- **Don't know how to write regex?** README adds a guide for AI-generated regex, tell ChatGPT/Gemini/DeepSeek what you want to match, and let AI write it for you


### 2025/12/30 - mcp-v2.0.0

- **Architecture Adjustment**: Removed TXT support, unified to use SQLite database
- **RSS Query**: Added `get_latest_rss`, `search_rss`, `get_rss_feeds_status`
- **Unified Search**: `search_news` supports the `include_rss` parameter to search both trending lists and RSS simultaneously


### 2026/01/01 - v4.6.0

- **Fix RSS HTML Display**: Merged RSS content into the trending list HTML page, displayed grouped by source
- **New display_mode Configuration**: Supports two display modes: `keyword` (grouped by keyword) and `platform` (grouped by platform)


### 2025/12/30 - v4.5.0

- **RSS Feed Support**: Added RSS/Atom fetching, grouped and counted by keywords (consistent with the trending list format)
- **Storage Structure Refactoring**: Flattened directory structure `output/{type}/{date}.db`
- **Unified Sorting Configuration**: `sort_by_position_first` affects both trending lists and RSS
- **Configuration Structure Refactoring**: `config.yaml` is reorganized into 7 logical groups (app, report, notification, storage, platforms, rss, advanced), making configuration paths clearer


### 2025/12/26 - mcp-v1.2.0

  **MCP Module Update - Optimized toolset, added aggregation and comparison features, merged redundant tools:**
  - Added `aggregate_news` tool - Cross-platform news deduplication and aggregation
  - Added `compare_periods` tool - Period comparison analysis (week-over-week/month-over-month)
  - Merged `find_similar_news` + `search_related_news_history` → `find_related_news`
  - Enhanced `get_trending_topics` - Added `auto_extract` mode to automatically extract trending topics
  - Fixed several bugs
  - Synchronously updated the Chinese and English versions of the README-MCP-FAQ.md document (Q1-Q18)


### 2025/12/20 - v4.0.3

- Added URL standardization feature to solve duplicate push issues caused by dynamic parameters (e.g., `band_rank`) on platforms like Weibo
- Fixed incremental mode detection logic to correctly identify historical titles


### 2025/12/17 - v4.0.1

- StorageManager added push record proxy methods
- Switched S3 client to virtual-hosted style to improve compatibility (supports more services like Tencent Cloud COS)


### 2025/12/13 - mcp-v1.1.0

  **MCP Module Update:**
  - Adapted to v4.0.0, while also compatible with v3.x data
  - Added storage synchronization tools: `sync_from_remote`, `get_storage_status`, `list_available_dates`


### 2025/12/13 - v4.0.0

**🎉 Major Update: Comprehensive Refactoring of Storage and Core Architecture**

- **Multiple Storage Backend Support**: Introduced a brand new storage module supporting local SQLite and remote cloud storage (S3-compatible protocols, e.g., Cloudflare R2), suitable for GitHub Actions, Docker, and local environments.
- **Database Structure Optimization**: Refactored the SQLite database table structure to improve data efficiency and query capabilities.
- **Core Code Modularization**: Split the main program logic into multiple modules within the trendradar package, significantly improving code maintainability.
- **Enhanced Features**: Implemented date format standardization, data retention policies, timezone configuration support, and time display optimization; fixed remote storage data persistence issues to ensure the accuracy of data merging.
- **Cleanup and Compatibility**: Removed most legacy compatibility code, unifying data storage and reading methods.


### 2025/12/03 - v3.5.0

**🎉 Core Feature Enhancements**

1. **Multi-Account Push Support**
   - All push channels (Feishu, DingTalk, WeChat Work, Telegram, ntfy, Bark, Slack) support multi-account configuration
   - Use a semicolon `;` to separate multiple accounts, for example: `FEISHU_WEBHOOK_URL=url1;url2`
   - Automatically verify the consistency in the number of paired configurations (such as Telegram's token and chat_id)

2. **Push Region Configuration**
   - Customize the display order of each region via `display.region_order` (replaced the original `reverse_content_order` in v5.2.0)
   - Control whether each region is displayed via `display.regions` (Hot List, New Hot Topics, RSS, Independent Display Area, AI Analysis)

3. **Global Filter Keywords**
   - Added `[GLOBAL_FILTER]` region tag, supporting global filtering of unwanted content
   - Applicable scenarios: filtering ads, marketing, low-quality content, etc.

**🐳 Docker Dual-Path HTML Generation Optimization**

- **Bug Fix**: Resolved the issue where `index.html` could not be synchronized to the host machine in the Docker environment
- **Dual-Path Generation**: The daily summary HTML is simultaneously generated in two locations
  - `index.html` (project root directory): For GitHub Pages access
  - `output/index.html`: Mounted via Docker Volume, directly accessible by the host machine
- **Compatibility**: Ensure that Docker, GitHub Actions, and local runtime environments can all normally access the web version of the report

**🐳 Docker MCP Image Support**

- Added an independent MCP service image `wantcat/trendradar-mcp`
- Supports Docker deployment of AI analysis features, providing services via HTTP interface (port 3333)
- Dual-container architecture: News push service and MCP service run independently, and can be scaled and restarted separately
- See [Docker Deployment - MCP Service](#6-docker-deployment) for details

**🌐 Web Server Support**

- Added built-in Web server, supporting browser access to generated reports
- Control start/stop via `manage.py` command: `docker exec -it trendradar python manage.py start_webserver`
- Access address: `http://localhost:8080` (port is configurable)
- Security features: Static file service, directory restrictions, local access
- Supports both automatic startup and manual control modes

**📖 Documentation Optimization**

- Added [How is the push content displayed?](#7-How is the push content displayed) section: Customize push style and content
- Added [When will it push to me?](#8-WHEN will it push to me) section: Set push time periods
- Added [How often does it run?](#9-How often) section: Set automatic run frequency
- Added [Push to multiple groups/devices](#10-Push to multiple groups/devices) section: Push to multiple recipients simultaneously
- Optimized configuration sections: Uniformly added "Configuration Location" instructions
- Simplified quick start configuration instructions: three core files at a glance
- Optimized [Docker Deployment](#6-docker-deployment) section: added image instructions, recommended git clone deployment, reorganized deployment methods

**🔧 Upgrade Instructions**:
- **GitHub Fork Users**: Update `main.py`, `config/config.yaml` (added multi-account push support, no need to modify existing configuration)
- **Multi-account Push**: New feature, disabled by default, existing single-account configuration is not affected


### 2025/11/26 - mcp-v1.0.3

  **MCP Module Update:**
  - Added date parsing tool resolve_date_range to solve the issue of inconsistent date calculations by AI models
  - Supports parsing natural language date expressions (this week, last 7 days, last month, etc.)
  - Total number of tools increased from 13 to 14


### 2025/11/28 - v3.4.1

**🔧 Format Optimization**

1. **Bark Push Enhancement**
   - Bark now supports Markdown rendering
   - Enabled native Markdown formatting: bold, links, lists, code blocks, etc.
   - Removed plain text conversion to fully utilize Bark's native rendering capabilities

2. **Slack Format Refinement**
   - Use dedicated mrkdwn format to process batched content
   - Improved byte size estimation accuracy (to avoid message size limits)
   - Optimized link format: `<url|text>` and bold syntax: `*text*`

3. **Performance Improvement**
   - Format conversion is completed during the batching process to avoid secondary processing
   - Accurately estimate message size to reduce send failure rate

**🔧 Upgrade Instructions**:
- **GitHub Fork Users**: Update `main.py`, `config.yaml`


### 2025/11/25 - v3.4.0

**🎉 Added Slack Push Support**

1. **Team Collaboration Push Channel**
   - Supports Slack Incoming Webhooks (a globally popular team collaboration tool)
   - Centralized message management, suitable for teams to share trending news
   - Supports mrkdwn format (bold, links, etc.)

2. **Multiple Deployment Methods**
   - GitHub Actions: Configure `SLACK_WEBHOOK_URL` Secret
   - Docker: Environment variable `SLACK_WEBHOOK_URL`
   - Local Run: `config/config.yaml` configuration file


> 📖 **Detailed Configuration Tutorial**: [Quick Start - Slack Push](#-Quick Start)

- Optimized the one-click MCP installation experience for setup-windows.bat and setup-windows-en.bat

**🔧 Upgrade Instructions**:
- **GitHub Fork Users**: Update `main.py`, `config/config.yaml`, `.github/workflows/crawler.yml`


### 2025/11/24 - v3.3.0

**🎉 Added Bark Push Support**

1. **iOS Exclusive Push Channel**
   - Supports Bark push (based on APNs, iOS platform)
   - Free and open-source, simple and efficient, no ad interference
   - Supports both official and self-hosted servers

2. **Multiple deployment methods**
   - GitHub Actions: Configure `BARK_URL` Secret
   - Docker: Environment variable `BARK_URL`
   - Local execution: `config/config.yaml` configuration file

> 📖 **Detailed configuration tutorial**: [Quick Start - Bark Push](#-Quick Start)

**🐛 Bug Fixes**
- Fixed the issue where the `ntfy_server_url` configuration in `config.yaml` did not take effect ([#345](https://github.com/sansan0/TrendRadar/issues/345))

**🔧 Upgrade Instructions**:
- **GitHub Fork Users**: Update `main.py`, `config/config.yaml`, `.github/workflows/crawler.yml`

### 2025/11/23 - v3.2.0

**🎯 New Advanced Customization Features**

1. **Keyword sorting priority configuration**
   - Supports two sorting strategies: popularity first vs. configuration order first
   - Meets different usage scenarios: hotspot tracking or personalized following

2. **Precise control of display quantity**
   - Global configuration: Uniformly limit the display quantity of all keywords
   - Individual configuration: Use the `@number` syntax to set limits for specific keywords
   - Effectively control push length and highlight key content

> 📖 **Detailed configuration tutorial**: [Keyword Configuration - Advanced Configuration](#Keyword Advanced Configuration)

**🔧 Upgrade Instructions**:
- **GitHub Fork Users**: Update `main.py`, `config/config.yaml`


### 2025/11/18 - mcp-v1.0.2

  **MCP Module Updates:**
  - Optimized the issue where querying today's news might incorrectly return past dates


### 2025/11/22 - v3.1.1

- **Fixed crash caused by data anomalies**: Resolved the `'float' object has no attribute 'lower'` error encountered by some users in the GitHub Actions environment
- Added dual protection mechanism: filter invalid titles (None, float, empty strings) during the data acquisition phase, and add type checking at function calls
- Improved system stability to ensure normal operation even when data sources return abnormal formats

**Upgrade Instructions** (GitHub Fork Users):
- Must update: `main.py`
- Recommended to use the minor version upgrade method: copy and replace the above files


### 2025/11/20 - v3.1.0

- **Added support for personal WeChat push**: WeChat Work apps can push to personal WeChat without installing the WeChat Work APP
- Supports two message formats: `markdown` (WeChat Work group bot) and `text` (personal WeChat app)
- Added `WEWORK_MSG_TYPE` environment variable configuration, supporting multiple deployment methods such as GitHub Actions, Docker, and docker compose
- `text` mode automatically clears Markdown syntax, providing a plain text push effect
- See the "Personal WeChat Push" configuration instructions in the Quick Start for details

**Upgrade Instructions** (GitHub Fork Users):
- Must update: `main.py`, `config/config.yaml`
- Optional update: `.github/workflows/crawler.yml` (if deployed using GitHub Actions)
- Recommended to use the minor version upgrade method: copy and replace the above files

### 2025/11/12 - v3.0.5

- Fixed logic error in email sending SSL/TLS port configuration
- Optimized email service providers (QQ/163/126) to use port 465 (SSL) by default
- **Added Docker environment variable support**: Core configuration items (`enable_crawler`, `report_mode`, `push_window`, etc.) support being overridden via environment variables, solving the issue where modifying the configuration file does not take effect for NAS users (see the [🐳 Docker Deployment](#-docker- deploy) section for details)


### 2025/10/26 - mcp-v1.0.1

  **MCP module update:**
  - Fixed date query parameter passing error
  - Unified time parameter format for all tools


### 2025/10/31 - v3.0.4

- Resolved the error caused by Feishu push content being too long, implemented batch pushing


### 2025/10/23 - v3.0.3

- Expanded the display scope of ntfy error messages


### 2025/10/21 - v3.0.2

- Fixed ntfy push encoding issue

### 2025/10/20 - v3.0.0

**Major Update - AI Analysis Feature Launched** ✨

- **Core Features**:
  - Added AI analysis server based on MCP (Model Context Protocol)
  - Supports 17 intelligent analysis tools: basic query, smart retrieval, advanced analysis, RSS query, system management
  - Natural language interaction: Query and analyze news data through conversation
  - Multi-client support: Claude Desktop, Cherry Studio, Cursor, Cline, etc.

- **Analysis Capabilities**:
  - Topic trend analysis (popularity tracking, lifecycle, viral detection, trend prediction)
  - Data insights (platform comparison, activity statistics, keyword co-occurrence)
  - Sentiment analysis, similar news search, smart summary generation
  - Historical related news retrieval, multi-mode search

- **Update Notes**:
  - This is an independent AI analysis feature, does not affect existing push functions
  - Optional to use, no need to upgrade existing deployments


### 2025/10/15 - v2.4.4

- **Update Content**:
    - Fixed ntfy push encoding issue + 1
    - Fixed push time window judgment issue

- **Update Notes**:
  - Recommended [Minor version upgrade]


### 2025/10/10 - v2.4.3

> Thanks to [nidaye996](https://github.com/sansan0/TrendRadar/issues/98) for discovering the user experience issue

- **Update Content**:
    - Refactored "Silent Push Mode" to "Push Time Window Control" to improve feature understanding
    - Clarified that the push time window is an optional add-on feature that can be used with the three push modes
    - Improved comments and documentation descriptions to make feature positioning clearer

- **Update Notes**:
  - This is just a refactoring, no need to upgrade


### 2025/10/8 - v2.4.2

- **Update Content**:
    - Fixed ntfy push encoding issue
    - Fixed missing configuration file issue
    - Optimized ntfy push effect
    - Added GitHub Pages image segmented export feature

- **Update Notes**:
  - Recommended to use [Major version update]


### 2025/10/2 - v2.4.0

**Added ntfy push notifications**

- **Core features**:
  - Supports ntfy.sh public service and self-hosted servers

- **Use cases**:
  - Suitable for privacy-conscious users (supports self-hosting)
  - Cross-platform push (iOS, Android, Desktop, Web)
  - No account registration required (public servers)
  - Free and open-source (MIT License)

- **Update notes**:
  - Recommended to use [Major Version Update]


### 2025/09/26 - v2.3.2

- Fixed an issue where email notification configuration checks were missed ([#88](https://github.com/sansan0/TrendRadar/issues/88))

**Fix details**:
- Resolved the issue where the system still prompted "No webhook configured" even when email notifications were correctly configured

### 2025/09/22 - v2.3.1

- **Added email push feature**, supporting sending trending news reports to email
- **Smart SMTP recognition**: Automatically recognizes configurations for 10+ email providers such as Gmail, QQ Mail, Outlook, NetEase Mail, etc.
- **Beautiful HTML formatting**: Email content uses the same HTML format as the web version, with beautiful typography and mobile adaptation
- **Batch sending support**: Supports multiple recipients, simply separate with commas to send to multiple people simultaneously
- **Custom SMTP**: Customizable SMTP server and port
- Fixed Docker build network connection issues

**Usage instructions**:
- Applicable scenarios: Suitable for users who need email archiving, team sharing, and scheduled reports
- Supported emails: Gmail, QQ Mail, Outlook/Hotmail, 163/126 Mail, Sina Mail, Sohu Mail, etc.

**Update notes**:
- This update contains many changes. If you want to upgrade, it is recommended to use [Major Version Upgrade]

### 2025/09/17 - v2.2.0

- Added one-click save news as image feature, allowing you to easily share trending topics you follow

**Usage instructions**:
- Applicable scenarios: After you have enabled the web version feature according to the tutorial (GitHub Pages)
- How to use: Open the web link on your phone or computer, and click the "Save as Image" button at the top of the page
- Actual effect: The system will automatically generate a beautiful image of the current news report and save it to your phone album or computer desktop
- Sharing convenience: You can directly send this image to friends, post it on Moments, or share it in work groups, so others can also see the important information you discovered

### 2025/09/13 - v2.1.2

- Resolved the issue of news push failures caused by DingTalk's push capacity limits (using batch pushing)

### 2025/09/04 - v2.1.1

- Fixed the issue where docker could not run properly on certain architectures
- Officially released the official Docker image wantcat/trendradar, supporting multiple architectures
- Optimized the Docker deployment process, allowing quick use without local building

### 2025/08/30 - v2.1.0

**Core improvements**:
- **Push logic optimization**: Changed from "push on every execution" to "controllable push within a time window"
- **Time window control**: Can set a push time range to avoid disturbances during non-working hours
- **Selectable push frequency**: Supports single or multiple pushes within the time period

**Update notes**:
- This feature is disabled by default and requires manually enabling the push time window control in config.yaml
- Upgrading requires updating both main.py and config.yaml files simultaneously

### 2025/08/27 - v2.0.4

- This version is not a feature fix, but an important reminder
- Please be sure to keep your webhooks safe, do not make them public, do not make them public, do not make them public
- If you deploy this project on GitHub by forking, please fill the webhooks into GitHub Secret instead of config.yaml
- If you have already exposed your webhooks or filled them into config.yaml, it is recommended to delete and regenerate them

### 2025/08/06 - v2.0.3

- Optimized the web version effect of github page for easier mobile use

### 2025/07/28 - v2.0.2

- Refactored code
- Solved the issue where the version number was easily forgotten to be modified

### 2025/07/27 - v2.0.1

**Fixes**:

1. Execution exception caused by CRLF line endings in the docker shell script
2. Logic issue where empty frequency_words.txt resulted in empty news sending
  - After the fix, when you choose to leave frequency_words.txt empty, it will **push all news**, but due to message push size limits, please make the following adjustments
    - Option 1: Turn off mobile push and only choose Github Pages deployment (this is the option to get the most complete information, it will reorder the hot topics of all platforms according to your **custom hot search algorithm**)
    - Option 2: Reduce push platforms, prioritize **WeCom** or **Telegram**. I have implemented a batch push feature for these two (because batch push affects the push experience, and only these two platforms provide very little push capacity, so I had to implement the batch push feature, but at least it guarantees the information obtained is complete)
    - Option 3: Can be combined with Option 2, selecting current or incremental mode can effectively reduce the content pushed at one time

### 2025/07/17 - v2.0.0

**Major Refactoring**:
- Configuration management refactoring: All configurations are now managed through the `config/config.yaml` file (I still haven't split main.py, to make it easier for you to copy and upgrade)
- Run mode upgrade: Supports three modes - `daily` (daily summary), `current` (current ranking), `incremental` (incremental monitoring)
- Docker support: Complete Docker deployment solution, supporting containerized execution

**Configuration File Description**:
- `config/config.yaml` - Main configuration file (application settings, crawler configuration, notification configuration, platform configuration, etc.)
- `config/frequency_words.txt` - Keyword configuration (monitoring vocabulary settings)

### 2025/07/09 - v1.4.1

**New Feature**: Added incremental push (configure FOCUS_NEW_ONLY at the top of main.py), this switch only cares about new topics rather than sustained popularity, and only sends notifications when there is new content.

**Fixes**: Occasional layout anomalies caused by special symbols in the news itself in some cases.

### 2025/06/23 - v1.3.0

WeCom and Telegram push messages have length limits, for which I adopted the method of splitting the messages for pushing. For development documentation, see [WeCom](https://developer.work.weixin.qq.com/document/path/91770) and [Telegram](https://core.telegram.org/bots/api)

### 2025/06/21 - v1.2.1

In older versions before this version, not only main.py needs to be copied and replaced, but crawler.yml also needs you to copy and replace
https://github.com/sansan0/TrendRadar/blob/master/.github/workflows/crawler.yml

### 2025/06/19 - v1.2.0

> Thanks to claude research for organizing the APIs of various platforms, allowing me to quickly complete the adaptation for each platform (although the code is more redundant now~

1. Support telegram, WeCom, DingTalk push channels, support multi-channel configuration and simultaneous push

### 2025/06/18 - v1.1.0

> **200 stars⭐**, continuing to add to the fun for everyone~ Recently, under my "encouragement", many people liked, shared, and recommended to support me on my official account. I saw the encouragement data of specific accounts in the background, and many have become angel-round veteran fans (I've only been running the official account for over a month, although I registered it seven or eight years ago haha, which means I got on the bus early but departed late). However, because you didn't leave a message or private message me, I couldn't respond and thank you for your support one by one, so thank you all here!

1. Important update, added weights, the news you see now are the hottest and most followed appearing at the top
2. Updated usage documentation, because many features have been updated recently, and I was lazy and wrote the previous usage documentation too simply (see the complete tutorial for ⚙️ frequency_words.txt configuration below)

### 2025/06/16 - v1.0.0

1. Added a project new version update prompt, turned on by default, if you want to turn it off, you can change True to False in "FEISHU_SHOW_VERSION_UPDATE": True in main.py

### 2025/06/13+14

1. Removed compatibility code, for users who forked before, directly copying the code will display abnormally on the same day (it will return to normal the next day)
2. Added a new news display at the bottom of feishu and html

### 2025/06/09

**100 stars⭐**, wrote a small feature to add to the fun for everyone
Added a [Must-have Word] feature to the frequency_words.txt file, using the + sign

1. The syntax for must-have words is as follows:
   Tang Seng and Zhu Bajie must appear in the title at the same time to be included in the pushed news

```
+Tang Seng
+Zhu Bajie
```

2. Filter words have higher priority:
   If a filter word matches "Tang Monk chanting" in the title, it will not be displayed even if the required words include "Tang Monk"

```
+Tang Monk
!Tang Monk chanting
```

### 2025/06/02

1. **Webpages** and **Feishu messages** support direct redirection to news details on mobile
2. Optimized display effect + 1

### 2025/05/26

1. Optimized Feishu message display effect

<table>
<tr>
<td align="center">
Before optimization<br>
<img src="_image/before.jpg" alt="Feishu message interface - Before optimization" width="400"/>
</td>
<td align="center">
After optimization<br>
<img src="_image/after.jpg" alt="Feishu message interface - After optimization" width="400"/>
</td>
</tr>
</table>

</details>

<br>

## ✨ Core Features

### **All-Network Hot Trends Aggregation**

- Zhihu
- Douyin
- Bilibili Hot Search
- Wallstreetcn
- Tieba
- Baidu Hot Search
- Cailianshe Hot
- The Paper
- iFeng
- Toutiao
- Weibo

Monitors 11 mainstream platforms by default, and you can also add additional platforms yourself

> 💡 For detailed configuration tutorials, see [Configuration Details - Platform Configuration](#1-Platform Configuration)

### **RSS Feed Support** (New in v4.5.0)

Supports fetching RSS/Atom feeds, grouped and counted by keywords (consistent with the hotlist format):

- **Unified format**: RSS and hotlists use the same keyword matching and display format
- **Simple configuration**: Add RSS feeds directly in `config.yaml`
- **Merged push**: Hotlists and RSS are merged into a single message for push
- **Freshness filtering**: Automatically filters out old articles exceeding a specified number of days to avoid duplicate pushes. Supports global default days and independent settings per feed

> 💡 RSS uses the same `frequency_words.txt` as the hotlist for keyword filtering

### **Visual Configuration Editor**

Provides a Web-based graphical configuration interface. No need to manually edit YAML files; you can modify and export all configuration items through forms.

👉 **Online Experience**: [https://sansan0.github.io/TrendRadar/](https://sansan0.github.io/TrendRadar/)

<img src="/_image/editor.png" alt="Visual Configuration Editor" width="80%">

### **Smart Push Strategy**

**Three push modes**:

| Mode | Applicable Scenarios | Push Features |
|------|---------|---------|
| **Daily Summary** (daily) | Enterprise Managers/Regular Users | Pushes all matching news for the day on schedule (includes previously pushed items) |
| **Current Rankings** (current) | Independent Media/Content Creators | Pushes matching news from the current rankings on schedule (items staying on the list appear every time) |
| **Incremental Monitoring** (incremental) | Investors/Traders | Only pushes new content, zero repetition |

> 💡 **Quick Selection Guide:**
> - Don't want to see duplicate news → Use `incremental` (Incremental Monitoring)
> - Want to see complete ranking trends → Use `current` (Current Rankings)
> - Need a daily summary report → Use `daily` (Daily Summary)
>
> For detailed comparison and configuration tutorials, see [Detailed Configuration - Push Modes Explained](#3-Push Modes Explained)

**Additional Features** (Optional):

| Feature | Description | Default |
|------|------|------|
| **Scheduling System** | Daily orchestration from Monday to Sunday: assigns different time periods, push modes, and AI analysis strategies for each day. **Each period can independently set filtering methods (keyword/AI) and focus areas**, allowing you to read different types of news at different times. Built-in 5 presets (always_on / morning_evening / office_hours / night_owl / custom), also customizable. Supports weekday/weekend differentiation, cross-midnight periods, per-period deduplication, and period conflict detection (v6.0.0 + v6.5.0) | morning_evening |
| **Content Order Configuration** | Adjust the display order of each region (Hot List, New Hot Topics, RSS, Independent Display Area, AI Analysis) via `display.region_order`; control whether each region is displayed via `display.regions` (v5.2.0) | See config file |
| **Display Mode Switching** | `keyword`=Group by keyword, `platform`=Group by platform (Added in v4.6.0) | keyword |

> 💡 For detailed configuration tutorials, see [How is the push content displayed?](#7-How to display push content) and [When will it push to me?](#8-WHEN will it be pushed to me)

### **Precise Content Filtering**

Set personal keywords (e.g., AI, BYD, education policy) to only push related hot topics and filter out irrelevant information

> 💡 **Basic Configuration Tutorial**: [Keyword Configuration - Basic Syntax](#Keyword Basic Syntax)
>
> 💡 **Advanced Configuration Tutorial**: [Keyword Configuration - Advanced Configuration](#Keyword Advanced Configuration)
>
> 💡 You can also choose not to filter and push all hot topics completely (leave frequency_words.txt empty)

### **AI Intelligent News Filtering** (Added in v6.5.0)

Describe your interests in natural language, and AI will automatically categorize news, replacing traditional keyword matching

- **Natural Language Interest Description**: Write down your focus areas in everyday language in `ai_interests.txt`, no need to learn keyword syntax
- **Two-Stage Intelligent Processing**: AI first extracts structured tags from interest descriptions, then batch categorizes and scores news by tags
- **Score Threshold Control**: Precisely control push quality via `ai_filter.min_score`, only pushing highly relevant news
- **Automatic Fallback Guarantee**: Automatically falls back to keyword matching when AI filtering fails, ensuring uninterrupted pushes
- **Intelligent Tag Updates**: When interests change, AI automatically evaluates the extent of the change to decide on incremental or full re-categorization
- **Flexible Switching**: `filter.method` supports both `keyword` (default) and `ai` modes, Timeline can override by time period
- **Time-Period Personalization**: Different time periods can use different keyword files or AI interest descriptions. For example, use a "tech vocabulary" for quick filtering in the morning, and switch to "financial interests" for deep AI filtering at night

```yaml
# config.yaml quick start example
filter:
  method: ai          # keyword (default) | ai
ai_filter:
  min_score: 6         # Minimum score threshold for pushing (1-10)
```

> 💡 AI filtering shares model configuration with AI analysis/translation, only need to configure `ai.api_key` once

### **Hot Topic Trend Analysis**

Track news popularity changes in real-time, letting you not only know "what's trending" but also understand "how hot topics evolve"

- **Timeline Tracking**: Record the complete time span of each news item from its first appearance to its last
- **Popularity Changes**: Count the ranking changes and appearance frequency of news across different time periods
- **New Addition Detection**: Identify newly emerged hot topics in real-time, using the 🆕 tag for immediate alerts
- **Persistence Analysis**: Distinguish between one-off hot topics and continuously developing in-depth news
- **Cross-Platform Comparison**: The ranking performance of the same news across different platforms, revealing differences in media attention

> 💡 For push format instructions, see [Message Style Instructions](#5-What does the message I receive look like)

### **Personalized Trending Algorithm**

No longer led by the algorithms of various platforms, TrendRadar will reorganize trending searches across the entire internet

> 💡 The three ratios can be adjusted, see [Configuration Details - Trending Weight Adjustment](#4-Hotspot Weight Adjustment) for details

### **Multi-channel and Multi-account Push**

Supports **WeCom** (+ WeChat push solution), **Feishu**, **DingTalk**, **Telegram**, **Email**, **ntfy**, **Bark**, **Slack**, **General Webhook** (can connect to Discord, IFTTT, and any other platforms), delivering messages directly to your phone and email

> 💡 For detailed configuration tutorials, see [Push to Multiple Groups/Devices](#10-Push to multiple group devices)

### **AI Multi-language Translation** (New in v5.2.0)

Translate push content into any language, breaking language barriers. Whether reading domestic trending topics or subscribing to overseas news via RSS, you can easily access them in your native language

- **One-click Translation**: Simply set `ai_translation.enabled: true` and the target language in `config.yaml`
- **Multi-language Support**: Supports any language such as English, Korean, Japanese, French, etc.
- **Smart Batch Processing**: Automatically translates in batches, reducing API calls and saving costs
- **Custom Style**: Customize translation style and terminology via `ai_translation_prompt.txt`
- **Shared Model Configuration**: Shares the model settings in the `ai` configuration section with the AI analysis feature

```yaml
# config.yaml quick start example
ai_translation:
  enabled: true
  language: "English"  # Target translation language
```

> 💡 The translation feature shares the model configuration with the AI analysis feature, you only need to configure `ai.api_key` once to use both features simultaneously

**RSS Feed Reference**: Below are some RSS feed collections that can be used as needed
- [awesome-tech-rss](https://github.com/tuan3w/awesome-tech-rss) - Blogs and media in technology, entrepreneurship, and programming
- [awesome-rss-feeds](https://github.com/plenaryapp/awesome-rss-feeds) - RSS collection of mainstream news media from around the world

> ⚠️ Some overseas media content may involve sensitive topics, and AI models may refuse to translate. It is recommended to filter subscription feeds based on actual needs

### **HTML Report Browser Enhancement** (New in v6.6.0)

Open the pushed HTML report in a browser to automatically unlock an enhanced experience (email clients are not affected):

- **Widescreen Mode**: Automatically switches to a 1200px widescreen layout on desktop, fully utilizing screen space
- **Quick Tab Switching**: Both keyword grouping and independent exhibition areas support Tab navigation, saying goodbye to long page scrolling
- **Dark Mode**: One-click switch to dark theme, automatically remembers preferences
- **Real-time Search**: Press `/` to bring up the search box, instantly filtering news titles
- **One-click Copy**: Hover over the news number to copy the title and link
- **Shortcuts**: `W` for widescreen, `D` for dark mode, `/` for search, `?` to view all shortcuts

> 💡 All enhanced features are based on progressive enhancement, email clients still display the original 600px layout, zero regressions

### **Flexible Storage Architecture** (Major update in v4.0.0)

**Multi-storage Backend Support**:
- **Remote Cloud Storage**: Default for GitHub Actions environment, supports S3-compatible protocols (R2/OSS/COS, etc.), data is stored in the cloud, without polluting the repository
- **Local SQLite Database**: Default for Docker/local environments, data is fully controllable
- **Automatic Backend Selection**: Intelligently switches storage methods based on the running environment

> 💡 For detailed instructions, see [Where is the data saved?](#11-Where is the data saved?)

### **Multi-platform Deployment**
- **GitHub Actions**: Scheduled automatic crawling + remote cloud storage (requires check-in for renewal)
- **Docker Deployment**: Supports multi-architecture containerized execution, local data storage
- **Local Execution**: Run directly on Windows/Mac/Linux


### **AI Analysis Push (New in v5.0.0)**

Use large AI models to conduct deep analysis of pushed content and automatically generate trending insight reports

- **Intelligent Analysis**: Automatically analyze hot trends, keyword popularity, cross-platform correlations, and potential impacts
- **Multiple Providers**: Based on the LiteLLM unified interface, supports 100+ AI providers (DeepSeek, OpenAI, Gemini, Anthropic, local Ollama, etc.), and also supports automatic fallback model switching
- **Independent Analysis Mode**: The AI's analysis scope can differ from the push—the push only sends new messages (to avoid disturbance), but the AI can analyze all news of the day (to see the complete trend)
- **Flexible Push**: Choose to push only original content, only AI analysis, or both
- **Custom Prompts**: Customize analysis perspectives via `config/ai_analysis_prompt.txt`

> 💡 For detailed configuration tutorials, see [Let AI Help Me Analyze Trends](#12-Let-ai-help me analyze hot spots)

### **Independent Display Area (New in v5.0.0)**

Provide a complete trending list display for specified platforms, unaffected by keyword filtering

- **Complete Trending List**: Complete display of the trending list for specified platforms, suitable for users who want to see the full rankings
- **Independent RSS Display**: RSS feed content can be displayed completely, unrestricted by keywords
- **Deep AI Analysis**: Independently enable AI trend analysis on the complete trending list without displaying it in the push
- **Flexible Configuration**: Support configuring display platforms, RSS feeds, and maximum item counts

> 💡 For detailed configuration tutorials, see [How is the pushed content displayed? - Independent Display Area](#7-How is the pushed content displayed)

### **AI Intelligent Analysis (New in v3.0.0)**

An AI dialogue analysis system based on the MCP (Model Context Protocol) protocol, allowing you to deeply mine news data using natural language

> **💡 Usage Tip**: AI features require local news data support
> - The project comes with test data, allowing you to experience the features immediately
> - It is recommended to deploy and run the project yourself to get more real-time data
>
> For details, see [AI Intelligent Analysis](#-ai-INTELLIGENT ANALYSIS)

### **Web Deployment**

After running, an `index.html` is generated in the root directory, which is the complete news report page.

> **Deployment Method**: Click **Use this template** to create a repository, which can be deployed to static hosting platforms like Cloudflare Pages or GitHub Pages.
>
> **💡 Tip**: Enable GitHub Pages to get an online access address; go to repository Settings → Pages to turn it on. [Preview Effect](https://sansan0.github.io/TrendRadar/)
>
> ⚠️ The original GitHub Actions automatic storage feature has been taken offline (this solution previously caused high load on GitHub servers, affecting platform stability).

### **Reduce APP Dependency**

Shift from "being kidnapped by algorithmic recommendations" to "proactively acquiring the information you want"

**Target Audience:** Investors, self-media creators, corporate PR, and ordinary users who care about current affairs

**Typical Scenarios:** Stock market investment monitoring, brand public opinion tracking, industry dynamics attention, and lifestyle information acquisition


| Web Page Effect (Email Push Effect) | Feishu Push Effect | AI Analysis Push Effect |
|:---:|:---:|:---:|
| ![Web Page Effect](_image/github-pages.png) | ![Feishu Push Effect](_image/feishu.jpg) | ![AI Analysis Push Effect](_image/ai.jpg) |


<br>

## 🚀 Quick Start

> **Reminder**: It is recommended to first **[check the latest official documentation](https://github.com/sansan0/TrendRadar?tab=readme-ov-file)** to ensure the configuration steps are up to date.

### Please choose the deployment method that suits you

#### 🅰️ Option 1: Docker Deployment (Recommended 🔥)

* **Features**: More stable than GitHub Actions, local data storage (no need to configure cloud storage)
* **Suitable for**: Those with their own servers, NAS, or long-running computers
* **Note**: You need to read and understand the basic configuration process below, then jump to the Docker tutorial for deployment.

#### 🅱️ Option 2: GitHub Actions Deployment (Content of this chapter ⬇️)

* **Features**: Serverless, data stored in **remote cloud storage** (recommended configuration)
* **Applicable to**: Users without a server, utilizing free GitHub resources
* **Note**: Cloud storage configuration is required for a complete experience, and regular check-ins are needed for renewal

### 1️⃣ Step 1: Get the project code

   Click the green **[Use this template]** button in the top right corner of this repository page → select "Create a new repository".

   > ⚠️ Reminder:
   > - "Fork" mentioned in the subsequent documentation can be understood as "Use this template"
   > - Using Fork may cause abnormal operation, see [Issue #606](https://github.com/sansan0/TrendRadar/issues/606) for details

   <br>

### 2️⃣ Step 2: Set up GitHub Secrets

   In your Forked repository, go to `Settings` > `Secrets and variables` > `Actions` > `New repository secret`

   **📌 Important Note (Please read carefully):**

   - **One Name corresponds to one Secret**: For each configuration item added, click the "New repository secret" button once and fill in a pair of "Name" and "Secret"
   - **It is normal not to see the value after saving**: For security reasons, when editing again after saving, you can only see the Name, not the content of the Secret (value)
   - **Do not create your own names**: The Name of the Secret must **strictly use** the names listed below (such as `WEWORK_WEBHOOK_URL`, `FEISHU_WEBHOOK_URL`, etc.). You cannot arbitrarily modify or create new names, otherwise the system will not recognize them
   - **Multiple platforms can be configured simultaneously**: The system will send notifications to all configured platforms

   **Configuration Example:**

   <img src="_image/secrets.png" alt="GitHub Secrets Configuration Example"/>

   As shown in the figure above, each line is a configuration item:
   - **Name**: Must use the fixed names listed in the expanded content below (such as `WEWORK_WEBHOOK_URL`)
   - **Secret (Value)**: Fill in the actual content you obtained from the corresponding platform (such as Webhook address, Token, etc.)

   <br>

   <details>
   <summary>👉 Click to expand: <strong>WeCom Bot</strong> (Simplest and fastest configuration)</summary>
   <br>

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `WEWORK_WEBHOOK_URL` (Please copy and paste this name, do not type it manually to avoid typos)
   - **Secret (Value)**: Your WeCom Bot Webhook address

   <br>

   **Bot Setup Steps:**

   #### Mobile Setup:
   1. Open the WeCom App → enter the target internal group chat
   2. Click the "..." button in the top right corner → select "Message Push"
   3. Click "Add" → enter "TrendRadar" as the name
   4. Copy the Webhook address, click save, and configure the copied content into the GitHub Secret above

   #### PC setup process is similar
   </details>

   <details>
   <summary>👉 Click to expand: <strong>Personal WeChat Push</strong> (Based on WeCom app, pushes to personal WeChat)</summary>
   <br>

   > Since this solution is based on the WeCom plugin mechanism, the push style is plain text (no markdown format), but it can be pushed directly to personal WeChat without installing the WeCom App.

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `WEWORK_MSG_TYPE` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your WeCom app Webhook address

   - **Name**: `WEWORK_MSG_TYPE` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: `text`

   <br>

   **Setup Steps:**

   1. Complete the WeCom Bot Webhook setup above
   2. Add the `WEWORK_MSG_TYPE` Secret and set the value to `text`
   3. Follow the image below to link your personal WeChat
   4. After configuration, the WeCom App on your phone can be deleted

   <img src="_image/wework.png" title="Personal WeChat Push Configuration"/>

   **Note**:
   - Uses the same Webhook address as the WeCom bot
   - The difference lies in the message format: `text` is plain text, `markdown` is rich text (default)
   - Plain text format will automatically remove all markdown syntax (bold, links, etc.)

   </details>

   <details>
   <summary>👉 Click to expand: <strong>Feishu Bot</strong> (Message display is relatively friendly)</summary>
   <br>

   If **AI Analysis** is enabled, Feishu push may occasionally (about 5% probability) have a delay of a few minutes (presumably due to the platform's compliance review of AI-generated content).

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `FEISHU_WEBHOOK_URL` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Feishu bot Webhook address (The link starts with something like https://www.feishu.cn/flow/api/trigger-webhook/********)
   <br>

   There are two options, **Option 1** is simple to configure, **Option 2** is complex to configure (but provides stable push)

   Option 1 was discovered and suggested by **ziventian**, thanks to him here. The default is personal push, but group push operations can also be configured [#97](https://github.com/sansan0/TrendRadar/issues/97) ,

   **Option 1:**

   > There are extra operations for some people, otherwise a "System Error" will be reported. You need to search for the bot on the mobile app, and then enable the Feishu bot application (This suggestion comes from netizens and can be used as a reference)

   1. Open https://botbuilder.feishu.cn/home/my-command in your computer browser

   2. Click "New Bot Command"

   3. Click "Select Trigger", scroll down, and click "Webhook Trigger"

   4. At this point, you will see the "Webhook Address". Copy this link to a local notepad temporarily, and continue with the next operations

   5. Put the following content in "Parameters", and then click "Complete"

   ```json
   {
     "message_type": "text",
     "content": {
       "text": "{{Content}}"
     }
   }
   ```

   6. Click "Select Action" > "Send message via official bot"

   7. Fill in "TrendRadar Hotspot Monitor" for the message title

   8. Here comes the most crucial part, click the + button, select "Webhook Trigger", and then arrange it according to the image below

   ![Feishu Bot Configuration Example](_image/feishu.png)

   9. After configuration is complete, configure the Webhook address copied in step 4 to `FEISHU_WEBHOOK_URL` in GitHub Secrets

   <br>

   **Option 2:**

   1. Open https://botbuilder.feishu.cn/home/my-app in your computer browser

   2. Click "New Bot Application"

   3. After entering the created application, click "Process Design" > "Create Process" > "Select Trigger"

   4. Scroll down and click "Webhook Trigger"

   5. At this point, you will see the "Webhook Address". Copy this link to a local notepad temporarily, and continue with the next operations

   6. Put the following content in "Parameters", and then click "Complete"

   ```json
   {
     "message_type": "text",
     "content": {
       "text": "{{Content}}"
     }
   }
   ```

   7. Click "Select Action" > "Send Feishu Message", check "Group Message", then click the input box below, and click "Groups I Manage" (If there are no groups, you can create a group on the Feishu app)

   8. Fill in "TrendRadar Hotspot Monitor" for the message title

   9. Here comes the most crucial part, click the + button, select "Webhook Trigger", and then arrange it according to the image below

   ![Feishu Bot Configuration Example](_image/feishu.png)

   10. After configuration is complete, configure the Webhook address copied in step 5 to `FEISHU_WEBHOOK_URL` in GitHub Secrets

   </details>

   <details>
   <summary>👉 Click to expand: <strong>DingTalk Bot</strong></summary>
   <br>

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `DINGTALK_WEBHOOK_URL` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your DingTalk Bot Webhook URL

   <br>

   **Bot Setup Steps:**

   1. **Create a Bot (Only supported on PC)**:
      - Open the DingTalk PC client and enter the target group chat
      - Click the group settings icon (⚙️) → scroll down to find "Bots" and open it
      - Select "Add Bot" → "Custom"

   2. **Configure the Bot**:
      - Set the bot name
      - **Security Settings**:
        - **Custom Keywords**: Set "hotspot"

   3. **Complete Setup**:
      - Check the terms of service agreement → click "Finished"
      - Copy the obtained Webhook URL
      - Configure the URL into `DINGTALK_WEBHOOK_URL` in GitHub Secrets

   **Note**: The mobile app can only receive messages and cannot create new bots.
   </details>

   <details>
   <summary>👉 Click to expand: <strong>Telegram Bot</strong></summary>
   <br>

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `TELEGRAM_BOT_TOKEN` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Telegram Bot Token

   - **Name**: `TELEGRAM_CHAT_ID` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Telegram Chat ID

   **Note**: Telegram requires configuring **two** Secrets. Please click the "New repository secret" button twice to add them separately.

   <br>

   **Bot Setup Steps:**

   1. **Create a Bot**:
      - Search for `@BotFather` in Telegram (note the capitalization, it has a blue verified checkmark and something like 37849827 monthly users. This is the official one, be careful to distinguish it from fake accounts)
      - Send the `/newbot` command to create a new bot
      - Set the bot name (must end with "bot". It's easy to encounter duplicate names, so you'll have to rack your brains for a unique one)
      - Get the Bot Token (format like: `123456789:AAHfiqksKZ8WmR2zSjiQ7_v4TMAKdiHm9T0`)

   2. **Get the Chat ID**:

      **Method 1: Get via official API**
      - First, send a message to your bot
      - Visit: `https://api.telegram.org/bot<Your Bot Token>/getUpdates`
      - Find the number in `"chat":{"id":number}` from the returned JSON

      **Method 2: Use a third-party tool**
      - Search for `@userinfobot` and send `/start`
      - Get your user ID to use as the Chat ID

   3. **Configure in GitHub**:
      - `TELEGRAM_BOT_TOKEN`: Enter the Bot Token obtained in step 1
      - `TELEGRAM_CHAT_ID`: Enter the Chat ID obtained in step 2
   </details>

   <details>
   <summary>👉 Click to expand: <strong>Email Push</strong> (Supports all mainstream email providers)</summary>
   <br>

   - Note: To prevent the mass email function from being **abused**, the current mass mailing allows all recipients to see each other's email addresses.
   - If you have no experience configuring the email sending methods below, it is not recommended to try

   > ⚠️ **Important Configuration Dependency**: Email push requires an HTML report file. Please ensure `storage.formats.html` in `config/config.yaml` is set to `true`:
   > ```yaml
   > storage:
   >   formats:
   >     sqlite: true
   >     txt: false
   >     html: true   # Must be enabled, otherwise email push will fail
   > ```
   > If set to `false`, an error will occur during email push: `Error: HTML file does not exist or is not provided: None`

   <br>

   **GitHub Secret Configuration (⚠️ Name must be strictly identical):**
   - **Name**: `EMAIL_FROM` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Sender's email address

   - **Name**: `EMAIL_PASSWORD` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Email password or authorization code

   - **Name**: `EMAIL_TO` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Recipient's email address (Multiple recipients should be separated by English commas; it can also be the same as EMAIL_FROM to send to yourself)

   - **Name**: `EMAIL_SMTP_SERVER` (Optional configuration, please copy and paste this name)
   - **Secret (Value)**: SMTP server address (Can be left blank, the system will automatically recognize it)

   - **Name**: `EMAIL_SMTP_PORT` (Optional configuration, please copy and paste this name)
   - **Secret (Value)**: SMTP port (Can be left blank, the system will automatically recognize it)

   **Description**: Email push requires configuring at least **3 required** Secrets (EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO), the latter two are optional configurations

   <br>

   **Supported Email Providers** (Automatically recognize SMTP configuration):

   | Email Provider | Domain | SMTP Server | Port | Encryption |
   |-----------|------|------------|------|---------|
   | **Gmail** | gmail.com | smtp.gmail.com | 587 | TLS |
   | **QQ Mail** | qq.com | smtp.qq.com | 465 | SSL |
   | **Outlook** | outlook.com | smtp-mail.outlook.com | 587 | TLS |
   | **Hotmail** | hotmail.com | smtp-mail.outlook.com | 587 | TLS |
   | **Live** | live.com | smtp-mail.outlook.com | 587 | TLS |
   | **163 Mail** | 163.com | smtp.163.com | 465 | SSL |
   | **126 Mail** | 126.com | smtp.126.com | 465 | SSL |
   | **Sina Mail** | sina.com | smtp.sina.com | 465 | SSL |
   | **Sohu Mail** | sohu.com | smtp.sohu.com | 465 | SSL |
   | **189 Mail** | 189.cn | smtp.189.cn | 465 | SSL |
   | **Aliyun Mail** | aliyun.com | smtp.aliyun.com | 465 | TLS |
   | **Yandex Mail** | yandex.com | smtp.yandex.com | 465 | TLS |
   | **iCloud Mail** | icloud.com | smtp.mail.me.com | 587 | SSL |

   > **Automatic Recognition**: When using the above emails, there is no need to manually configure `EMAIL_SMTP_SERVER` and `EMAIL_SMTP_PORT`, the system will automatically recognize them.
   >
   > **Feedback Instructions**:
   > - If you successfully test with **other emails**, please open an [Issues](https://github.com/sansan0/TrendRadar/issues) to let me know, and I will add it to the supported list
   > - If the above email configurations are incorrect or unusable, please also open an [Issues](https://github.com/sansan0/TrendRadar/issues) to provide feedback and help improve the project
   >
   > **Special Thanks**:
   > - Thanks to [@DYZYD](https://github.com/DYZYD) for contributing the 189 Mail (189.cn) configuration and completing the self-send and self-receive test ([#291](https://github.com/sansan0/TrendRadar/issues/291))
   > - Thanks to [@longzhenren](https://github.com/longzhenren) for contributing the Aliyun Mail (aliyun.com) configuration and completing the test ([#344](https://github.com/sansan0/TrendRadar/issues/344))
   > - Thanks to [@ACANX](https://github.com/ACANX) for contributing the Yandex Mail (yandex.com) configuration and completing the test ([#663](https://github.com/sansan0/TrendRadar/issues/663))
   > - Thanks to [@Sleepy-Tianhao](https://github.com/Sleepy-Tianhao) for contributing the iCloud Mail (icloud.com) configuration and completing the test ([#728](https://github.com/sansan0/TrendRadar/issues/728))

   **Common Email Settings:**

   #### QQ Mail:
   1. Log in to QQ Mail web version → Settings → Account
   2. Enable POP3/SMTP service
   3. Generate authorization code (16-letter code)
   4. For `EMAIL_PASSWORD`, fill in the authorization code, not the QQ password

   #### Gmail：
   1. Enable two-step verification
   2. Generate an app password
   3. For `EMAIL_PASSWORD`, fill in the app password

   #### 163/126 Mail:
   1. Log in to the web version → Settings → POP3/SMTP/IMAP
   2. Enable SMTP service
   3. Set up client authorization code
   4. For `EMAIL_PASSWORD`, fill in the authorization code
   <br>

   **Advanced Configuration**:
   If automatic recognition fails, you can manually configure SMTP:
   - `EMAIL_SMTP_SERVER`: e.g., smtp.gmail.com
   - `EMAIL_SMTP_PORT`: e.g., 587 (TLS) or 465 (SSL)
   <br>

   **If there are multiple recipients (note: separated by English commas)**:
   - EMAIL_TO="user1@example.com,user2@example.com,user3@example.com"

   </details>

   <details>
   <summary>👉 Click to expand: <strong>ntfy Push</strong> (Open source, free, supports self-hosting)</summary>
   <br>

   **Two ways to use:**

   ### Method 1: Free to use (Recommended for beginners) 🆓

   **Features**:
   - ✅ No account registration required, use immediately
   - ✅ 250 messages per day (enough for 90% of users)
   - ✅ Topic name is the "password" (need to choose a name that is hard to guess)
   - ⚠️ Messages are unencrypted, not suitable for sensitive information, but suitable for the non-sensitive information of our project

   **Quick Start:**

   1. **Download the ntfy app**:
      - Android：[Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [F-Droid](https://f-droid.org/en/packages/io.heckel.ntfy/)
      - iOS：[App Store](https://apps.apple.com/us/app/ntfy/id1625396347)
      - Desktop: Visit [ntfy.sh](https://ntfy.sh)

   2. **Subscribe to a topic** (choose a hard-to-guess name):
      ```
      Suggested format: trendradar-{your initials}-{random numbers}
   
      Cannot use Chinese
      
      ✅ Good example: trendradar-zs-8492
      ❌ Bad example: news, alerts (too easy to guess)
      ```

   3. **Configure GitHub Secret (⚠️ Name must be strictly identical)**:
      - **Name**: `NTFY_TOPIC` (please copy and paste this name, do not type it manually)
      - **Secret (Value)**: Fill in the topic name you just subscribed to

      - **Name**: `NTFY_SERVER_URL` (optional configuration, please copy and paste this name)
      - **Secret (Value)**: Leave blank (defaults to ntfy.sh)

      - **Name**: `NTFY_TOKEN` (Optional configuration, please copy and paste this name)
      - **Secret (Value)**: Leave blank

      **Note**: ntfy requires at least 1 mandatory Secret (NTFY_TOPIC), the latter two are optional configurations

   4. **Test**:
      ```bash
      curl -d "Test message" ntfy.sh/your_topic_name
      ```

   ---

   ### Method 2: Self-hosted (Complete Privacy Control) 🔒

   **Suitable for**: Users with servers, seeking complete privacy, and strong technical skills

   **Advantages**:
   - ✅ Completely open-source (Apache 2.0 + GPLv2)
   - ✅ Complete control over your own data
   - ✅ No restrictions
   - ✅ Zero cost

   **One-click Docker Deployment**:
   ```bash
   docker run -d \
     --name ntfy \
     -p 80:80 \
     -v /var/cache/ntfy:/var/cache/ntfy \
     binwiederhier/ntfy \
     serve --cache-file /var/cache/ntfy/cache.db
   ```

   **Configure TrendRadar**:
   ```yaml
   NTFY_SERVER_URL: https://ntfy.yourdomain.com
   NTFY_TOPIC: trendradar-alerts  # Simple names can be used for self-hosting
   NTFY_TOKEN: tk_your_token  # Optional: Enable access control
   ```

   **Subscribe in the app**:
   - Click "Use another server"
   - Enter your server address
   - Enter the topic name
   - (Optional) Enter login credentials

   ---

   **FAQ:**

   <details>
   <summary><strong>Q1: Is the free version enough?</strong></summary>

   250 messages per day is enough for most users. Calculated at one scrape every 30 minutes, there are about 48 pushes per day, which is completely sufficient.
   </details>

   <details>
   <summary><strong>Q2: Is the Topic name really secure?</strong></summary>

   If you choose a random, sufficiently long name (like `trendradar-zs-8492-news`), brute-force cracking is almost impossible:
   - ntfy has strict rate limits (1 request per second)
   - 64 character choices (A-Z, a-z, 0-9, _, -)
   - A 10-character random string has 64^10 possibilities (would take years to crack)
   </details>

   ---

   **Recommended choices:**

   | User Type | Recommended Solution | Reason |
   |---------|---------|------|
   | Regular User | Method 1 (Free) | Simple and fast, sufficient |
   | Technical User | Method 2 (Self-hosted) | Complete control, no restrictions |
   | High-frequency User | Method 3 (Paid) | Check the official website for this |

   **Related Links:**
   - [ntfy Official Documentation](https://docs.ntfy.sh/)
   - [Self-hosting Tutorial](https://docs.ntfy.sh/install/)
   - [GitHub Repository](https://github.com/binwiederhier/ntfy)

   </details>

   <details>
   <summary>👉 Click to expand: <strong>Bark Push</strong> (iOS exclusive, simple and efficient)</summary>
   <br>

   **GitHub Secret Configuration (⚠️ Name must be strictly identical):**
   - **Name**: `BARK_URL` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Bark push URL

   <br>

   **Introduction to Bark:**

   Bark is a free and open-source push notification tool for iOS, featuring simplicity, speed, and no ads.

   **How to use:**

   ### Method 1: Use the official server (Recommended for beginners) 🆓

   1. **Download the Bark App**:
      - iOS: [App Store](https://apps.apple.com/cn/app/bark-send push to your mobile phone/id1403753865)

   2. **Get the push URL**:
      - Open the Bark App
      - Copy the push URL displayed on the homepage (format: `https://api.day.app/your_device_key`)
      - Configure the URL into `BARK_URL` in GitHub Secrets

   ### Method 2: Self-hosted server (Complete privacy control) 🔒

   **Suitable for**: Users with servers, seeking complete privacy, and strong technical skills

   **Docker one-click deployment**:
   ```bash
   docker run -d \
     --name bark-server \
     -p 8080:8080 \
     finab/bark-server
   ```

   **Configure TrendRadar**:
   ```yaml
   BARK_URL: http://your-server-ip:8080/your_device_key
   ```

   ---

   **Notes:**
   - ✅ Bark uses APNs for push notifications, with a maximum size of 4KB per message
   - ✅ Supports automatic batch push, no need to worry about messages being too long
   - ✅ Push format is plain text (Markdown syntax is automatically removed)
   - ⚠️ Only supports the iOS platform

   **Related links:**
   - [Bark Official Website](https://bark.day.app/)
   - [Bark GitHub Repository](https://github.com/Finb/Bark)
   - [Bark Server Self-hosting Tutorial](https://github.com/Finb/bark-server)

   </details>

   <details>
   <summary>👉 Click to expand: <strong>Slack Push</strong></summary>
   <br>

   **GitHub Secret Configuration (⚠️ The Name must be strictly identical):**
   - **Name**: `SLACK_WEBHOOK_URL` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Slack Incoming Webhook URL

   <br>

   **Introduction to Slack:**

   Slack is a team collaboration tool, and Incoming Webhooks can push messages to Slack channels.

   **Setup steps:**

   ### Step 1: Create a Slack App

   1. **Visit the Slack API page**:
      - Open https://api.slack.com/apps?new_app=1
      - If not logged in, log in to your Slack workspace first

   2. **Select creation method**:
      - Click **"From scratch"**

   3. **Fill in App information**:
      - **App Name**: Enter the application name (e.g., `TrendRadar` or `Hot News Monitor`)
      - **Workspace**: Select your workspace from the dropdown list
      - Click the **"Create App"** button

   ### Step 2: Enable Incoming Webhooks

   1. **Navigate to Incoming Webhooks**:
      - Find and click **"Incoming Webhooks"** in the left menu

   2. **Enable the feature**:
      - Find the **"Activate Incoming Webhooks"** toggle
      - Switch the toggle from `OFF` to `ON`
      - The page will automatically refresh to show new configuration options

   ### Step 3: Generate Webhook URL

   1. **Add a new Webhook**:
      - Scroll to the bottom of the page
      - Click the **"Add New Webhook to Workspace"** button

   2. **Select the target channel**:
      - The system will pop up an authorization page
      - Select the channel to receive messages from the dropdown list (e.g., `#hot-news`)
      - ⚠️ If you want to select a private channel, you must join that channel first

   3. **Authorize the app**:
      - Click the **"Allow"** button to complete authorization
      - The system will automatically redirect back to the configuration page

   ### Step 4: Copy and save the Webhook URL

   1. **View the generated URL**:
      - In the "Webhook URLs for Your Workspace" section
      - You will see the newly generated Webhook URL
      - Format like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`

   2. **Copy the URL**:
      - Click the **"Copy"** button on the right side of the URL
      - Or manually select the URL and copy it

   3. **Configure in TrendRadar**:
      - **GitHub Actions**: Add the URL to `SLACK_WEBHOOK_URL` in GitHub Secrets
      - **Local testing**: Fill the URL into the `slack_webhook_url` field in `config/config.yaml`
      - **Docker deployment**: Add the URL to the `SLACK_WEBHOOK_URL` variable in the `docker/.env` file

   ---

   **Notes:**
   - ✅ Supports Markdown format (automatically converted to Slack mrkdwn)
   - ✅ Supports automatic batch pushing (4KB per batch)
   - ✅ Suitable for team collaboration and centralized message management
   - ⚠️ The Webhook URL contains a secret key, never make it public

   **Message format preview:**
   ```
   *[Batch 1/2]*

   📊 *Trending Keywords Statistics*

   🔥 *[1/3] AI ChatGPT* : 2 items

     1. [Baidu Hot Search] 🆕 ChatGPT-5 officially released *[1]* - 09:15 (1 time)

     2. [Toutiao] AI chip concept stocks surge *[3]* - [08:30 ~ 10:45] (3 times)
   ```

   **Related Links:**
   - [Slack Incoming Webhooks Official Documentation](https://api.slack.com/messaging/webhooks)
   - [Slack API App Management](https://api.slack.com/apps)

   </details>

   <details>
   <summary>👉 Click to expand: <strong>Generic Webhook Push</strong> (Supports Discord, Matrix, IFTTT, etc.)</summary>
   <br>

   **GitHub Secret Configuration (⚠️ Name must be strictly identical):**
   - **Name**: `GENERIC_WEBHOOK_URL` (Please copy and paste this name, do not type it manually)
   - **Secret (Value)**: Your Webhook URL

   - **Name**: `GENERIC_WEBHOOK_TEMPLATE` (Optional configuration, please copy and paste this name)
   - **Secret (Value)**: JSON template string, supports `{title}` and `{content}` placeholders

   <br>

   **Generic Webhook Introduction:**

   Generic Webhook supports any platform that accepts HTTP POST requests, including but not limited to:
   - **Discord**: Push to channel via Webhook
   - **Matrix**: Bridge push via Webhook
   - **IFTTT**: Trigger automated workflows
   - **Self-hosted services**: Any custom service that supports Webhooks

   **Configuration Example:**

   ### Discord Configuration

   1. **Get Webhook URL**:
      - Go to Discord Server Settings → Integrations → Webhooks
      - Create a new Webhook, copy the URL

   2. **Configure Template**:
      ```json
      {"content": "{content}"}
      ```

   3. **GitHub Secret Configuration**:
      - `GENERIC_WEBHOOK_URL`：Discord Webhook URL
      - `GENERIC_WEBHOOK_TEMPLATE`：`{"content": "{content}"}`

   ### Custom Template

   The template supports two placeholders:
   - `{title}` - Message title
   - `{content}` - Message content

   **Template Example**:
   ```json
   # Default format (used when left blank)
   {"title": "{title}", "content": "{content}"}

   # Discord format
   {"content": "{content}"}

   # Custom format
   {"text": "{content}", "username": "TrendRadar"}
   ```

   ---

   **Notes:**
   - ✅ Supports Markdown format (consistent with WeCom format)
   - ✅ Supports automatic batch pushing
   - ✅ Supports multi-account configuration (separated by `;`)
   - ⚠️ The template must be in a valid JSON format
   - ⚠️ Different platforms have different requirements for message formats, please refer to the target platform's documentation

   </details>

   <br>

### 3️⃣ Step 3: Manually test news push

   > ⚠️ Reminder:
   > - After completing steps 1-2, please test immediately! Once the test is successful, adjust the configuration as needed (Step 4)
   > - Please go to your own project, not this project!

   **How to find your Actions page**:

   - **Method 1**: Open the homepage of your forked project and click the **Actions** tab at the top
   - **Method 2**: Directly visit `https://github.com/your-username/TrendRadar/actions`

   **Example comparison**:
   - ❌ Author's project: `https://github.com/sansan0/TrendRadar/actions`
   - ✅ Your project: `https://github.com/your-username/TrendRadar/actions`

   **Test steps**:
   1. Go to the Actions page of your project
   2. Find **"Get Hot News"** (it must be exactly these words), click on it, and click the **"Run workflow"** button on the right to run it
      - If you cannot see these words, refer to [#109](https://github.com/sansan0/TrendRadar/issues/109) to resolve it
   3. In about 3 minutes, the message will be pushed to your configured platform

   <br>

   > ⚠️ Reminder:
   > - Do not test manually too frequently to avoid triggering GitHub Actions limits
   > - After clicking Run workflow, you need to refresh the browser page to see the new run record

   <br>

### 4️⃣ Step 4: Configuration Instructions (Optional)

   The default configuration is ready to use. If you need personalized adjustments, just understand the following files:

   | File | Purpose |
   |------|------|
   | `config/config.yaml` | Main configuration file: push mode, time window, platform list, hot topic weights, etc. |
   | `config/frequency_words.txt` | Keyword file: set the words you care about to filter pushed content |
   | `config/ai_analysis_prompt.txt` | AI prompt template: customize the role and analysis dimensions of the AI analyst |
   | `.github/workflows/crawler.yml` | Execution frequency: controls how often it runs (⚠️ modify with caution) |

   👉 **Detailed configuration tutorial**: [Configuration Details](#configuration-details)

   <br>

### 5️⃣ Step 5: Remote Cloud Storage & Check-in Configuration

   **v4.0.0 Important Change**: Introduced an "activity detection" mechanism; GitHub Actions requires regular check-ins to keep running.

   - **Run cycle**: The validity period is **7 days**, and the service will be automatically suspended after the countdown ends.
   - **Renewal method**: Manually trigger the "Check In" workflow on the Actions page to reset the 7-day validity period.
   - **Operation path**: `Actions` → `Check In` → `Run workflow`
   - **Design philosophy**:
     - If you forget to check in for 7 days, perhaps this information is not a rigid demand for you. A timely pause can help you detach from the information flow and give your brain some breathing room.
     - GitHub Actions is a valuable public computing resource. The introduction of the check-in mechanism aims to avoid invalid idling of computing power and ensure that resources can be allocated to truly active users who need them. Thank you for your understanding and support.

   ---

   **About remote cloud storage configuration (please choose according to your deployment method):**

   - **GitHub Actions users**:
     - **Current status**: Every time Actions runs, it is a brand new environment and does not save files. If cloud storage is not configured, the project will run in **lightweight mode** (no incremental push, no historical tracking).
     - **Recommendation**: Configure remote cloud storage to get the full experience.

   - **Docker / Local users**:
     - **Current status**: Data is saved on the local hard drive by default.
     - **Recommendation**: Cloud storage is optional and can be used as an off-site backup.

   <details>
   <summary>👉 Click to expand: <strong>Remote Cloud Storage Configuration Tutorial (Using Cloudflare R2 as an example)</strong></summary>
   <br>

   **⚠️ Prerequisites (Important):**

   According to Cloudflare platform rules, enabling R2 requires binding a payment method.

   * **Purpose**: For identity verification only (Verify Only), **no charges will be incurred**.
   * **Payment**: Supports dual-currency credit cards or China region PayPal.
   * **Usage**: R2's free tier (10GB storage/month) is sufficient to cover the daily operation of this project, so there is no need to worry about paying.

   ---

   **GitHub Secret Configuration (4 items need to be added):**

   | Name | Secret (Value) Description |
   |-------------|-----------------|
   | `S3_BUCKET_NAME` | Bucket name (e.g., `trendradar-data`) |
   | `S3_ACCESS_KEY_ID` | Access Key ID |
   | `S3_SECRET_ACCESS_KEY` | Secret Access Key |
   | `S3_ENDPOINT_URL` | S3 API endpoint (e.g., for R2: `https://<account-id>.r2.cloudflarestorage.com`) |

   **Optional Configuration:**

   | Name | Secret (Value) Description |
   |-------------|-----------------|
   | `S3_REGION` | Region (default is `auto`, some providers may require specifying it) |

   > 💡 **More storage configuration options**: See [Where is the data saved?](#11-Where is the data saved)

   <br>

   **Detailed Steps (Getting Credentials):**

   1. **Enter R2 Overview**:
      - Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/).
      - Find and click `R2 Object Storage` in the left sidebar.

   2. **Create a Bucket**:
      - Click `Overview`
      - Click `Create bucket` in the top right corner.
      - Enter a name (e.g., `trendradar-data`), and click `Create bucket`.

   3. **Create an API Token**:
      - Return to the **Overview** page.
      - Click `Account Details` in the **bottom right corner**, find and click `Manage` (Manage R2 API Tokens).
      - At the same time, you will see the `S3 API`: `https://<account-id>.r2.cloudflarestorage.com` (This is the S3_ENDPOINT_URL)
      - Click `Create Account API Token`.
      - **⚠️ Key Settings**:
        - **Token Name**: Fill in anything (e.g., `github-action-write`).
        - **Permissions**: Select `Admin Read and Write`.
        - **Specify Bucket**: For security, it is recommended to select `Apply to specific buckets only` and choose your bucket (e.g., `trendradar-data`).
      - Click `Create API Token`, and **immediately copy** the displayed `Access Key ID` and `Secret Access Key` (they are only shown once!).

   </details>

   <br>

### 6️⃣ Step 6: Enable AI Analysis Push

   This is the core feature of v5.0.0, letting AI help you summarize and analyze news. It is highly recommended to try it.

   **Configuration Method:**
   Add the following to GitHub Secrets (or `.env` / `config.yaml`):
   - `AI_API_KEY`: Your API Key (supports DeepSeek, OpenAI, etc.)
   - `AI_PROVIDER`: Provider name (e.g., `deepseek`, `openai`)

   That's it, no complex deployment required. You will see the intelligent analysis report in the next push.

   <br>

### 7️⃣ Step 7: 🎉 Deployment Successful!

   Congratulations! Now you can start enjoying the efficient information flow brought by TrendRadar.

   💬 **Join the Community**: Welcome to follow the WeChat official account "**[Silicon-based Breakroom](#-supported project)**" to share your experience and advanced usage.

   <br>

### 8️⃣ Step 8: Advanced: Choose Your AI Assistant

   TrendRadar provides two ways to use AI to meet different needs:

   | Feature | ✨ AI Analysis Push | 🧠 AI Intelligent Analysis |
   | :--- | :--- | :--- |
   | **Mode** | **Passive Reception** (Daily Report) | **Active Dialogue** (In-depth Research) |
   | **Scenario** | "What are the big events today?" | "Analyze the changes in the AI industry over the past week" |
   | **Deployment** | Minimalist (Just fill in the Key) | Advanced (Requires local run/Docker) |
   | **Client** | Mobile | Computer |
  

   👉 **Conclusion**: Use **AI Analysis Push** first to meet daily needs; if you are a data analyst or need in-depth mining, then try **[AI Intelligent Analysis](#-ai- Intelligent Analysis)**.

<br>

<a name="Configuration details"></a>

## ⚙️ Configuration Details

> **📖 Reminder**: This section provides detailed configuration instructions. It is recommended to complete the basic configuration in [Quick Start](#-Quick Start) first, and then come back to check the detailed options as needed.

### 1. Which platforms do I want to watch?

<details id="Customized monitoring platform">
<summary>👉 Click to expand: <strong>Select Information Sources</strong></summary>
<br>

**Configuration Location:** The `platforms` section of `config/config.yaml`

The information data of this project comes from [newsnow](https://github.com/ourongxing/newsnow). You can click on the [website](https://newsnow.busiyi.world/), click [More], and check if there are platforms you want.

For specific additions, you can visit the [project source code](https://github.com/ourongxing/newsnow/tree/main/server/sources), and modify the `platforms` configuration in the `config/config.yaml` file according to the file names inside:

```yaml
platforms:
  enabled: true                       # Whether to enable hotlist platform scraping
  sources:
    - id: "toutiao"
      name: "Today's headlines"
    - id: "baidu"
      name: "Baidu Hot Search"
    - id: "wallstreetcn-hot"
      name: "Wall Street Insights"
    # Add more platforms...
```

> 💡 **Shortcut**: If you don't know how to read the source code, you can copy the [Platform Configuration Summary](https://github.com/sansan0/TrendRadar/issues/95) compiled by others.

> ⚠️ **Note**: More platforms is not always better. It is recommended to choose 10-15 core platforms. Too many platforms will lead to information overload and reduce the user experience.

</details>

### 2. What content do I care about?

Tell the bot what you want to see in the `frequency_words.txt` file, and it will keep an eye on it for you. It supports various usages such as normal words, required words, and filter words.

| Syntax Type | Symbol | Function | Example | Matching Logic |
|---------|------|------|------|---------|
| **Normal Word** | None | Basic matching | `Huawei` | Contains any one of them |
| **Required Word** | `+` | Limit scope | `+` | Must contain simultaneously |
| **Filter Word** | `!` | Exclude interference | `!Advertisement` | Exclude directly if contained |
| **Quantity Limit** | `@` | Control display quantity | `@10` | Display up to 10 news items (Added in v3.2.0) |
| **Global Filter** | `[GLOBAL_FILTER]` | Globally exclude specified content | See example below | Filter under any circumstances (Added in v3.5.0) |
| **Regular Expression** | `/pattern/` | Exact match pattern | `/\bai\b/` | Match using regular expressions (Added in v4.7.0) |
| **Display Name** | `=> Remark` | Custom display text | `/\bai\b/ => AI related` | Push and HTML display remark name (Added in v4.7.0) |

#### 2.1 Basic Syntax

<a name="Keyword basic syntax"></a>

<details>
<summary>👉 Click to expand: <strong>Basic Syntax Tutorial</strong></summary>
<br>

**Configuration location:** `config/frequency_words.txt`

##### 1. **Normal Keywords** - Basic matching
```txt
Huawei
OPPO
Apple
```
**Function:** News titles containing **any of these words** will be captured

##### 2. **Required Words** `+word` - Limit scope
```txt
Huawei
OPPO
+phone
```
**Function:** Must contain both normal words **and** required words to be captured

##### 3. **Filter Words** `!word` - Exclude interference
```txt
Apple
Huawei
!fruit
!price
```
**Function:** News containing filter words will be **directly excluded**, even if they contain keywords

##### 4. **Quantity Limit** `@number` - Control display quantity (Added in v3.2.0)
```txt
Tesla
Musk
@5
```
**Function:** Limit the maximum number of news items displayed for this keyword group

**Configuration priority:** `@number` > Global configuration > No limit

##### 5. **Global Filter** `[GLOBAL_FILTER]` - Globally exclude specified content (Added in v3.5.0)
```txt
[GLOBAL_FILTER]
Advertisement
Promotion
Marketing
Shocking
Clickbait

[WORD_GROUPS]
Technology
AI

Huawei
HarmonyOS
!car
```
**Function:** Filter news containing specified words under any circumstances, **highest priority**

**Use cases:**
- Filter low-quality content: shocking, clickbait, leaks, etc.
- Filter marketing content: advertisements, promotions, sponsorships, etc.
- Filter specific topics: entertainment, gossip (according to needs)

**Filter priority:** Global filter > Intra-group filter (`!`) > Group matching

**Section description:**
- `[GLOBAL_FILTER]`: Global filter section, included words will be filtered under any circumstances
- `[WORD_GROUPS]`: Word group section, keeps existing syntax (`!`, `+`, `@`)
- If no region markers are used, all are treated as phrases by default (backward compatible)

**Match examples:**
```txt
[GLOBAL_FILTER]
Ads

[WORD_GROUPS]
Technology
AI
```
- ❌ "Ads: Latest tech product release" ← Contains the global filter word "Ads", rejected directly
- ✅ "Tech company releases new AI product" ← Does not contain global filter words, matches the "Technology" phrase
- ✅ "AI technology breakthrough attracts attention" ← Does not contain global filter words, matches "AI" in the "Technology" phrase

**Notes:**
- Global filter words should be used with caution to avoid over-filtering and missing valuable content
- It is recommended to keep the number of global filter words within 5-15
- For filtering specific phrases, prioritize using intra-phrase filter words (with the `!` prefix)

##### 6. **Regular Expressions** `/pattern/` - Exact match mode (New in v4.7.0)

Normal keywords use substring matching, which is convenient in a Chinese environment but may cause false matches in an English environment. For example, `ai` will match the `ai` in `training`.

Using the regular expression syntax `/pattern/` enables exact matching:

```txt
/(?<![a-z])ai(?![a-z])/
Artificial Intelligence
```

**Function:** Uses regular expressions for matching, supporting all Python regex syntax

**Common regex patterns:**

| Requirement | Regex Syntax | Description |
|------|---------|------|
| English word boundary | `/\bword\b/` | Matches independent words, e.g., `/\bai\b/` matches "AI" but not "training" |
| Non-letter before and after | `/(?<![a-z])ai(?![a-z])/` | Looser boundaries, suitable for mixed Chinese and English scenarios |
| Match at beginning | `/^breaking/` | Only matches titles starting with "breaking" |
| Match at end | `/release$/` | Only matches titles ending with "release" |
| Match any of multiple | `/Apple\|Huawei\|Xiaomi/` | Matches any one of them (note the escaped `\|`) |

**Match examples:**
```txt
# Configuration
/(?<![a-z])ai(?![a-z])/
Artificial Intelligence
```

- ✅ "AI is the future" ← Matches the independent "AI"
- ✅ "aihehe" ← Surrounded by Chinese, matches "ai"
- ✅ "Artificial Intelligence develops rapidly" ← Matches "Artificial Intelligence"
- ❌ "Resistance training is important" ← The "ai" in "training" does not match
- ❌ "The maid cleaned the room" ← The "ai" in "maid" does not match

**Combined usage:**
```txt
# Regex + Normal word + Filter word
/\bai\b/
Artificial Intelligence
Machine Learning
!Ads
```

**Notes:**
- Regular expressions automatically enable case-insensitive matching (`re.IGNORECASE`)
- Supports JavaScript-style syntax like `/pattern/i` (flags will be ignored since case-insensitivity is enabled by default)
- Invalid regex syntax will be treated as normal words
- Regex can be used for normal words, required words (`+`), and filter words (`!`)

**💡 Don't know how to write regex? Let AI generate it for you!**

If you are not familiar with regular expressions, you can directly ask ChatGPT / Gemini / DeepSeek to generate them for you. Just tell the AI:

> I need a Python regular expression to match the English word "ai", but not the "ai" in "training".
> Please provide the regular expression directly in the format `/pattern/`, without any extra explanation.

The AI will give you a result like this: `/(?<![a-zA-Z])ai(?![a-zA-Z])/`

##### 7. **Display Name** `=> Remark` - Custom display text (New in v4.7.0)

Regular expressions might not be very user-friendly when displayed in push messages and HTML pages. Use the `=> Remark` syntax to set a display name:

```txt
/(?<![a-zA-Z])ai(?![a-zA-Z])/ => AI Related
Artificial Intelligence
```

**Effect:** Push messages and HTML pages will display "AI Related" instead of the complex regular expression

**Syntax Format:**
```txt
# Regex + Display Name
/pattern/ => Display Name
/pattern/i => Display Name    # Supports flags syntax (flags are ignored)
/pattern/=>Display Name       # Spaces around => are optional

# Normal word + Display Name
deepseek => DeepSeek Updates
```

**Matching Example:**
```txt
# Configuration
/(?<![a-zA-Z])ai(?![a-zA-Z])/ => AI Related
Artificial Intelligence
```

| Original Configuration | Push/HTML Display |
|---------|---------------|
| `/(?<![a-z])ai(?![a-z])/` + `Artificial Intelligence` | `(?<![a-z])ai(?![a-z]) Artificial Intelligence` |
| `/(?<![a-z])ai(?![a-z])/ => AI Related` + `Artificial Intelligence` | **`AI Related`** |

**Notes:**
- The display name only needs to be written on the first word of the phrase group
- If multiple words in a phrase group have display names, the first one is used
- When no display name is set, all words in the phrase group are automatically concatenated

---

#### 🔗 Phrase Group Feature - The Important Role of Blank Line Separation

**Core Rule:** Use **blank lines** to separate different phrase groups, each group is counted independently

##### Example Configuration:
```txt
iPhone
Huawei
OPPO
+Release

A-shares
SSE
SZSE
+Fluctuation
!Prediction

World Cup
European Cup
Asian Cup
+Match
```

##### Phrase explanation and matching results:

**Group 1 - New Mobile Phones:**
- Keywords: iPhone, Huawei, OPPO
- Required words: Launch
- Effect: Must contain the mobile phone brand name, and also contain "Launch"

**Matching examples:**
- ✅ "iPhone 15 officially launched, price announced" ← Contains "iPhone" + "Launch"
- ✅ "Huawei Mate60 series launch event live stream" ← Contains "Huawei" + "Launch"
- ✅ "OPPO Find X7 launch time confirmed" ← Contains "OPPO" + "Launch"
- ❌ "iPhone sales hit a new high" ← Contains "iPhone" but missing "Launch"

**Group 2 - Stock Market Trends:**
- Keywords: A-shares, SSE, SZSE
- Required words: Rise/Fall
- Filter words: Predict
- Effect: Focus on actual stock market rise/fall, exclude prediction-related content

**Matching examples:**
- ✅ "Analysis of significant rise/fall in A-shares today" ← Contains "A-shares" + "Rise/Fall"
- ✅ "SSE index rise/fall margin hits a new high" ← Contains "SSE" + "Rise/Fall"
- ❌ "Experts predict A-shares rise/fall trend" ← Contains "A-shares" + "Rise/Fall" but includes "Predict"

**Group 3 - Football Matches:**
- Keywords: World Cup, European Cup, Asian Cup
- Required words: Match
- Effect: Only focus on match-related news

---

#### 📝 Configuration Tips

##### 1. **From Broad to Strict**
```txt
# Step 1: Test with broad keywords first
Artificial Intelligence
AI
ChatGPT

# Step 2: After finding false matches, add required words to limit
Artificial Intelligence
AI
ChatGPT
+Technology

# Step 3: After finding interfering content, add filter words
Artificial Intelligence
AI
ChatGPT
+Technology
!Ads
!Training
```

##### 2. **Avoid Overcomplication**

❌ **Not recommended:** A phrase containing too many words
```txt
Huawei
OPPO
Apple
Samsung
vivo
OnePlus
Meizu
+Smartphone
+Release
+Sales
!Fake
!Repair
!Second-hand
```

✅ **Recommended:** Split into multiple precise phrases
```txt
Huawei
OPPO
+New product

Apple
Samsung
+Release

Smartphone
Sales
+Market
```

</details>

#### 2.2 Advanced Configuration (New in v3.2.0)

<a name="keyword-advanced-configuration"></a>

<details>
<summary>👉 Click to expand: <strong>Advanced Configuration Tutorial</strong></summary>
<br>

##### Keyword Sorting Priority

**Configuration Location:** `config/config.yaml`

```yaml
report:
  sort_by_position_first: false  # Sorting priority configuration
```

| Configuration Value | Sorting Rule | Applicable Scenario |
|--------|---------|---------|
| `false` (Default) | Hot news count ↓ → Configuration order ↑ | Focus on popularity trends |
| `true` | Configuration order ↑ → Hot news count ↓ | Focus on personal priority |

**Example:** Configuration order A, B, C, hot news count A (3 items), B (10 items), C (5 items)
- `false`: B (10 items) → C (5 items) → A (3 items)
- `true`: A (3 items) → B (10 items) → C (5 items)

##### Global Display Quantity Limit

```yaml
report:
  max_news_per_keyword: 10  # Display up to 10 items per keyword (0 = unlimited)
```

**Docker Environment Variables:**
```bash
SORT_BY_POSITION_FIRST=true
MAX_NEWS_PER_KEYWORD=10
```

**Comprehensive Example:**
```yaml
# config.yaml
report:
  sort_by_position_first: true   # Prioritize by configuration order
  max_news_per_keyword: 10       # Global default max 10 items per keyword
```

```txt
# frequency_words.txt
Tesla
Musk
@20              # Focus, show 20 items (overrides global config)

Huawei            # Uses global config, shows 10 items

BYD
@5               # Limit to 5 items
```

**Final effect:** Displayed in configured order: Tesla (20 items) → Huawei (10 items) → BYD (5 items)

</details>

### 3. Which push mode to choose?

<details>
<summary>👉 Click to expand: <strong>Detailed comparison of the three push modes</strong></summary>
<br>

**Configuration location:** `report.mode` in `config/config.yaml`

```yaml
report:
  mode: "daily"  # Optional: "daily" | "incremental" | "current"
```

#### Detailed comparison table

| Mode | Target Audience | Push Timing | Display Content | Typical Use Cases |
|------|----------|----------|----------|------------|
| **Daily Summary**<br/>`daily` | 📋 Enterprise Managers / Regular Users | Pushed on schedule (default once per hour) | All matching news of the day<br/>+ New news section | **Case**: Check all important news today at 6 PM every day<br/>**Features**: View the complete trend of the whole day without missing any hot topics<br/>**Reminder**: Will include previously pushed news |
| **Current Rankings**<br/>`current` | 📰 Independent Media / Content Creators | Pushed on schedule (default once per hour) | Matching news from current rankings<br/>+ New news section | **Case**: Track "what topics are hottest right now" every hour<br/>**Features**: Real-time understanding of current popularity ranking changes<br/>**Reminder**: News that remains on the list will appear every time |
| **Incremental Monitoring**<br/>`incremental` | 📈 Investors / Traders | Pushed only when there are new additions | Newly appeared matching keyword news | **Case**: Monitor "Tesla", notify only when there is new information<br/>**Features**: Zero repetition, only view news appearing for the first time<br/>**Suitable for**: High-frequency monitoring, avoiding information overload |

#### Example of actual push effects

Assuming you monitor the keyword "Apple" and execute it once an hour:

| Time | daily mode push | current mode push | incremental mode push |
|-----|--------------|----------------|-------------------|
| 10:00 | News A, News B | News A, News B | News A, News B |
| 11:00 | News A, News B, News C | News B, News C, News D | **Only** News C |
| 12:00 | News A, News B, News C | News C, News D, News E | **Only** News D, News E |

**Explanation**:
- `daily`: Cumulatively displays all news of the day (A, B, and C are all kept)
- `current`: Displays news from the current rankings (rankings change, News D enters the list, News A drops off)
- `incremental`: **Only pushes newly appeared news** (avoids repetitive interference)

#### Frequently Asked Questions

> **💡 Encountering this issue?** 👉 "Executes once an hour, the news output after the first execution still appears during the next hour's execution"
> - **Cause**: You might have selected the `daily` (Daily Summary) or `current` (Current Rankings) mode
> - **Solution**: Switch to the `incremental` (Incremental Monitoring) mode, which only pushes new content

#### ⚠️ Important note for incremental mode

> **Users who selected the `incremental` (Incremental Monitoring) mode, please note:**
>
> 📌 **Incremental mode will only push when there are new matching news items**
>
> **If you haven't received a push for a long time, it might be because:**
> 1. No new hot topics matching your keywords appeared during the current period
> 2. Keyword configuration is too strict or too broad
> 3. The number of monitored platforms is too small
>
> **Solutions:**
> - Solution 1: 👉 [Optimize keyword configuration](#2-Keyword configuration) - Adjust the precision of keywords, add or modify monitored vocabulary
> - Solution 2: Switch push mode - Change to `current` or `daily` mode to receive scheduled pushes
> - Solution 3: 👉 [Add monitoring platforms](#1-Platform configuration) - Add more news platforms to expand information sources

</details>

### 4. Adjusting the hot topic algorithm

<details>
<summary>👉 Click to expand: <strong>Custom Trend Weights</strong></summary>
<br>

**Configuration location:** The `advanced.weight` section of `config/config.yaml`

```yaml
advanced:
  weight:
    rank: 0.6           # Rank weight
    frequency: 0.3      # Frequency weight
    hotness: 0.1        # Hotness weight
```

The current default configuration is a balanced configuration

#### Two Core Scenarios

**Chasing Real-time Trends**:
```yaml
advanced:
  weight:
    rank: 0.8           # Focuses mainly on rank
    frequency: 0.1      # Cares less about persistence
    hotness: 0.1
```
**Target Audience**: Content creators, marketers, users who want to quickly understand the hottest current topics

**Chasing In-depth Topics**:
```yaml
advanced:
  weight:
    rank: 0.4           # Moderately considers rank
    frequency: 0.5      # Emphasizes sustained hotness throughout the day
    hotness: 0.1
```
**Target Audience**: Investors, researchers, journalists, users who need in-depth trend analysis

#### How to Adjust
1. **The three numbers must add up to 1.0**
2. **Increase the value of what is more important**: If you care about rank, increase `rank`; if you care about persistence, increase `frequency`
3. **It is recommended to adjust only by 0.1-0.2 each time** and observe the effect

Core idea: Users pursuing speed and timeliness should increase the rank weight, while users pursuing depth and stability should increase the frequency weight.

</details>

### 5. What do the messages I receive look like?

<details>
<summary>👉 Click to expand: <strong>Message Style Preview</strong></summary>
<br>

#### Push Example

📊 Trending Vocabulary Statistics

🔥 [1/3] AI ChatGPT : 2 items

  1. [Baidu Hot Search] 🆕 ChatGPT-5 officially released [**1**] - 09:15 (1 time)

  2. [Toutiao] AI chip concept stocks surge [**3**] - [08:30 ~ 10:45] (3 times)

━━━━━━━━━━━━━━━━━━━

📈 [2/3] BYD Tesla : 2 items

  1. [Weibo] 🆕 BYD monthly sales break record [**2**] - 10:20 (1 time)

  2. [Douyin] Tesla price cut promotion [**4**] - [07:45 ~ 09:15] (2 times)

━━━━━━━━━━━━━━━━━━━

📌 [3/3] A-shares Stock Market : 1 item

  1. [Wallstreetcn] A-shares midday review and analysis [**5**] - [11:30 ~ 12:00] (2 times)

🆕 Newly added trending news this time (Total 2 items)

**Baidu Hot Search** (1 item):
  1. ChatGPT-5 officially released [**1**]

**Weibo** (1 item):
  1. BYD monthly sales break record [**2**]

Update time: 2025-01-15 12:30:15

#### Message Format Description

| Format Element | Example                     | Meaning      | Description                             |
| ------------- | --------------------------- | ------------ | --------------------------------------- |
| 🔥📈📌        | 🔥 [1/3] AI ChatGPT        | Popularity Level | 🔥High Popularity(≥10 items) 📈Medium Popularity(5-9 items) 📌Normal Popularity(<5 items) |
| [Index/Total] | [1/3]                       | Sort Position | Ranking of the current phrase among all matched phrases |
| Frequency Phrase | AI ChatGPT               | Keyword Phrase | Phrases in the config file, titles must contain these words |
| : N items     | : 2 items                   | Match Count  | Total number of news matched by this phrase |
| [Platform Name] | [Baidu Hot Search]        | Source Platform | Name of the platform the news belongs to |
| 🆕            | 🆕 ChatGPT-5 officially released | New Tag      | Hot topics appearing for the first time in this scraping round |
| [**Number**]  | [**1**]                     | High Ranking | Hot searches with ranking ≤ threshold, displayed in bold red |
| [Number]      | [7]                         | Normal Ranking | Hot searches with ranking > threshold, displayed normally |
| - Time        | - 09:15                     | First Time   | Time when the news was first discovered |
| [Time~Time]   | [08:30 ~ 10:45]             | Duration     | Time range from first appearance to last appearance |
| (N times)     | (3 times)                   | Appearance Frequency | Total number of appearances during the monitoring period |
| **New Area**  | 🆕 **Newly added hot news this time** | New Topic Summary | Separately display newly appeared hot topics in this round |

</details>


### 6. Docker Deployment

**Image Description:**

TrendRadar provides two independent Docker images, which can be deployed according to your needs:

| Image Name | Purpose | Description |
|---------|------|------|
| `wantcat/trendradar` | News Push Service | Scheduled news scraping, push notifications (Required) |
| `wantcat/trendradar-mcp` | AI Analysis Service | MCP protocol support, AI dialogue analysis (Optional) |

> 💡 **Suggestion**:
> - Only need push function: Deploy only the `wantcat/trendradar` image
> - Need AI analysis function: Deploy both images simultaneously

<details>
<summary>👉 Click to expand: <strong>Complete Docker Deployment Guide</strong></summary>
<br>

#### Method 1: Using docker compose (Recommended)

1. **Create project directory and configuration**:

   ```bash
   # Clone the project locally
   git clone https://github.com/sansan0/TrendRadar.git
   cd TrendRadar
   ```

   > 💡 **Note**: The key directory structure required for Docker deployment is as follows:
```
Current Directory/
├── config/
│   ├── config.yaml                 # Core function configuration (Required)
│   ├── frequency_words.txt         # Keyword configuration (Required)
│   ├── timeline.yaml               # Timeline configuration
│   ├── ai_analysis_prompt.txt      # AI analysis prompt (Optional)
│   ├── ai_translation_prompt.txt   # AI translation prompt (Optional)
│   ├── ai_interests.txt            # AI interest filtering configuration (Optional)
│   ├── ai_filter/                  # AI filtering related prompts
│   │   ├── prompt.txt
│   │   ├── extract_prompt.txt
│   │   └── update_tags_prompt.txt
│   └── custom/                     # User custom configuration (Optional)
│       ├── ai/                     # Custom AI prompts
│       └── keyword/                # Custom keyword files
└── docker/
    ├── .env                        # Sensitive information + Docker specific configuration
    └── docker-compose.yml          # Docker Compose orchestration file
```

2. **Configuration file description**:

   **Configuration Division Principles (v4.6.0 Optimized)**:

   | File | Purpose | Modification Frequency | Description |
   |------|------|---------|------|
   | `config/config.yaml` | **Core Function Configuration** | Low | Global behavior control such as report mode, push settings, storage format, push window, AI analysis switch, platform enablement, etc. |
   | `config/frequency_words.txt` | **Keyword Configuration** | High | Set the hot words you care about, supporting advanced syntax like grouping, regex, aliases, etc. |
   | `config/timeline.yaml` | **Timeline Configuration** | Low | Control the display and filtering rules of the news timeline |
   | `config/ai_analysis_prompt.txt` | **AI Analysis Prompt** | Medium | Customize the role definition and output format of AI analysis (v5.0.0+) |
   | `config/ai_translation_prompt.txt` | **AI Translation Prompt** | Low | Customize the prompt template for AI translation |
   | `config/ai_interests.txt` | **AI Interest Filtering** | Medium | Define rules for AI to automatically filter news based on interests |
   | `config/ai_filter/` | **AI Filter Prompts** | Low | Internal prompts for the AI filtering module (generally no need to modify) |
   | `config/custom/` | **User Custom Extensions** | As needed | `custom/ai/` for custom AI prompts, `custom/keyword/` for custom keyword files |
   | `docker/.env` | **Sensitive Information + Docker Specific Configuration** | Low | webhook URLs, API Key, S3 keys, cron jobs, etc., **will not be tracked by git** |

   > 💡 **Division Key Points**:
   > - **Functional Behavior** → Modify `config.yaml` (e.g., enable/disable a platform, adjust push mode)
   > - **Followed Content** → Modify `frequency_words.txt` (e.g., add new followed keywords)
   > - **AI Output Style** → Modify `ai_analysis_prompt.txt` or `ai_translation_prompt.txt`
   > - **Keys and Credentials** → Modify `docker/.env` (API Key, Webhook URL, and other sensitive information are uniformly placed here)
   > - **Personalized Extensions** → Use the `config/custom/` directory to avoid direct modifications to default configurations being overwritten by upgrades

   > 💡 **Configuration Modification Takes Effect**: After modifying `config.yaml`, execute `docker compose up -d` to restart the container to take effect

   **⚙️ Environment Variable Override Mechanism (v3.0.5+)**

   Environment variables in the `.env` file will override the corresponding configurations in `config.yaml`:

   | Environment Variable | Corresponding Configuration | Example Value | Description |
   |---------|---------|-------|------|
   | `WEBSERVER_PORT` | - | `8080` | Web server port |
   | `FEISHU_WEBHOOK_URL` | `notification.channels.feishu.webhook_url` | `https://...` | Feishu Webhook (use `;` to separate multiple accounts) |
   | `AI_ANALYSIS_ENABLED` | `ai_analysis.enabled` | `true` / `false` | Whether to enable AI analysis (added in v5.0.0) |
   | `AI_API_KEY` | `ai.api_key` | `sk-xxx...` | AI API Key (shared by ai_analysis and ai_translation) |
   | `AI_PROVIDER` | `ai.provider` | `deepseek` / `openai` / `gemini` | AI Provider |
   | `S3_*` | `storage.remote.*` | - | Remote storage configuration (5 parameters) |

   **Configuration Priority**: Environment Variables > config.yaml

   **Usage**:
   - Modify the `.env` file and fill in the required configurations
   - Or add directly in the "Environment Variables" of the NAS/Synology Docker management interface
   - Takes effect after restarting the container: `docker compose up -d`


3. **Start Services**:

   **Option A: Start all services (Push + AI Analysis)**
   ```bash
   # Pull the latest image
   docker compose pull

   # Start all services (trendradar + trendradar-mcp)
   docker compose up -d
   ```

   **Option B: Start only the news push service**
   ```bash
   # Start only trendradar (scheduled scraping and pushing)
   docker compose pull trendradar
   docker compose up -d trendradar
   ```

   **Option C: Start only the MCP AI analysis service**
   ```bash
   # Start only trendradar-mcp (provides AI analysis interface)
   docker compose pull trendradar-mcp
   docker compose up -d trendradar-mcp
   ```

   > 💡 **Tip**:
   > - Most users only need to start `trendradar` to enable the news push functionality
   > - You only need to start `trendradar-mcp` if you want to use ChatGPT/Gemini for AI conversation analysis
   > - The two services are independent and can be flexibly combined according to your needs

4. **Check running status**:
   ```bash
   # View news push service logs
   docker logs -f trendradar

   # View MCP AI analysis service logs
   docker logs -f trendradar-mcp

   # View all container statuses
   docker ps | grep trendradar

   # Stop specific services
   docker compose stop trendradar      # Stop push service
   docker compose stop trendradar-mcp  # Stop MCP service
   ```

#### Method 2: Local Build (Developer Option)

If you need to customize the code or build your own image:

```bash
# Clone the project
git clone https://github.com/sansan0/TrendRadar.git
cd TrendRadar

# Modify configuration files
vim config/config.yaml
vim config/frequency_words.txt

# Use the build version of docker compose
cd docker
cp docker-compose-build.yml docker-compose.yml
```

**Build and start services**:

```bash
# Option A: Build and start all services
docker compose build
docker compose up -d

# Option B: Build and start only the news push service
docker compose build trendradar
docker compose up -d trendradar

# Option C: Build and start only the MCP AI analysis service
docker compose build trendradar-mcp
docker compose up -d trendradar-mcp
```

> 💡 **Architecture parameter description**:
> - Builds `amd64` architecture images by default (suitable for most x86_64 servers)
> - If you need to build for `arm64` architecture (Apple Silicon, Raspberry Pi, etc.), set the environment variable:
>   ```bash
>   export DOCKER_ARCH=arm64
>   docker compose build
>   ```

#### Image Update

```bash
# Method 1: Manual update (Crawler + MCP images)
docker pull wantcat/trendradar:latest
docker pull wantcat/trendradar-mcp:latest
docker compose down
docker compose up -d

# Method 2: Update using docker compose
docker compose pull
docker compose up -d
```

**Available images**:

| Image Name | Purpose | Description |
|---------|------|------|
| `wantcat/trendradar` | News push service | Scheduled news crawling, push notifications |
| `wantcat/trendradar-mcp` | MCP service | AI analysis features (optional) |

#### Service Management Commands

```bash
# View running status
docker exec -it trendradar python manage.py status

# Manually run the crawler once
docker exec -it trendradar python manage.py run

# View real-time logs
docker exec -it trendradar python manage.py logs

# Show current configuration
docker exec -it trendradar python manage.py config

# Show output files
docker exec -it trendradar python manage.py files

# Web server management (for browser access to generated reports)
docker exec -it trendradar python manage.py start_webserver   # Start Web server
docker exec -it trendradar python manage.py stop_webserver    # Stop Web server
docker exec -it trendradar python manage.py webserver_status  # View Web server status

# View help information
docker exec -it trendradar python manage.py help

# Restart the container
docker restart trendradar

# Stop the container
docker stop trendradar

# Delete the container (keep data)
docker rm trendradar
```

> 💡 **Web Server Instructions**:
> - Starts automatically in cron mode, access `http://localhost:8080` via browser to view the latest report
> - Access historical reports via directory navigation (e.g., `http://localhost:8080/2025-xx-xx/`)
> - The port can be configured via the `WEBSERVER_PORT` parameter in the `.env` file
> - Manual stop: `docker exec -it trendradar python manage.py stop_webserver`
> - Manual start: `docker exec -it trendradar python manage.py start_webserver`
> - Security tip: Only provides static file access, restricted to the output directory, and bound to local access only

#### Data Persistence

Generated reports and data are saved in the `./output` directory by default, and the data will be retained even if the container is restarted or deleted.

**📊 Web Report Access Paths**:

The daily summary HTML report generated by TrendRadar will be saved to two locations simultaneously:

| File Location | Access Method | Applicable Scenario |
|---------|---------|---------|
| `output/index.html` | Direct access from host | **Docker Deployment** (visible to host via Volume mount) |
| `index.html` | Root directory access | **GitHub Pages** (repository root, automatically recognized by Pages) |
| `output/html/YYYY-MM-DD/Daily Summary.html` | Historical report access | All environments (archived by date) |

**Local Access Examples**:
```bash
# Method 1: Access via Web Server (Recommended, Docker environment)
# 1. Start the Web Server
docker exec -it trendradar python manage.py start_webserver
# 2. Access in browser
http://localhost:8080                           # Access the latest report (default index.html)
http://localhost:8080/html/2025-xx-xx/          # Access the report for a specific date

# Method 2: Open the file directly (Local environment)
open ./output/index.html             # macOS
start ./output/index.html            # Windows
xdg-open ./output/index.html         # Linux

# Method 3: Access historical archives
open ./output/html/2025-xx-xx/summary of the day.html
```

**Why are there two index.html files?**
- `output/index.html`: Docker Volume mounted to the host, can be opened directly locally
- `index.html`: Pushed to the repository by GitHub Actions, automatically deployed by GitHub Pages

> 💡 **Tip**: The contents of the two files are exactly the same, you can choose either one to access.

#### Troubleshooting

```bash
# Check container status
docker inspect trendradar

# View container logs
docker logs --tail 100 trendradar

# Enter container for debugging
docker exec -it trendradar /bin/bash

# Verify configuration file
docker exec -it trendradar ls -la /app/config/
```

#### MCP Service Deployment (AI Analysis Feature)

If you need to use the AI analysis feature, you can deploy an independent MCP service container.

**Architecture Description**:

```mermaid
flowchart TB
    subgraph trendradar["trendradar"]
        A1[Scheduled news fetching]
        A2[Push notifications]
    end
    
    subgraph trendradar-mcp["trendradar-mcp"]
        B1[127.0.0.1:3333]
        B2[AI analysis API]
    end
    
    subgraph shared["Shared volume"]
        C1["config/ (ro)"]
        C2["output/ (ro)"]
    end
    
    trendradar --> shared
    trendradar-mcp --> shared
```

**Quick Start**:

If you have already deployed using [Method 1: Using docker compose](# Method 1 using-docker-compose recommended), simply start the MCP service:

```bash
cd TrendRadar/docker
docker compose up -d trendradar-mcp

# Check running status
docker ps | grep trendradar-mcp
```

**Start MCP service independently** (without docker compose):

```bash
# Linux/Mac
docker run -d --name trendradar-mcp \
  -p 127.0.0.1:3333:3333 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/output:/app/output:ro \
  -e TZ=Asia/Shanghai \
  wantcat/trendradar-mcp:latest

# Windows PowerShell
docker run -d --name trendradar-mcp `
  -p 127.0.0.1:3333:3333 `
  -v ${PWD}/config:/app/config:ro `
  -v ${PWD}/output:/app/output:ro `
  -e TZ=Asia/Shanghai `
  wantcat/trendradar-mcp:latest
```

> ⚠️ **Note**: When running independently, ensure the `config/` and `output/` folders exist in the current directory, and contain the configuration files and news data.

**Verify service**:

```bash
# Check MCP service health status
curl http://127.0.0.1:3333/mcp

# View MCP service logs
docker logs -f trendradar-mcp
```

**Configure in AI clients**:

After the MCP service is started, configure it according to the different clients:

**Cherry Studio** (Recommended, GUI configuration):
- Settings → MCP Server → Add
- Type: `streamableHttp`
- URL：`http://127.0.0.1:3333/mcp`

**Claude Desktop / Cline** (JSON configuration):
```json
{
  "mcpServers": {
    "trendradar": {
      "url": "http://127.0.0.1:3333/mcp",
      "type": "streamableHttp"
    }
  }
}
```

> 💡 **Tip**: The MCP service only listens on the local port (127.0.0.1) to ensure security. If remote access is required, please configure a reverse proxy and authentication yourself.

</details>

### 7. How is the pushed content displayed?

<details>
<summary>👉 Click to expand: <strong>Customize push style and content</strong></summary>
<br>

**Configuration location:** `report` and `display` sections in `config/config.yaml`

```yaml
report:
  mode: "daily"                    # Push mode
  display_mode: "keyword"          # Display mode (Added in v4.6.0)
  rank_threshold: 5                # Rank highlight threshold
  sort_by_position_first: false    # Sorting priority
  max_news_per_keyword: 0          # Maximum display quantity per keyword

display:
  region_order:                    # Region display order (Added in v5.2.0)
    - new_items                    # New hot items region
    - hotlist                      # Hotlist region
    - rss                          # RSS subscription region
    - standalone                   # Standalone display region
    - ai_analysis                  # AI analysis region
```

#### Common configuration items explanation

| What I want to adjust | Which parameter to modify | Default value | Description |
|-------------|-------------|-------|------|
| **Push mode** | `mode` | `daily` | Determines push timing and content, see [Push mode details](#3-Push mode details) |
| **Grouping method** | `display_mode` | `keyword` | `keyword`=Group by keyword (e.g., "AI"), `platform`=Group by platform (e.g., "Weibo") |
| **Highlight focus** | `rank_threshold` | `5` | News ranked in the top 5 will be displayed in **bold**, letting you see the hottest ones at a glance |
| **Sorting rules** | `sort_by_position_first` | `false` | `false`=Higher popularity ranks first, `true`=Your configured words rank first |
| **Quantity limit** | `max_news_per_keyword` | `0` | Maximum number of news per keyword? `0` means unlimited |
| **Display Order** | `display.region_order` | See configuration above | Adjust the list order to control the display position of each region |

#### Grouping Method Comparison (display_mode)

Do you want to see "what news is under this topic" or "what news is on this platform"?

| Mode | Grouping Method | Title Prefix | Applicable Scenario |
|------|---------|---------|---------|
| `keyword` (Default) | **Aggregate by Keyword** | `[Platform Name]` | I follow "AI" and want to see news about AI across all platforms |
| `platform` | **Aggregate by Platform** | `[Keyword]` | I follow "Weibo" and want to see news on Weibo about my followed keywords |

#### Region Display Order (region_order)

By adjusting the order of the `display.region_order` list, you can control the display position of each region in the push message.

**Default Order**: New Hot Topics → Hotlist → RSS → Standalone Display Area → AI Analysis

**Custom Example**: Want to put AI Analysis at the very beginning?

```yaml
display:
  region_order:
    - ai_analysis                  # Move to the first line
    - new_items
    - hotlist
    - rss
    - standalone
```

**Note**: A region will only be displayed if it meets both of the following conditions:
1. It is in the `region_order` list
2. The corresponding switch in `display.regions` is `true`

#### Region Switches (regions)

Control whether each region is displayed in the push message via `display.regions`:

```yaml
display:
  regions:
    hotlist: true                    # Hotlist region (hot news matching keywords)
    new_items: false                 # New hot topics region (includes new hotlist items + new RSS items)
    rss: true                       # RSS subscription region (RSS content matching keywords)
    standalone: false                # Standalone display area (complete hotlist/RSS, unaffected by keyword filtering)
    ai_analysis: true                # AI analysis region
```

| Region | Configuration Key | Default Value | Description |
|------|--------|-------|------|
| **Hotlist** | `hotlist` | `true` | Aggregation of hot news matching keywords |
| **New Hot Topics** | `new_items` | `false` | Newly emerged hot topics in this round (includes new hotlist items + new RSS items). Note: The 🆕 mark in the hotlist region is not affected by this switch |
| **RSS** | `rss` | `true` | RSS subscription content matching keywords. If disabled, RSS analysis is skipped, but RSS in the standalone display area is not affected |
| **Standalone Display Area** | `standalone` | `false` | Complete content display of specified platforms/RSS, unaffected by keyword filtering |
| **AI Analysis** | `ai_analysis` | `true` | AI-generated hot topic analysis summary |

#### Sorting Priority (sort_by_position_first)

Suppose you configured the keywords: 1. Tesla, 2. BYD.
Actual popularity: BYD (10 items), Tesla (3 items).

| Configuration Value | Sorting Result | Your Thought |
|-------|---------|---------|
| `false` (Default) | BYD (10 items) → Tesla (3 items) | "Whatever is more popular goes first" |
| `true` | Tesla (3 items) → BYD (10 items) | "My configured order is the priority, regardless of popularity" |

#### Standalone Display Area (standalone)

**Scenario**: For some platforms (like Zhihu Hotlist, HackerNews), I want to **read them completely**, regardless of whether they match my keywords.

```yaml
display:
  regions:
    standalone: true                  # Display standalone display area in push message (disabling does not affect AI analysis)

  standalone:
    platforms: ["zhihu", "weibo"]     # Display the hotlists of these platforms completely
    rss_feeds: ["hacker-news"]        # Display the content of these RSS feeds completely
    max_items: 20                     # Maximum number of items to display
```

> 💡 **Independent Control of Push Display and AI Analysis**: `regions.standalone` only controls whether the standalone display area is shown in the push message. Even if the push display is disabled, as long as `include_standalone: true` is enabled in the AI configuration, the AI will still analyze the complete data of these platforms. Suitable for users who want the AI to do deep analysis but don't want the push message to be too long.

</details>

### 8. When will I receive pushes?

<details>
<summary>👉 Click to expand: <strong>Set push time (Scheduling System)</strong></summary>
<br>

**Configuration location:** `schedule` section in `config/config.yaml` + `config/timeline.yaml`

#### Quick Start

Just select a preset template in `config.yaml`, no need to edit `timeline.yaml`:

```yaml
schedule:
  enabled: true
  preset: "morning_evening"     # Just change this
```

#### Available Preset Templates

| Template Name | Description | Push Behavior |
|-------|------|---------|
| `morning_evening` | All-day incremental + Evening summary (Recommended) | Push on new updates all day + 19:00-21:00 evening daily summary |
| `always_on` | 24/7 monitoring | Push on new updates all day, no time periods |
| `office_hours` | Office hours | Weekday 3-phase (Arrival quick look → Noon hot topics → Off-work summary), weekend incremental free push |
| `night_owl` | Night owl | Afternoon quick look + Late night all-day summary (22:00-01:00 across midnight) |
| `custom` | Fully custom | Edit the custom section at the bottom of `timeline.yaml` |

#### Fully Custom

If none of the preset templates meet your needs, you can edit the `custom` section at the bottom of `config/timeline.yaml` to freely define time periods, daily plans, and weekly mappings. See the comments in the `timeline.yaml` file for details.

#### Important Notes

> ⚠️ **Note for users upgrading from older versions:**
> - v6.0.0 removed the old `notification.push_window` and `ai_analysis.analysis_window` configurations
> - Please use the new `schedule` + `timeline.yaml` scheduling system instead
> - The old "push once a day" can be replaced by the `morning_evening` preset
> - The old "push during working hours" can be replaced by the `office_hours` preset

> ⚠️ **Note for GitHub Actions users:**
> - GitHub Actions execution time is unstable, there may be a deviation of ±15 minutes
> - It is recommended to leave at least **2 hours** for the time period range
> - If you want precise scheduled pushes, it is recommended to use **Docker deployment** on a personal server

</details>

### 9. How often does it run?

<details>
<summary>👉 Click to expand: <strong>Set automatic run frequency</strong></summary>
<br>

**Configuration location:** `schedule` section in `.github/workflows/crawler.yml`

```yaml
on:
  schedule:
    - cron: "0 * * * *"  # Run once an hour
```

#### How to modify the run frequency?

GitHub Actions uses a time format called "Cron". You don't need to understand it deeply, just copy the code below and replace it.

**Configuration location:** `schedule` section in the `.github/workflows/crawler.yml` file

| I want to... | Copy this line of code | Description |
|-----------|------------|------|
| **Once an hour** | `- cron: "0 * * * *"` | **Default configuration**, runs at the 0th minute |
| **Every 30 minutes** | `- cron: "*/30 * * * *"` | Runs every 30 minutes |
| **Every day at 8 AM** | `- cron: "0 0 * * *"` | ⚠️ Write `0` because UTC time (0:00) = Beijing time (8:00) |
| **Every half hour during working hours** | `- cron: "*/30 0-14 * * *"` | Corresponds to Beijing time 8:00 - 22:00 |
| **Three meals a day** | `- cron: "0 0,6,12 * * *"` | Corresponds to Beijing time 8:00, 14:00, 20:00 |

#### ⚠️ Two Important Reminders

1. **Time zone difference**: GitHub's servers are abroad and use UTC time.
   - **Simple math**: The Beijing time you want to set **minus 8 hours** = the time you need to fill in.
   - *Example: If you want it to run at 20:00 Beijing time, you need to fill in 12:00 in the settings*

2. **Not too frequent**: It is recommended that the interval is not less than 30 minutes.
   - GitHub's free resources are limited; running it too frequently may result in your account being restricted.
   - Moreover, Actions startup itself has a delay of a few minutes, so overly precise control is meaningless.

#### Step-by-step modification steps

1. In your GitHub repository, find the `.github/workflows/crawler.yml` file
2. Click the ✏️ (Edit) button in the top right corner
3. Find the line with `cron: "..."`, and replace the content inside the quotes with the "code" above
4. Click the green **Commit changes** button in the top right corner to save

</details>

### 10. Push to multiple groups/devices

<details>
<summary>👉 Click to expand: <strong>Push to multiple recipients simultaneously</strong></summary>

> ### ⚠️ **Safety first**
> **Do not write passwords/Tokens directly in `config.yaml`!**
> If you upload a file containing passwords to GitHub, the whole world can see it.
>
> **Correct approach**:
> - **GitHub Actions users**: Go to Settings -> Secrets to add them
> - **Docker users**: Write them in the `.env` file (this file will not be uploaded)

#### How to push to multiple places simultaneously?

It's very simple, just use a semicolon `;` to separate multiple addresses when configuring.

**For example**:
Suppose you have two Feishu groups and want to receive pushes simultaneously:
- Group 1 address: `https://.../webhook/aaa`
- Group 2 address: `https://.../webhook/bbb`

Fill in during configuration:
`https://.../webhook/aaa;https://.../webhook/bbb`

#### Platforms supporting multiple accounts

| Platform | Configuration Method | Notes |
|------|---------|----------|
| **Feishu/DingTalk/WeCom** | Use `;` to separate multiple Webhook URLs | The simplest, just string them together |
| **Bark (iOS)** | Use `;` to separate multiple Key URLs | Push to multiple iPhones |
| **Telegram** | Both Token and ChatID must be separated by `;` | ⚠️ **Note the order must correspond**: <br>Token1 corresponds to ChatID1<br>Token2 corresponds to ChatID2 |
| **ntfy** | Both Topic and Token must be separated by `;` | If a Topic doesn't need a Token, just leave it blank: <br>`token1;;token3` (the middle one is empty) |

#### Common configuration examples (GitHub Secrets / .env)

```bash
# Feishu sends to 3 groups
FEISHU_WEBHOOK_URL=https://hook1...;https://hook2...;https://hook3...

# DingTalk sends to 2 groups
DINGTALK_WEBHOOK_URL=https://oapi...;https://oapi...

# Telegram sends to 2 people (note one-to-one correspondence)
TELEGRAM_BOT_TOKEN=tokenA;tokenB
TELEGRAM_CHAT_ID=userA;userB
```

> **Tip**: To prevent abuse, the default limit is a maximum of 3 accounts per platform. If you need more, you can modify the `MAX_ACCOUNTS_PER_CHANNEL` configuration.

</details>

### 11. Where is the data saved?

<details id="storage-config">
<summary>👉 Click to expand: <strong>Select data storage location</strong></summary>
<br>

#### Where will the data be stored?

The system will automatically choose the most suitable place for you, you usually don't need to worry about it:

| Your Environment | Where Data is Stored | Description |
|-------------|-----------|------|
| **Docker / Local Run** | **Local Hard Drive** | Stored in the `output/` folder under the project directory, can be viewed at any time. |
| **GitHub Actions** | **Cloud Storage** | Because GitHub Actions destroys the environment after running, you must configure cloud storage (e.g., Cloudflare R2). |

#### How to Configure Cloud Storage? (Must-read for GitHub Actions Users)

If you are running with GitHub Actions, you need a "cloud drive" to store data. For example, use Cloudflare R2 (because it has a free tier).

**Add these 5 variables in GitHub Secrets:**

| Variable Name | What to Fill In |
|-------|-------|
| `STORAGE_BACKEND` | `remote` |
| `S3_BUCKET_NAME` | Your bucket name |
| `S3_ACCESS_KEY_ID` | Your Access Key |
| `S3_SECRET_ACCESS_KEY` | Your Secret Key |
| `S3_ENDPOINT_URL` | Your R2 endpoint URL |

> 💡 **Detailed Tutorial**: How to apply for R2? Please see [Quick Start - Remote Storage Configuration](#-Quick Start)

#### How Long Will Data Be Saved?

By default, we will not automatically delete your data. But if you feel there is too much data taking up space, you can set up "auto-cleanup".

**Configuration Location**: `config/config.yaml`

```yaml
storage:
  local:
    retention_days: 30    # Local data is only kept for 30 days (0 means permanent)
  remote:
    retention_days: 30    # Cloud data is only kept for 30 days
```

#### Push Time is Incorrect? (Timezone Settings)

If you are overseas, or find that the push time does not match your local time, you can modify the timezone.

**Configuration Location**: `config/config.yaml`

```yaml
app:
  timezone: "Asia/Shanghai"  # Default is China time
```
- For example, if you are in Los Angeles, USA, change it to: `America/Los_Angeles`
- For example, if you are in London, UK, change it to: `Europe/London`

</details>

### 12. Let AI Help Me Analyze Trending Topics

<details id="ai-analysis-config">
<summary>👉 Click to expand: <strong>Enable AI Smart Analysis Feature</strong></summary>
<br>

#### What Can AI Do for Me?

After enabling this feature, AI will act like a professional analyst when pushing each batch of news:
1. **Auto-read**: Read all matched trending news
2. **Deep Thinking**: Analyze the connections between originally isolated news
3. **Write Reports**: Attach a short and profound "insight report" at the end of the push message

**Included Content**: Trending trend summary, public opinion direction judgment, cross-platform correlation analysis, potential impact assessment, etc.

#### How to Enable AI Analysis?

The simplest method is through environment variable configuration (GitHub Secrets or .env is recommended).

**Required Configuration Items**:

| Variable Name | What to Fill In | Description |
|-------|-------|------|
| `AI_ANALYSIS_ENABLED` | `true` | Enable switch |
| `AI_API_KEY` | `sk-xxxxxx` | Your API Key |
| `AI_MODEL` | `deepseek/deepseek-chat` | Model identifier (Format: `provider/model`) |

**Supported AI Providers** (Based on LiteLLM, supports 100+ providers):

| Provider | What to Fill in AI_MODEL | Description |
|-------|----------------|------|
| **DeepSeek** (Recommended) | `deepseek/deepseek-chat` | Extremely cost-effective, suitable for high-frequency analysis |
| **OpenAI** | `openai/gpt-4o`<br>`openai/gpt-4o-mini` | GPT-4o Series |
| **Google Gemini** | `gemini/gemini-1.5-flash`<br>`gemini/gemini-1.5-pro` | Gemini Series |
| **Custom API** | Any format | Use with `AI_API_BASE` |

> 💡 **New Feature**: Now based on the [LiteLLM](https://github.com/BerriAI/litellm) unified interface, supporting 100+ AI providers with simpler configuration and better error handling.

**Optional Configurations**:

| Variable Name | Default Value | Description |
|-------|-------|------|
| `AI_API_BASE` | (Auto) | Custom API address (e.g., OneAPI, local models) |
| `AI_TEMPERATURE` | `1.0` | Sampling temperature (0-2, higher is more random) |
| `AI_MAX_TOKENS` | `5000` | Maximum generated tokens |
| `AI_TIMEOUT` | `120` | Request timeout (seconds) |
| `AI_NUM_RETRIES` | `2` | Number of retries on failure |

#### Advanced Usage: AI Translation

If you follow foreign RSS feeds (like Hacker News), AI can help translate the content into Chinese and push it to you.

**Configuration Location**: `config/config.yaml`

```yaml
ai_translation:
  enabled: true          # Enable translation
  language: "Chinese"    # Target language for translation (Chinese, English, Japanese...)
```

#### Advanced Usage: Custom AI "Persona"

Think the AI sounds too official? You can modify its prompt to change it to your preferred style (e.g., "sharp-tongued commentator", "senior investment advisor").

- **File to Modify**: `config/ai_analysis_prompt.txt`
- **How to Modify**: Open and edit directly with a text editor, telling the AI what kind of analysis style you want.

</details>

<br>

## ✨ AI Intelligent Analysis

TrendRadar v3.0.0 adds an AI analysis feature based on **MCP (Model Context Protocol)**, allowing you to converse with news data using natural language for in-depth analysis.


### ⚠️ Must Read Before Use


**Important Note: AI features require local news data support**

The AI analysis feature does **not** directly query real-time network data, but analyzes your **accumulated local news data** (stored in the `output` folder)


#### Usage Instructions:

1. **Project's built-in test data**: The `output` directory contains a week of trending news data from **2025-12-21 to 2025-12-27** by default, which can be used to quickly experience the AI features

2. **Query Limitations**:
   - ✅ Can only query data within the existing date range (December 21-27, 7 days in total)
   - ❌ Cannot query real-time news or future dates

3. **Getting the Latest Data**:
   - Test data is only for a quick experience, **it is recommended to deploy the project yourself** to get real-time data
   - Follow [Quick Start](#-Quick Start) to deploy and run the project
   - Wait at least 1 day to accumulate news data, then you can query the latest hot topics


### 1. Quick Deployment

Cherry Studio provides a GUI configuration interface for a 5-minute quick deployment, and the complex parts are installed with one click.

**Graphic Deployment Tutorial**: Now updated on my [Official Account](#-support project), just reply "mcp"

**Detailed Deployment Tutorial**: [README-Cherry-Studio.md](README-Cherry-Studio.md)

**Deployment Mode Description**:
- **STDIO Mode (Recommended)**: Configure once and no need to repeat later. The **graphic deployment tutorial** only uses the configuration of this mode as an example.
- **HTTP Mode (Alternative)**: If you encounter problems configuring STDIO mode, you can use HTTP mode. The configuration method of this mode is basically the same as STDIO, but the content to copy and paste is just one line, making it less prone to errors. The only thing to note is that you need to manually start the service before each use. For details, please refer to the HTTP mode instructions at the bottom of [README-Cherry-Studio.md](README-Cherry-Studio.md).

### 2. Learning How to Converse with AI

**Detailed Conversation Tutorial**: [README-MCP-FAQ.md](README-MCP-FAQ.md)

> 💡 **Tip**: In practice, it is not recommended to ask multiple questions at once. If the AI model you choose cannot even perform the sequential calls shown in the figure below, it is recommended to change to another one.

<img src="/_image/ai4.png" alt="mcp usage effect" width="600">

<br>

## 🔌 MCP Clients

The TrendRadar MCP service supports the standard Model Context Protocol (MCP) and can be integrated with various MCP-supported AI clients for intelligent analysis.

### Supported Clients

**Notes**:
- Replace `/path/to/TrendRadar` with your actual project path
- Use double backslashes for Windows paths: `C:\\Users\\YourName\\TrendRadar`
- Remember to restart after saving

<details>
<summary>👉 Click to expand: <b>Cursor</b></summary>

#### Method 1: HTTP Mode

1. **Start the HTTP Service**:
   ```bash
   # Windows
   start-http.bat
   
   # Mac/Linux
   ./start-http.sh
   ```

2. **Configure Cursor**:

   **Project-level Configuration** (Recommended):
   Create `.cursor/mcp.json` in the project root directory:
   ```json
   {
     "mcpServers": {
       "trendradar": {
         "url": "http://localhost:3333/mcp",
         "description": "TrendRadar News Hotspot Aggregation Analysis"
       }
     }
   }
   ```

   **Global Configuration**:
   Create `~/.cursor/mcp.json` in the user directory (with the same content)

3. **Usage Steps**:
   - Restart Cursor after saving the configuration file
   - Check the connected tools in "Available Tools" in the chat interface
   - Start using: `Search for today's "AI" related news`

#### Method 2: STDIO Mode (Recommended)

Create `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "trendradar": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/TrendRadar",
        "run",
        "python",
        "-m",
        "mcp_server.server"
      ]
    }
  }
}
```

</details>

<details>
<summary>👉 Click to expand: <b>VSCode (Cline/Continue)</b></summary>

#### Cline Configuration

Add to Cline's MCP settings:

**HTTP Mode**:
```json
{
  "trendradar": {
    "url": "http://localhost:3333/mcp",
    "type": "streamableHttp",
    "autoApprove": [],
    "disabled": false
  }
}
```

**STDIO Mode** (Recommended):
```json
{
  "trendradar": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/TrendRadar",
      "run",
      "python",
      "-m",
      "mcp_server.server"
    ],
    "type": "stdio",
    "disabled": false
  }
}
```

#### Continue Configuration

Edit `~/.continue/config.json`:
```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "uv",
          "args": [
            "--directory",
            "/path/to/TrendRadar",
            "run",
            "python",
            "-m",
            "mcp_server.server"
          ]
        }
      }
    ]
  }
}
```

**Usage Examples**:
```
Analyze the popularity trend of "Tesla" over the last 7 days
Generate today's hotspot summary report
Search for "Bitcoin" related news and analyze sentiment
```

</details>

<details>
<summary>👉 Click to expand: <b>MCP Inspector</b> (Debugging Tool)</summary>
<br>

MCP Inspector is the official debugging tool used to test MCP connections:

#### Usage Steps

1. **Start the TrendRadar HTTP Service**:
   ```bash
   # Windows
   start-http.bat
   
   # Mac/Linux
   ./start-http.sh
   ```

2. **Start MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

3. **Connect in the Browser**:
   - Visit: `http://localhost:3333/mcp`
   - Test the "Ping Server" function to verify the connection
   - Check if "List Tools" returns 17 tools:
     - Basic Queries: get_latest_news, get_news_by_date, get_trending_topics
     - Smart Retrieval: search_news, find_related_news
     - Advanced Analysis: analyze_topic_trend, analyze_data_insights, analyze_sentiment, aggregate_news, compare_periods, generate_summary_report
     - RSS Queries: get_latest_rss, search_rss, get_rss_feeds_status
     - System Management: get_current_config, get_system_status, resolve_date_range

</details>

<details>
<summary>👉 Click to expand: <b>Other Clients Supporting MCP</b></summary>
<br>

Any client that supports the Model Context Protocol can connect to TrendRadar:

#### HTTP Mode

**Service Address**: `http://localhost:3333/mcp`

**Basic Configuration Template**:
```json
{
  "name": "trendradar",
  "url": "http://localhost:3333/mcp",
  "type": "http",
  "description": "Trending News Aggregation Analysis"
}
```

#### STDIO Mode (Recommended)

**Basic Configuration Template**:
```json
{
  "name": "trendradar",
  "command": "uv",
  "args": [
    "--directory",
    "/path/to/TrendRadar",
    "run",
    "python",
    "-m",
    "mcp_server.server"
  ],
  "type": "stdio"
}
```

**Notes**:
- Replace `/path/to/TrendRadar` with the actual project path
- Windows paths use backslash escaping: `C:\\Users\\...`
- Ensure project dependencies are installed (setup script has been run)

</details>



### FAQ

<details>
<summary>👉 Click to expand: <b>Q1: HTTP service fails to start?</b></summary>
<br>

**Check Steps**:
1. Confirm port 3333 is not occupied:
   ```bash
   # Windows
   netstat -ano | findstr :3333
   
   # Mac/Linux
   lsof -i :3333
   ```

2. Check if project dependencies are installed:
   ```bash
   # Re-run the installation script
   # Windows: setup-windows.bat or setup-windows-en.bat
   # Mac/Linux: ./setup-mac.sh
   ```

3. View detailed error logs:
   ```bash
   uv run python -m mcp_server.server --transport http --port 3333
   ```
4. Try a custom port:
   ```bash
   uv run python -m mcp_server.server --transport http --port 33333
   ```

</details>

<details>
<summary>👉 Click to expand: <b>Q2: Client cannot connect to the MCP service?</b></summary>
<br>

**Solutions**:

1. **STDIO Mode**:
   - Confirm the UV path is correct (run `which uv` or `where uv`)
   - Confirm the project path is correct and contains no Chinese characters
   - Check the client error logs

2. **HTTP Mode**:
   - Confirm the service is started (visit `http://localhost:3333/mcp`)
   - Check firewall settings
   - Try using 127.0.0.1 instead of localhost

3. **General Checks**:
   - Restart the client application
   - Check the MCP service logs
   - Use MCP Inspector to test the connection

</details>

<details>
<summary>👉 Click to expand: <b>Q3: Tool call failed or returned an error?</b></summary>
<br>

**Possible Causes**:

1. **Data does not exist**:
   - Confirm the crawler has been run (there is data in the output directory)
   - Check if there is data for the queried date range
   - Check the available dates in the output directory

2. **Parameter Error**:
   - Check the date format: `YYYY-MM-DD`
   - Confirm the platform ID is correct: `zhihu`, `weibo`, etc.
   - Check the parameter descriptions in the tool documentation

3. **Configuration Issues**:
   - Confirm `config/config.yaml` exists
   - Confirm `config/frequency_words.txt` exists
   - Check if the configuration file format is correct

</details>

<br>

## 📚 Project Related

> **4 Articles**:

- [You can leave a message below this article, making it convenient for the project author to answer questions via mobile phone](https://mp.weixin.qq.com/s/KYEPfTPVzZNWFclZh4am_g)
- [Breaking 1000 stars in 2 months, my practical experience in promoting GitHub projects](https://mp.weixin.qq.com/s/jzn0vLiQFX408opcfpPPxQ)
- [Precautions for running this project after a GitHub fork ](https://mp.weixin.qq.com/s/C8evK-U7onG1sTTdwdW2zg)
- [How to write articles for WeChat official accounts or news feeds based on this project](https://mp.weixin.qq.com/s/8ghyfDAtQZjLrnWTQabYOQ)

>**AI Development**:
- If you have niche needs, you can completely develop them yourself based on my project; even those with zero programming foundation can give it a try
- All my open-source projects have more or less used the **AI assistant software** I wrote myself to improve development efficiency, and this tool is now open-source
- **Core Function**: Quickly filter project code to feed to AI, you only need to supplement your personal requirements
- **Project Address**: https://github.com/sansan0/ai-code-context-helper

### Other Projects

> 📍 Chairman Mao's Footprint Map - Interactive dynamic display of the complete trajectory from 1893-1976. Comrades are welcome to contribute data

- https://github.com/sansan0/mao-map

> Bilibili comment section data visualization and analysis software

- https://github.com/sansan0/bilibili-comment-analyzer


[![Star History Chart](https://api.star-history.com/svg?repos=sansan0/TrendRadar&type=Date)](https://www.star-history.com/#sansan0/TrendRadar&Date)

<br>

## 📄 License

GPL-3.0 License

---

<div align="center">

[🔝 Back to Top](#trendradar)

</div>
