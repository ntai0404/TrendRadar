# Universal News/Web Crawler Skill

This crawler converts a user instruction plus observed browser HTML into a reliable multi-item extraction workflow.

## Operating Principles

- Treat the user instruction as the business goal, not a keyword-only search request.
- Prefer deterministic navigation when the page already exposes a relevant category, topic, listing, profile, group, or collection link.
- Use search only when no better listing/category route exists.
- Never extract a homepage shell, login page, menu, footer, recommendation block, or utility page as if it were the requested content.
- For requests asking for `N` items, produce up to `N` independent target items. Each item must have its own metadata, screenshot, content, and HTML.
- If fewer than `N` real target items are visible, return fewer clean items instead of padding with unrelated links.
- Do not invent URLs, dates, authors, or facts. Use null/empty fields when not visible.

## Planning Workflow

1. Understand the requested target type: article, post, video, profile, product, table row, document, or generic web page.
2. If the user asks for separate quotas/topics/sources, split them into independent collection goals. Never combine separate topics like "5 stock articles and 5 AI articles" into one query.
3. Determine whether the current page is a homepage, searchable platform, listing/category page, search results page, detail page, or login/checkpoint page.
4. If a direct URL is mentioned in the instruction, set `navigation_url` to that URL unless it is clearly not the intended target.
5. If the page navigation/menu contains a relevant category/topic link, prefer `navigation_url` to that link over search.
6. If no listing/category link is available but the site has search, set `needs_search=true` and preserve the clean query.
7. If already on a listing/results page, set `needs_search=false` and provide a result selector if visible.

## Target Selection Rules

- Detail URLs are preferred over category/search/home URLs.
- Article/news URLs usually have headline text and often end in `.html`; prefer links inside `article`, `.item-news`, `.title-news`, `h1`, `h2`, or `h3`.
- Social posts should be post/permalink URLs, not login, about, profile root, or recovery URLs.
- Videos should be watch/detail URLs, not channel navigation or Shorts unless Shorts are explicitly requested.
- Exclude utility/navigation links: login, account, calendar, weather, RSS, terms, privacy, contact, ads, comments, footer, and homepage.

## Extraction Rules

- Extract the main target content from the final detail page.
- Extract metadata first, before writing the summary/content.
- Metadata priority order is: JSON-LD/schema.org (`headline`, `name`, `author`, `creator`, `publisher`, `datePublished`, `dateModified`, `uploadDate`, `articleSection`, `keywords`), then OpenGraph/Twitter/article meta tags (`og:title`, `article:author`, `article:published_time`, `article:modified_time`, `article:section`, `article:tag`, `keywords`, `og:site_name`), then semantic visible HTML (`h1`, byline, `time[datetime]`, `itemprop=datePublished/dateModified`, breadcrumbs, visible tags).
- If a metadata hint is provided by the crawler from JSON-LD/meta/time tags, use it unless the final page visibly contradicts it.
- Fill metadata naturally for the page type: title, author/source, published date, category, tags, summary, content, language.
- Remove boilerplate: menus, sidebars, ads, cookie banners, comments, related/recommended items, repeated labels, and footer text.
- If final page is still a listing/search page, summarize the relevant visible result list and state that no detail page was opened.
- Do not leave `published_at` null when JSON-LD/meta/time tags contain a publication, upload, or modified date.
