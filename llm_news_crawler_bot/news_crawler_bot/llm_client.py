import json
import logging
import re
from typing import Any, Optional, Type

import httpx
from pydantic import BaseModel

from .config import ROUTER_API_KEY, ROUTER_BASE_URL, ROUTER_MODEL

logger = logging.getLogger("news_crawler.llm")


def _extract_json(text: str) -> Any:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            text = fence.group(1).strip()

    start = min([i for i in [text.find("{"), text.find("[")] if i >= 0], default=-1)
    end = max(text.rfind("}"), text.rfind("]"))
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"LLM response did not contain valid JSON: {text[:300]}")


async def ask_json(
    prompt: str,
    schema: Type[BaseModel],
    system: Optional[str] = None,
    temperature: float = 0.1,
) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    schema_text = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    messages.append(
        {
            "role": "user",
            "content": (
                f"{prompt}\n\nReturn ONLY one valid JSON object matching this schema:\n"
                f"{schema_text}"
            ),
        }
    )

    payload = {
        "model": ROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {ROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    url = ROUTER_BASE_URL.rstrip("/") + "/chat/completions"

    logger.info("Calling LLM model=%s url=%s", ROUTER_MODEL, url)
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            chunks: list[str] = []
            async for raw_line in response.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for choice in event.get("choices", []):
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        if content:
                            chunks.append(content)
                else:
                    chunks.append(line)

    content = "".join(chunks).strip()
    return _extract_json(content)
