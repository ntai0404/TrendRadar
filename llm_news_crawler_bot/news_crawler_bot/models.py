from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class CrawlRequest(BaseModel):
    url: HttpUrl
    username: Optional[str] = None
    password: Optional[str] = None
    instruction: Optional[str] = Field(
        None,
        description="Detailed user instruction for login, navigation, or extraction behavior.",
    )
    browser_mode: Literal["auto", "bundled", "chrome", "cdp"] = Field(
        "auto",
        description="Browser mode: auto CDP profile selection, bundled Playwright Chromium, installed Chrome, or visible Chrome via CDP.",
    )
    cdp_url: Optional[str] = Field(
        None,
        description="Chrome DevTools Protocol URL, for example http://127.0.0.1:9222.",
    )
    headless: Optional[bool] = Field(
        None,
        description="Override headless mode for bundled/chrome modes.",
    )


class LoginPlan(BaseModel):
    requires_login: bool = Field(False)
    login_url: Optional[str] = None
    pre_click_selector: Optional[str] = None
    username_selector: Optional[str] = None
    password_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    success_indicator_selector: Optional[str] = None
    reasoning: str = ""


class CrawlPlan(BaseModel):
    needs_search: bool = Field(
        False,
        description="Whether the bot should search before extracting.",
    )
    navigation_url: Optional[str] = Field(
        None,
        description="Direct URL to navigate to before extraction/search when the user mentions a specific page, group, profile, article, or listing URL.",
    )
    search_query: Optional[str] = Field(
        None,
        description="Exact search query to use if needs_search is true.",
    )
    target_count: int = Field(
        1,
        ge=1,
        le=20,
        description="Number of independent target items to collect and extract.",
    )
    target_type: str = Field(
        "web_page",
        description="Target type such as video, song, post, article, profile, product, image, or web_page.",
    )
    open_each_result: bool = Field(
        True,
        description="Whether to open each search result/detail page before extraction.",
    )
    platform_hint: Optional[str] = Field(
        None,
        description="Optional platform inferred from URL/instruction, e.g. youtube, facebook, instagram, generic.",
    )
    search_box_selector: Optional[str] = Field(
        None,
        description="CSS selector for the search box on the current page if visible in HTML.",
    )
    result_link_selector: Optional[str] = Field(
        None,
        description="CSS selector for result/item links to collect after search when inferable.",
    )
    reasoning: str = Field(
        "",
        description="Short explanation of the interpreted user intent.",
    )


class TargetSelectionPlan(BaseModel):
    target_urls: List[str] = Field(
        default_factory=list,
        description="Specific target URLs found in the observed HTML, in the order they should be extracted.",
    )
    result_link_selector: Optional[str] = Field(
        None,
        description="CSS selector that matches target result links in the observed HTML.",
    )
    should_open_each: bool = Field(
        True,
        description="Whether each target should be opened before extraction.",
    )
    reasoning: str = Field(
        "",
        description="Short explanation of how targets were selected from the observed HTML.",
    )


class NavigationChoice(BaseModel):
    navigation_url: Optional[str] = Field(
        None,
        description="Best category, listing, topic, or search-results URL to open before selecting target items.",
    )
    reasoning: str = Field(
        "",
        description="Short explanation of why this navigation URL was selected.",
    )


class CollectionGoal(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Clean topic/search query for this independent collection goal.",
    )
    target_count: int = Field(
        1,
        ge=1,
        le=20,
        description="Number of independent items requested for this goal.",
    )
    target_type: str = Field(
        "article",
        description="Target type for this goal, such as article, post, video, profile, or product.",
    )
    navigation_url: Optional[str] = Field(
        None,
        description="Specific URL to open for this goal when the user named a page/group/category/listing.",
    )
    platform_hint: Optional[str] = Field(
        None,
        description="Platform/source hint for this goal.",
    )
    instruction: str = Field(
        "",
        description="Short standalone instruction preserving the user's intent for this goal.",
    )


class CollectionGoalPlan(BaseModel):
    goals: List[CollectionGoal] = Field(default_factory=list)
    reasoning: str = Field(
        "",
        description="Short explanation of whether the command was split into independent collection goals.",
    )


class ArticleMetadata(BaseModel):
    source_url: str
    final_url: str
    title: str
    author: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[str] = None
    summary: str
    tags: List[str] = Field(default_factory=list)
    content: str
    language: Optional[str] = None
    screenshot_path: str


class CrawlItem(BaseModel):
    item_index: int
    output_dir: str
    metadata_path: str
    screenshot_path: str
    article_path: str
    html_path: str
    metadata: ArticleMetadata


class CrawlResult(BaseModel):
    job_id: str
    status: str
    output_dir: str
    metadata_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    article_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[ArticleMetadata] = None
    items: List[CrawlItem] = Field(default_factory=list)
