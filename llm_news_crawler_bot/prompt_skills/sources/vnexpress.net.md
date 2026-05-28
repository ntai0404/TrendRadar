# Source Skill: VnExpress

Use this skill for `vnexpress.net`.

## Navigation

- For stock market / securities / "chứng khoán", prefer:
  `https://vnexpress.net/kinh-doanh/chung-khoan`
- For business topics, prefer `/kinh-doanh` subcategories before site search.
- VnExpress exposes useful category links in header/menu HTML. Do not ignore navigation links.
- The header search input may be hidden. If it is not visible/editable, use category navigation or the metadata search action instead of failing back to homepage extraction.

## Article Selection

- Prefer real article links ending with `.html`.
- Prefer anchors inside:
  - `article.item-news`
  - `.item-news .title-news a`
  - `.title-news a`
  - `h1/h2/h3 a`
- Do not select utility links such as:
  - `/lich-van-nien`
  - `/tin-tuc-24h`
  - `/tin-xem-nhieu`
  - `/rss`
  - `/lien-he-toa-soan`
  - terms/privacy/contact/calendar/weather pages

## Extraction

- VnExpress article pages often include JSON-LD `NewsArticle`; use it when visible for title, date, author/publisher, image, and category.
- The useful body is usually in the article content area, not "Tin xem thêm", "Xem nhiều", comments, or footer blocks.
