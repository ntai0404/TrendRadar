# coding=utf-8
import asyncio
import json
import base64
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from playwright.async_api import async_playwright
except ImportError:
    # Handle if playwright is not installed
    pass

from trendradar.ai.client import AIClient
from trendradar.config import load_config


class LLMScraperEngine:
    """
    Lightweight LLM-driven browser scraper using Playwright and AIClient.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        config = load_config()
        self.ai_client = AIClient(config.get("ai", {}))

    async def _scrape_youtube(self, url: str) -> str:
        """Sử dụng yt-dlp để lấy thông tin và mô tả/phụ đề của video YouTube."""
        print(f"[LLMScraper] Gọi yt-dlp cho {url}")
        try:
            # Lấy metadata
            result = subprocess.run(["yt-dlp", "--dump-json", url], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                title = data.get("title", "")
                desc = data.get("description", "")
                return f"YouTube Video: {title}\nDescription: {desc}"
        except Exception as e:
            print(f"[LLMScraper] Lỗi yt-dlp: {e}")
        return ""

    async def _scrape_bilibili(self, url: str) -> str:
        """Sử dụng bili-cli để lấy thông tin Bilibili."""
        print(f"[LLMScraper] Gọi bili-cli cho {url}")
        try:
            # Trích xuất bvid từ URL, ví dụ: https://www.bilibili.com/video/BV1xx411c7mD
            # Gọi bili-cli (cần parse output tuỳ thuộc vào công cụ)
            # Ở đây giả lập gọi lệnh lấy thông tin cơ bản:
            result = subprocess.run(["bili", "info", url], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"Bilibili Info:\n{result.stdout}"
        except Exception as e:
            print(f"[LLMScraper] Lỗi bili-cli: {e}")
        return ""

    async def _scrape_twitter(self, url: str) -> str:
        """Sử dụng twitter-cli hoặc opencli cho Twitter."""
        print(f"[LLMScraper] Gọi twitter-cli cho {url}")
        try:
            result = subprocess.run(["twitter", "tweet", url], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"Twitter Post:\n{result.stdout}"
            else:
                # Fallback to opencli
                result_open = subprocess.run(["opencli", "twitter", "tweet", url], capture_output=True, text=True, timeout=60)
                if result_open.returncode == 0:
                    return f"Twitter Post (OpenCLI):\n{result_open.stdout}"
        except Exception as e:
            print(f"[LLMScraper] Lỗi twitter-cli: {e}")
        return ""

    async def scrape(self, url: str, instruction: str, username: str = "", password: str = "", screenshots_dir: str = "output/screenshots") -> Dict[str, Any]:
        """
        Navigate to URL (via CLI tools if supported, else Playwright), extract DOM/Text, and ask LLM to extract data.
        """
        Path(screenshots_dir).mkdir(parents=True, exist_ok=True)
        screenshot_path = ""
        page_text = ""

        # --- 1. Routing theo Agent-Reach Philosophy ---
        if "youtube.com" in url or "youtu.be" in url:
            page_text = await self._scrape_youtube(url)
        elif "bilibili.com" in url:
            page_text = await self._scrape_bilibili(url)
        elif "twitter.com" in url or "x.com" in url:
            page_text = await self._scrape_twitter(url)

        # --- 2. Fallback về Playwright nếu CLI trả về rỗng hoặc nền tảng không có CLI ---
        if not page_text:
            print(f"[LLMScraper] Fallback to Playwright for {url}...")
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=self.headless)
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()

                    # Steath JS to bypass basic bot detections
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    """)

                    print(f"[LLMScraper] Navigating to {url}...")
                    await page.goto(url, wait_until="networkidle", timeout=60000)

                    # Basic heuristic login if credentials are provided
                    if username and password:
                        print("[LLMScraper] Attempting heuristic login...")
                        # Facebook heuristic
                        if "facebook.com" in url:
                            try:
                                await page.fill('input[name="email"]', username, timeout=5000)
                                await page.fill('input[name="pass"]', password, timeout=5000)
                                await page.click('button[name="login"]')
                                await page.wait_for_load_state("networkidle", timeout=15000)
                            except Exception as e:
                                print(f"[LLMScraper] FB login failed: {e}")

                    # Scroll to load dynamic content
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)

                    # Capture screenshot
                    filename = f"screenshot_{asyncio.get_event_loop().time()}.png".replace(".", "_") + ".png"
                    screenshot_path = str(Path(screenshots_dir) / filename)
                    await page.screenshot(path=screenshot_path, full_page=True)
                    
                    # Get cleaned text content
                    # Instead of full HTML (which is huge), get visible text
                    page_text = await page.evaluate("document.body.innerText")
                    
                    await browser.close()
            except Exception as e:
                print(f"[LLMScraper] Exception during Playwright scrape: {e}")
                
        # Call LLM to extract data from whatever text we gathered
        if not page_text:
            return {"error": "Could not retrieve content via CLI or Playwright."}
            
        return await self._extract_with_llm(page_text, instruction, screenshot_path, url)

    async def _extract_with_llm(self, text_content: str, instruction: str, screenshot_path: str, url: str) -> Dict[str, Any]:
        """
        Ask the LLM to analyze the page text and extract required structured data.
        """
        prompt = f"""
Bạn là một AI phân tích dữ liệu web chuyên nghiệp.
Trang web nguồn: {url}

Yêu cầu/Chỉ thị từ người dùng:
{instruction}

Dưới đây là nội dung văn bản bóc tách được từ trang web:
=========================================
{text_content[:20000]}  # Giới hạn 20000 ký tự để tránh vượt token limit
=========================================

Dựa vào chỉ thị và nội dung trên, hãy trích xuất thông tin thành định dạng JSON với cấu trúc sau:
{{
    "title": "Tiêu đề bài viết / video / nội dung chính",
    "content": "Nội dung tóm tắt hoặc nội dung chi tiết theo yêu cầu",
    "metadata": {{
        "author": "Tên tác giả/kênh nếu có",
        "date": "Ngày đăng nếu có",
        "tags": ["tag1", "tag2"]
    }}
}}

CHỈ trả về một chuỗi JSON hợp lệ, KHÔNG bọc trong markdown ```json, KHÔNG kèm giải thích thêm.
"""
        try:
            print("[LLMScraper] Sending extracted text to LLM for processing...")
            response = self.ai_client.chat([
                {"role": "system", "content": "You are a web data extractor. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Clean JSON response
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            # Gắn thêm đường dẫn ảnh
            data["screenshot_path"] = screenshot_path
            data["source_url"] = url
            return data
            
        except Exception as e:
            print(f"[LLMScraper] LLM extraction failed: {e}")
            return {
                "title": "LLM Extraction Failed",
                "content": text_content[:500],
                "metadata": {},
                "screenshot_path": screenshot_path,
                "source_url": url,
                "error": str(e)
            }
