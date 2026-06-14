# coding=utf-8
import asyncio
import yaml
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .engine import LLMScraperEngine


class LLMBotPipeline:
    """
    Pipeline adapter that loads crawler configurations, executes the LLM Engine,
    and writes the output to llm_news_crawler_bot/output/ so that TrendRadar's 
    existing CrawlerBotFetcher can seamlessly pick it up.
    """
    def __init__(self, config_path: str = "config/llm_crawler_sources.yaml", output_dir: str = "llm_news_crawler_bot/output"):
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.engine = LLMScraperEngine(headless=True)
        self.sources = self._load_sources()

    def _load_sources(self) -> List[Dict[str, Any]]:
        path = Path(self.config_path)
        if not path.exists():
            print(f"[LLMBotPipeline] Warning: Config file {self.config_path} not found.")
            return []
            
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                return data.get("sources", [])
            except Exception as e:
                print(f"[LLMBotPipeline] Error loading config: {e}")
                return []

    async def run_pipeline(self):
        """Execute crawler for enabled sources and write to output_dir."""
        for source in self.sources:
            if not source.get("enabled", False):
                continue
                
            print(f"[LLMBotPipeline] Processing source: {source.get('id')} ({source.get('url')})")
            
            try:
                data = await self.engine.scrape(
                    url=source.get("url"),
                    instruction=source.get("instruction", ""),
                    username=source.get("username", ""),
                    password=source.get("password", ""),
                    screenshots_dir=str(self.output_dir / "screenshots")
                )
                
                # Write to job directory format required by CrawlerBotFetcher
                job_id = f"job_{uuid.uuid4().hex[:8]}"
                job_dir = self.output_dir / job_id
                items_dir = job_dir / "items"
                items_dir.mkdir(parents=True, exist_ok=True)
                
                # Create one item
                item_id = f"item_{uuid.uuid4().hex[:8]}"
                item_dir = items_dir / item_id
                item_dir.mkdir(parents=True, exist_ok=True)
                
                # The format CrawlerBotFetcher parses:
                # title, final_url/source_url, summary, author, published_at
                metadata = {
                    "title": data.get("title", f"Scraped from {source.get('id')}"),
                    "source_url": data.get("source_url", source.get("url")),
                    "summary": data.get("content", ""),
                    "author": data.get("metadata", {}).get("author", source.get("id")),
                    "published_at": data.get("metadata", {}).get("date", datetime.now().isoformat()),
                    "screenshot_path": data.get("screenshot_path", "")
                }
                
                with open(item_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                # Create root metadata to mark job as complete (for CrawlerBotFetcher)
                with open(job_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump({"job_id": job_id, "status": "completed"}, f)
                    
                print(f"[LLMBotPipeline] Saved item to {item_dir}")
                
            except Exception as e:
                print(f"[LLMBotPipeline] Error processing source {source.get('id')}: {e}")

# Expose a synchronous entrypoint
def run_llm_crawler_sync():
    pipeline = LLMBotPipeline()
    asyncio.run(pipeline.run_pipeline())
