# coding=utf-8
import json
import os
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from trendradar.storage.base import RSSItem, RSSData


class CrawlerBotFetcher:
    """
    Trình thu thập dữ liệu từ thư mục output của LLM News Crawler Bot.
    Giả lập dữ liệu Crawler thành định dạng RSSData để TrendRadar dễ dàng xử lý.
    """

    def __init__(self, output_dir: str, mark_as_processed: bool = True):
        self.output_dir = Path(output_dir)
        self.mark_as_processed = mark_as_processed

    def fetch_all(self, timezone: str, crawl_time: str, crawl_date: str) -> RSSData:
        """
        Quét thư mục output_dir và trả về RSSData
        """
        items_by_feed: Dict[str, List[RSSItem]] = {}
        id_to_name: Dict[str, str] = {}
        
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            print(f"[CrawlerBot] Thư mục output không tồn tại: {self.output_dir}")
            return RSSData(date=crawl_date, crawl_time=crawl_time, items={})

        processed_count = 0

        # Lặp qua các thư mục job
        for job_dir in self.output_dir.iterdir():
            if not job_dir.is_dir():
                continue
            
            # File metadata ở root của job (manifest tổng)
            root_metadata_path = job_dir / "metadata.json"
            processed_marker = job_dir / "metadata.processed.json"

            if processed_marker.exists() and not root_metadata_path.exists():
                # Đã được xử lý trong lần chạy trước
                continue
                
            if not root_metadata_path.exists():
                # Job chưa hoàn thành hoặc bị lỗi
                continue

            try:
                # Tìm các items
                items_dir = job_dir / "items"
                if items_dir.exists() and items_dir.is_dir():
                    for item_dir in items_dir.iterdir():
                        if not item_dir.is_dir():
                            continue
                            
                        item_metadata_path = item_dir / "metadata.json"
                        if item_metadata_path.exists():
                            rss_item = self._parse_item(item_metadata_path, crawl_time)
                            if rss_item:
                                feed_id = rss_item.feed_id
                                if feed_id not in items_by_feed:
                                    items_by_feed[feed_id] = []
                                    id_to_name[feed_id] = rss_item.feed_name
                                items_by_feed[feed_id].append(rss_item)
                                processed_count += 1
                                
                # Đánh dấu đã xử lý
                if self.mark_as_processed:
                    try:
                        root_metadata_path.rename(processed_marker)
                    except Exception as e:
                        print(f"[CrawlerBot] Không thể đổi tên file đánh dấu đã xử lý {root_metadata_path}: {e}")

            except Exception as e:
                print(f"[CrawlerBot] Lỗi khi xử lý job {job_dir.name}: {e}")

        if processed_count > 0:
            print(f"[CrawlerBot] Đã đọc thành công {processed_count} bài viết từ bot cào dữ liệu.")

        return RSSData(
            date=crawl_date,
            crawl_time=crawl_time,
            items=items_by_feed,
            id_to_name=id_to_name,
            failed_ids=[]
        )

    def _parse_item(self, metadata_path: Path, crawl_time: str) -> RSSItem:
        """
        Đọc ArticleMetadata và chuyển sang RSSItem
        """
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", "")
        url = data.get("final_url") or data.get("source_url", "")
        summary = data.get("summary", "")
        author = data.get("author", "")
        published_at = data.get("published_at", "")
        
        if not title or not url:
            return None

        # Trích xuất domain làm feed_id
        try:
            parsed_uri = urlparse(url)
            domain = parsed_uri.netloc.replace("www.", "")
            if not domain:
                domain = "crawler_bot"
        except:
            domain = "crawler_bot"

        feed_id = domain
        feed_name = f"[Crawler] {domain}"

        return RSSItem(
            title=title,
            feed_id=feed_id,
            feed_name=feed_name,
            url=url,
            guid=url,
            published_at=published_at,
            summary=summary,
            author=author,
            crawl_time=crawl_time,
            first_time=crawl_time,
            last_time=crawl_time,
            count=1
        )
