import argparse
import asyncio
import json
import logging

from .crawler import NewsCrawlerBot
from .cdp_router import select_browser
from .config import AUTO_CDP_FIRST_RUN_WAIT_SECONDS


def parse_args():
    parser = argparse.ArgumentParser(description="Crawl one news URL with optional login and LLM extraction.")
    parser.add_argument("--url", required=True, help="News article URL")
    parser.add_argument("--username", default=None, help="Login username/account")
    parser.add_argument("--password", default=None, help="Login password")
    parser.add_argument("--job-id", default=None, help="Optional stable job id")
    parser.add_argument("--instruction-file", default=None, help="Path to instruction prompt file")
    parser.add_argument("--browser-mode", default="auto", help="Browser mode: auto|bundled|chrome|cdp")
    parser.add_argument("--cdp-url", default=None, help="CDP URL (e.g. http://127.0.0.1:9222)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    return parser.parse_args()


async def main_async():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger("news_crawler.cli")

    instruction = None
    if args.instruction_file:
        try:
            with open(args.instruction_file, "r", encoding="utf-8") as f:
                instruction = f.read()
        except Exception as e:
            logging.error(f"Failed to read instruction file: {e}")

    # Chọn browser mode tự động (hỗ trợ CDP cho Facebook, Instagram, TikTok, v.v.)
    selection = select_browser(
        url=args.url,
        instruction=instruction,
        browser_mode=args.browser_mode,
        cdp_url=args.cdp_url,
    )
    logger.info(f"Browser selection: mode={selection.browser_mode}, reason={selection.reason}")

    # Nếu vừa tạo CDP profile mới → chờ người dùng đăng nhập thủ công
    if selection.created_profile and AUTO_CDP_FIRST_RUN_WAIT_SECONDS > 0:
        logger.info(
            f"[CDP] Đã mở Chrome mới cho {args.url}. "
            f"Vui lòng ĐĂNG NHẬP trong cửa sổ Chrome đó. "
            f"Hệ thống sẽ tiếp tục sau {AUTO_CDP_FIRST_RUN_WAIT_SECONDS} giây..."
        )
        print(
            f"\n{'='*60}\n"
            f"  🔐 ĐĂNG NHẬP THỦ CÔNG\n"
            f"  Hãy đăng nhập Facebook trong cửa sổ Chrome vừa mở!\n"
            f"  Hệ thống sẽ tự tiếp tục sau {AUTO_CDP_FIRST_RUN_WAIT_SECONDS}s...\n"
            f"{'='*60}\n"
        )
        await asyncio.sleep(AUTO_CDP_FIRST_RUN_WAIT_SECONDS)

    result = await NewsCrawlerBot().crawl(
        url=args.url,
        username=args.username,
        password=args.password,
        job_id=args.job_id,
        instruction=instruction,
        browser_mode=selection.browser_mode,
        cdp_url=selection.cdp_url,
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
