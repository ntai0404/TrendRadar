import argparse
import asyncio
import json
import logging

from .crawler import NewsCrawlerBot


def parse_args():
    parser = argparse.ArgumentParser(description="Crawl one news URL with optional login and LLM extraction.")
    parser.add_argument("--url", required=True, help="News article URL")
    parser.add_argument("--username", default=None, help="Login username/account")
    parser.add_argument("--password", default=None, help="Login password")
    parser.add_argument("--job-id", default=None, help="Optional stable job id")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    return parser.parse_args()


async def main_async():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    result = await NewsCrawlerBot().crawl(
        url=args.url,
        username=args.username,
        password=args.password,
        job_id=args.job_id,
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
