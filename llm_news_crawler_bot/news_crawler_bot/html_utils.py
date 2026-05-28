import json
import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup


NOISE_SELECTORS: Iterable[str] = (
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "form",
    "nav",
    "header",
    "footer",
    "aside",
    "[role='navigation']",
    "[aria-hidden='true']",
)


def compact_html(html: str, limit: int = 45000, keep_navigation: bool = False) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    noise = NOISE_SELECTORS
    if keep_navigation:
        noise = tuple(
            selector
            for selector in NOISE_SELECTORS
            if selector not in {"form", "nav", "header", "[role='navigation']"}
        )
    for selector in noise:
        for node in soup.select(selector):
            node.decompose()
    text = str(soup.body or soup)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def heuristic_article_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()

    candidates = soup.select("article, main, [class*='article'], [class*='content'], [id*='article'], [id*='content']")
    if not candidates:
        candidates = [soup.body or soup]

    best = max(candidates, key=lambda node: len(node.get_text(" ", strip=True)))
    lines = [line.strip() for line in best.get_text("\n", strip=True).splitlines()]
    lines = [line for line in lines if len(line) > 20]
    return "\n".join(lines)


def page_title(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(" ", strip=True)
    return "Untitled article"


def extract_metadata_hints(html: str, final_url: str = "") -> dict:
    """Extract high-confidence metadata from common web standards."""
    soup = BeautifulSoup(html or "", "lxml")
    json_ld_nodes = _json_ld_nodes(soup)

    title = _first_nonempty(
        _json_ld_value(json_ld_nodes, ("headline", "name", "title")),
        _meta_value(soup, "og:title", "twitter:title", "title"),
        page_title(html),
    )
    author = _first_nonempty(
        _json_ld_people_value(json_ld_nodes, "author"),
        _meta_value(soup, "article:author", "author", "byl", "byline", "dc.creator"),
        _json_ld_people_value(json_ld_nodes, "creator"),
        _json_ld_people_value(json_ld_nodes, "publisher"),
        _meta_value(soup, "og:site_name", "application-name"),
    )
    published_at = _first_nonempty(
        _json_ld_value(json_ld_nodes, ("datePublished", "uploadDate", "dateCreated", "datePosted")),
        _meta_value(
            soup,
            "article:published_time",
            "article:modified_time",
            "og:updated_time",
            "date",
            "pubdate",
            "publishdate",
            "publication_date",
            "dc.date",
            "dc.date.issued",
            "sailthru.date",
        ),
        _time_value(soup),
    )
    category = _first_nonempty(
        _json_ld_value(json_ld_nodes, ("articleSection", "section", "genre")),
        _meta_value(soup, "article:section", "section", "category", "parsely-section"),
    )
    tags = _unique_values(
        _json_ld_list_value(json_ld_nodes, "keywords")
        + _meta_values(soup, "article:tag", "keywords", "news_keywords", "parsely-tags")
    )
    language = _first_nonempty(
        (soup.html.get("lang") if soup.html else None),
        _meta_value(soup, "og:locale", "language", "content-language"),
    )
    canonical_url = _first_nonempty(
        _link_value(soup, "canonical", final_url),
        _meta_value(soup, "og:url"),
        final_url,
    )

    return {
        "canonical_url": canonical_url,
        "title": title,
        "author": author,
        "published_at": published_at,
        "category": category,
        "tags": tags,
        "language": language,
    }


def merge_metadata_hints(metadata, hints: dict):
    for field in ("title", "author", "published_at", "category", "language"):
        if not getattr(metadata, field, None) and hints.get(field):
            setattr(metadata, field, hints[field])

    hinted_tags = hints.get("tags") or []
    if hinted_tags:
        seen = {tag.strip().lower() for tag in metadata.tags if tag and tag.strip()}
        for tag in hinted_tags:
            clean_tag = str(tag).strip()
            if clean_tag and clean_tag.lower() not in seen:
                metadata.tags.append(clean_tag)
                seen.add(clean_tag.lower())
    return metadata


def _json_ld_nodes(soup: BeautifulSoup) -> list[dict]:
    nodes: list[dict] = []
    for script in soup.select("script[type='application/ld+json']"):
        text = script.string or script.get_text("", strip=True)
        if not text:
            continue
        text = text.strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        _collect_json_dicts(data, nodes)
    return nodes


def _collect_json_dicts(value, out: list[dict]) -> None:
    if isinstance(value, dict):
        out.append(value)
        graph = value.get("@graph")
        if graph is not None:
            _collect_json_dicts(graph, out)
        for key in ("mainEntity", "mainEntityOfPage", "itemListElement"):
            if key in value:
                _collect_json_dicts(value[key], out)
    elif isinstance(value, list):
        for item in value:
            _collect_json_dicts(item, out)


def _json_ld_value(nodes: list[dict], keys: tuple[str, ...]) -> str | None:
    for node in nodes:
        for key in keys:
            value = node.get(key)
            text = _stringify_value(value)
            if text:
                return text
    return None


def _json_ld_people_value(nodes: list[dict], key: str) -> str | None:
    for node in nodes:
        value = node.get(key)
        text = _person_value(value)
        if text:
            return text
    return None


def _json_ld_list_value(nodes: list[dict], key: str) -> list[str]:
    values: list[str] = []
    for node in nodes:
        value = node.get(key)
        if isinstance(value, str):
            values.extend(part.strip() for part in re.split(r"[,;]", value) if part.strip())
        elif isinstance(value, list):
            values.extend(filter(None, (_stringify_value(item) for item in value)))
    return values


def _person_value(value) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        return _first_nonempty(value.get("name"), value.get("url"))
    if isinstance(value, list):
        parts = [_person_value(item) for item in value]
        parts = [part for part in parts if part]
        return ", ".join(parts) if parts else None
    return None


def _stringify_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "headline", "text", "@id", "url"):
            text = _stringify_value(value.get(key))
            if text:
                return text
    return None


def _meta_value(soup: BeautifulSoup, *names: str) -> str | None:
    values = _meta_values(soup, *names)
    return values[0] if values else None


def _meta_values(soup: BeautifulSoup, *names: str) -> list[str]:
    wanted = {name.lower() for name in names}
    values: list[str] = []
    for tag in soup.find_all("meta"):
        key = (
            tag.get("property")
            or tag.get("name")
            or tag.get("itemprop")
            or tag.get("http-equiv")
            or ""
        ).strip().lower()
        if key not in wanted:
            continue
        content = (tag.get("content") or "").strip()
        if not content:
            continue
        if key in {"keywords", "news_keywords", "parsely-tags"}:
            values.extend(part.strip() for part in re.split(r"[,;]", content) if part.strip())
        else:
            values.append(content)
    return values


def _time_value(soup: BeautifulSoup) -> str | None:
    selectors = [
        "time[datetime]",
        "[itemprop='datePublished'][content]",
        "[itemprop='dateModified'][content]",
        "[property='article:published_time'][content]",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        value = (node.get("datetime") or node.get("content") or node.get_text(" ", strip=True)).strip()
        if value:
            return value
    return None


def _link_value(soup: BeautifulSoup, rel: str, final_url: str) -> str | None:
    def has_rel(value) -> bool:
        if not value:
            return False
        parts = value if isinstance(value, list) else str(value).split()
        return rel in [part.lower() for part in parts]

    node = soup.find("link", rel=has_rel)
    href = (node.get("href") if node else "") or ""
    return urljoin(final_url, href.strip()) if href.strip() else None


def _unique_values(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value).strip()
        key = clean.lower()
        if clean and key not in seen:
            out.append(clean)
            seen.add(key)
    return out


def _first_nonempty(*values) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
