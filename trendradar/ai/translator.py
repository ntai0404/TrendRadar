# coding=utf-8
"""
AI translator module

Multilingual translation of push content
Based on LiteLLM unified interface, supporting 100+ AI providers
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from trendradar.ai.client import AIClient
from trendradar.ai.prompt_loader import load_prompt_template


@dataclass
class TranslationResult:
    """Translation results"""
    translated_text: str = "" # Translated text
    original_text: str = "" # Original text
    success: bool = False # Whether it was successful or not
    error: str = "" # Error message


@dataclass
class BatchTranslationResult:
    """Batch translation results"""
    results: List[TranslationResult] = field(default_factory=list)
    success_count: int = 0
    fail_count: int = 0
    total_count: int = 0
    prompt: str = "" # debug: complete prompt sent to AI
    raw_response: str = "" # debug: AI raw response
    parsed_count: int = 0 # debug: Number of entries parsed by AI response


class AITranslator:
    """AI Translator"""

    def __init__(self, translation_config: Dict[str, Any], ai_config: Dict[str, Any]):
        """
        Initialize AI translator

        Args:
            translation_config: AI translation configuration (AI_TRANSLATION)
            ai_config: AI model configuration (LiteLLM format)
        """
        self.translation_config = translation_config
        self.ai_config = ai_config

        # Translation configuration
        self.enabled = translation_config.get("ENABLED", False)
        self.target_language = translation_config.get("LANGUAGE", "English")
        self.scope = translation_config.get("SCOPE", {"HOTLIST": True, "RSS": True, "STANDALONE": True})

        #Create AI client (based on LiteLLM)
        self.client = AIClient(ai_config)

        #Load prompt word template
        self.system_prompt, self.user_prompt_template = load_prompt_template(
            translation_config.get("PROMPT_FILE", "ai_translation_prompt.txt"),
            label="translation",
        )

    def translate(self, text: str) -> TranslationResult:
        """
        Translate a single piece of text

        Args:
            text: text to be translated

        Returns:
            TranslationResult: translation result
        """
        result = TranslationResult(original_text=text)

        if not self.enabled:
            result.error = "Translation function is not enabled"
            return result

        if not self.client.api_key:
            result.error = "AI API Key not configured"
            return result

        if not text or not text.strip():
            result.translated_text = text
            result.success = True
            return result

        try:
            # Build prompt words
            user_prompt = self.user_prompt_template
            user_prompt = user_prompt.replace("{target_language}", self.target_language)
            user_prompt = user_prompt.replace("{content}", text)

            # Call AI API
            response = self._call_ai(user_prompt)
            result.translated_text = response.strip()
            result.success = True

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            result.error = f"Translation failed ({error_type}): {error_msg}"

        return result

    def translate_batch(self, texts: List[str]) -> BatchTranslationResult:
        """
        Batch translation of text (single API call)

        Args:
            texts: list of texts to translate

        Returns:
            BatchTranslationResult: Batch translation results
        """
        batch_result = BatchTranslationResult(total_count=len(texts))

        if not self.enabled:
            for text in texts:
                batch_result.results.append(TranslationResult(
                    original_text=text,
                    error="Translation function is not enabled"
                ))
            batch_result.fail_count = len(texts)
            return batch_result

        if not self.client.api_key:
            for text in texts:
                batch_result.results.append(TranslationResult(
                    original_text=text,
                    error="AI API Key not configured"
                ))
            batch_result.fail_count = len(texts)
            return batch_result

        if not texts:
            return batch_result

        # Filter empty text
        non_empty_indices = []
        non_empty_texts = []
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_indices.append(i)
                non_empty_texts.append(text)

        #Initialize the result list
        for text in texts:
            batch_result.results.append(TranslationResult(original_text=text))

        # Empty text is directly marked as successful
        for i, text in enumerate(texts):
            if not text or not text.strip():
                batch_result.results[i].translated_text = text
                batch_result.results[i].success = True
                batch_result.success_count += 1

        if not non_empty_texts:
            return batch_result

        try:
            # Build batch translation content (using numbering format)
            batch_content = self._format_batch_content(non_empty_texts)

            # Build prompt words
            user_prompt = self.user_prompt_template
            user_prompt = user_prompt.replace("{target_language}", self.target_language)
            user_prompt = user_prompt.replace("{content}", batch_content)

            # Record debug information (including complete system + user prompt)
            if self.system_prompt:
                batch_result.prompt = f"[system]\n{self.system_prompt}\n\n[user]\n{user_prompt}"
            else:
                batch_result.prompt = user_prompt

            # Call AI API
            response = self._call_ai(user_prompt)

            # Record AI original response
            batch_result.raw_response = response

            # Parse batch translation results
            translated_texts, raw_parsed_count = self._parse_batch_response(response, len(non_empty_texts))
            batch_result.parsed_count = raw_parsed_count

            # Fill results (skip empty translations to avoid overwriting original titles with empty strings)
            for idx, translated in zip(non_empty_indices, translated_texts):
                if translated and translated.strip():
                    batch_result.results[idx].translated_text = translated
                    batch_result.results[idx].success = True
                    batch_result.success_count += 1
                else:
                    batch_result.results[idx].translated_text = batch_result.results[idx].original_text
                    batch_result.results[idx].success = True
                    batch_result.success_count += 1

        except Exception as e:
            error_msg = f"Batch translation failed: {type(e).__name__}: {str(e)[:100]}"
            for idx in non_empty_indices:
                batch_result.results[idx].error = error_msg
            batch_result.fail_count = len(non_empty_indices)

        return batch_result

    def _format_batch_content(self, texts: List[str]) -> str:
        """Format batch translation content"""
        lines = []
        for i, text in enumerate(texts, 1):
            lines.append(f"[{i}] {text}")
        return "\n".join(lines)

    def _parse_batch_response(self, response: str, expected_count: int) -> tuple:
        """
        Parse batch translation responses

        Args:
            response: AI response text
            expected_count: expected number of translations

        Returns:
            tuple: (translation result list, number of entries originally parsed by AI)
        """
        results = []
        lines = response.strip().split("\n")

        current_idx = None
        current_text = []

        for line in lines:
            # Try to match [number] format
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                bracket_end = stripped.index("]")
                try:
                    idx = int(stripped[1:bracket_end])
                    # Save previous content
                    if current_idx is not None:
                        results.append((current_idx, "\n".join(current_text).strip()))
                    current_idx = idx
                    current_text = [stripped[bracket_end + 1:].strip()]
                except ValueError:
                    if current_idx is not None:
                        current_text.append(line)
            else:
                if current_idx is not None:
                    current_text.append(line)

        # Save the last entry
        if current_idx is not None:
            results.append((current_idx, "\n".join(current_text).strip()))

        # Sort by index and extract text
        results.sort(key=lambda x: x[0])
        translated = [text for _, text in results]
        raw_parsed_count = len(translated)

        # If the number of parsed results does not match, try simply splitting by line
        if len(translated) != expected_count:
            # Fallback: Split by line (remove numbers)
            translated = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and "]" in stripped:
                    bracket_end = stripped.index("]")
                    translated.append(stripped[bracket_end + 1:].strip())
                elif stripped:
                    translated.append(stripped)
            raw_parsed_count = len(translated)

        # Make sure the correct quantity is returned
        while len(translated) < expected_count:
            translated.append("")

        return translated[:expected_count], raw_parsed_count

    def _call_ai(self, user_prompt: str) -> str:
        """Call AI API (using LiteLLM)"""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return self.client.chat(messages)
