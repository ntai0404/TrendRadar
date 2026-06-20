# coding=utf-8
"""
Podcast Transcript Source

Chuyển audio podcast thành text bằng Groq Whisper (miễn phí).
Hỗ trợ: Xiaoyuzhou FM, bất kỳ podcast URL nào có file audio.
Yêu cầu: Groq API key (free tại https://console.groq.com)

Capabilities: Audio transcription → full text
"""

import json
import subprocess
import shutil
import os
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class PodcastSource(ExternalSource):
    """Podcast transcription source via Groq Whisper"""

    @property
    def source_id(self) -> str:
        return "podcast"

    @property
    def source_name(self) -> str:
        return "Podcast Transcript"

    def is_available(self) -> bool:
        """Kiểm tra Groq API key có sẵn không"""
        return bool(self._get_groq_key())

    def _get_groq_key(self) -> str:
        """Lấy Groq API key"""
        key = os.environ.get("GROQ_API_KEY", "")
        if key:
            return key

        # Từ agent-reach config
        config_path = os.path.expanduser("~/.agent-reach/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("groq_key", "")
            except Exception:
                pass

        return ""

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Transcribe podcast episodes.

        Config keys:
            episodes: List[Dict] - Danh sách episode cần transcribe
                Mỗi dict: {"url": "...", "title": "...(optional)"}
            groq_key: str - Groq API key (override env)
            max_episodes: int - Số episode tối đa (default: 3)
        """
        groq_key = config.get("groq_key", "") or self._get_groq_key()
        if not groq_key:
            return self._make_result(
                error="Chưa có Groq API key. Đăng ký miễn phí: https://console.groq.com → Set env GROQ_API_KEY"
            )

        episodes = config.get("episodes", [])
        max_episodes = config.get("max_episodes", 3)

        if not episodes:
            return self._make_result(error="Chưa cấu hình episodes cho Podcast")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        for episode in episodes[:max_episodes]:
            url = episode.get("url", "") if isinstance(episode, dict) else str(episode)
            title = episode.get("title", "") if isinstance(episode, dict) else ""

            if not url:
                continue

            try:
                transcript = self._transcribe(url, groq_key)
                if transcript:
                    # Lấy title từ transcript nếu chưa có
                    if not title:
                        title = transcript[:80] + "..."

                    all_items.append(SourceItem(
                        title=f"🎙️ {title}",
                        url=url,
                        source_id=self.source_id,
                        source_name=self.source_name,
                        content=transcript,
                        summary=transcript[:500],
                        metadata={
                            "type": "transcript",
                            "word_count": len(transcript.split()),
                        },
                    ))
            except Exception as e:
                errors.append(f"Episode '{url[:50]}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _transcribe(self, url: str, groq_key: str) -> str:
        """
        Transcribe audio from URL using Groq Whisper API.
        Simplified: downloads audio then sends to Groq.
        """
        # Kiểm tra script transcribe.sh của agent-reach
        script_path = os.path.expanduser("~/.agent-reach/tools/xiaoyuzhou/transcribe.sh")
        if os.path.exists(script_path) and "xiaoyuzhoufm.com" in url:
            result = subprocess.run(
                ["bash", script_path, url],
                capture_output=True,
                text=True,
                timeout=300,  # 5 phút
                encoding="utf-8",
                env={**os.environ, "GROQ_API_KEY": groq_key},
            )
            if result.returncode == 0:
                return result.stdout.strip()
            raise RuntimeError(result.stderr.strip()[:200])

        # Generic: dùng yt-dlp để extract audio, rồi gọi Groq
        if not shutil.which("yt-dlp"):
            raise RuntimeError("Cần yt-dlp để download audio. Chạy: pip install yt-dlp")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.mp3")

            # Download audio
            cmd = [
                "yt-dlp", "-x", "--audio-format", "mp3",
                "-o", audio_path,
                "--no-warnings",
                url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"Download failed: {result.stderr[:100]}")

            # Gọi Groq Whisper API
            import requests
            with open(audio_path, "rb") as f:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": ("audio.mp3", f, "audio/mpeg")},
                    data={"model": "whisper-large-v3", "language": "vi"},
                    timeout=180,
                )
            resp.raise_for_status()
            return resp.json().get("text", "")
