import asyncio
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import AUTO_CDP_FIRST_RUN_WAIT_SECONDS, OUTPUT_DIR
from .crawler import NewsCrawlerBot
from .cdp_router import select_browser
from .agent import plan_crawl
from .models import CrawlRequest, CrawlResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news_crawler.api")

if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="LLM News Crawler Bot")
bot = NewsCrawlerBot()
BASE_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = BASE_DIR / "web"

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/assets", StaticFiles(directory=str(WEB_DIR)), name="assets")

JOBS: dict[str, dict] = {}


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _append_log(job_id: str, message: str) -> None:
    if job_id in JOBS:
        JOBS[job_id].setdefault("logs", []).append(f"[{_now()}] {message}")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return index_path.read_text(encoding="utf-8")


@app.post("/api/crawl", response_model=CrawlResult)
async def crawl(request: CrawlRequest):
    browser = select_browser(str(request.url), request.instruction, request.browser_mode, request.cdp_url)
    return await bot.crawl(
        url=str(request.url),
        username=request.username,
        password=request.password,
        instruction=request.instruction,
        browser_mode=browser.browser_mode,
        cdp_url=browser.cdp_url,
        headless=request.headless,
    )


@app.post("/api/jobs")
async def start_job(request: CrawlRequest):
    import uuid

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",
        "request": request.model_dump(mode="json"),
        "logs": [f"[{_now()}] Job created."],
        "result": None,
        "error": None,
    }

    async def runner():
        try:
            browser = select_browser(str(request.url), request.instruction, request.browser_mode, request.cdp_url)
            _append_log(
                job_id,
                f"Browser selection: mode={browser.browser_mode}, cdp={browser.cdp_url or '-'} ({browser.reason}).",
            )
            if browser.created_profile:
                _append_log(
                    job_id,
                    "A new visible Chrome CDP profile was created. If this site needs login, log in once in that Chrome window; the session will be reused later.",
                )
                if AUTO_CDP_FIRST_RUN_WAIT_SECONDS > 0:
                    _append_log(
                        job_id,
                        f"Waiting {AUTO_CDP_FIRST_RUN_WAIT_SECONDS}s for first-time manual login before crawling.",
                    )
                    await asyncio.sleep(AUTO_CDP_FIRST_RUN_WAIT_SECONDS)
            result = await bot.crawl(
                url=str(request.url),
                username=request.username,
                password=request.password,
                instruction=request.instruction,
                browser_mode=browser.browser_mode,
                cdp_url=browser.cdp_url,
                headless=request.headless,
                job_id=job_id,
                log_callback=lambda msg: _append_log(job_id, msg),
            )
            JOBS[job_id]["result"] = result.model_dump(mode="json")
            JOBS[job_id]["status"] = result.status
            if result.error:
                JOBS[job_id]["error"] = result.error
            _append_log(job_id, f"Job finished with status: {result.status}")
        except asyncio.CancelledError:
            JOBS[job_id]["status"] = "stopped"
            JOBS[job_id]["error"] = "Stopped by user."
            _append_log(job_id, "Job stopped by user.")
        except Exception as exc:
            JOBS[job_id]["status"] = "failed"
            error_text = str(exc) or repr(exc)
            JOBS[job_id]["error"] = error_text
            logger.error("Unhandled job error\n%s", traceback.format_exc())
            _append_log(job_id, f"Unhandled error: {error_text}")

    task = asyncio.create_task(runner())
    JOBS[job_id]["task"] = task
    return {"job_id": job_id, "status": "running"}


@app.post("/api/plan")
async def preview_plan(request: CrawlRequest):
    plan = await plan_crawl(str(request.url), request.instruction)
    return plan.model_dump(mode="json")


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id in JOBS:
        job = JOBS[job_id]
        response = {
            "job_id": job_id,
            "status": job.get("status"),
            "logs": job.get("logs", []),
            "error": job.get("error"),
            "result": job.get("result"),
        }
        if job.get("result"):
            response.update(job["result"])
        return response

    job_dir = OUTPUT_DIR / job_id
    metadata_path = job_dir / "metadata.json"
    screenshot_path = job_dir / "screenshot.png"
    article_path = job_dir / "article.txt"

    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    metadata = None
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    return {
        "job_id": job_id,
        "status": "completed" if metadata else "failed_or_incomplete",
        "output_dir": str(job_dir),
        "metadata_path": str(metadata_path) if metadata_path.exists() else None,
        "screenshot_path": str(screenshot_path) if screenshot_path.exists() else None,
        "article_path": str(article_path) if article_path.exists() else None,
        "screenshot_url": f"/output/{job_id}/screenshot.png" if screenshot_path.exists() else None,
        "metadata": metadata,
    }


@app.post("/api/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    task = job.get("task")
    if job.get("status") not in {"running", "starting"}:
        return {"job_id": job_id, "status": job.get("status")}
    job["status"] = "stopping"
    _append_log(job_id, "Stop requested by user.")
    if task:
        task.cancel()
    return {"job_id": job_id, "status": "stopping"}
