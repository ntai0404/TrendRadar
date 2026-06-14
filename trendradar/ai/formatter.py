# coding=utf-8
"""
AI analysis result formatting module

Format AI analysis results into the style of each push channel
"""

import html as html_lib
import re
from .analyzer import AIAnalysisResult


def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS attacks"""
    return html_lib.escape(text) if text else ""


def _format_list_content(text: str) -> str:
    """
    Format the list content to ensure there is a line break before the serial number
    For example, convert "1. xxx 2. yyy" to:
    1. xxx
    2. yyy
    """
    if not text:
        return ""
    
    # Remove the leading and trailing blanks to prevent the content returned by AI from having a line break at the beginning, causing blank lines to be displayed.
    text = text.strip()

    # 0. Merge the serial number and the following [label] (defensive processing)
    # Merge "1.\n[Investor]:" or "1.[Investor]:" into "1.Investor:"
    text = re.sub(r'(\d+\.)\s*【([^】]+)】([:：]?)', r'\1 \2：', text)

    # 1. Normalization: Make sure there is a space after "1."
    result = re.sub(r'(\d+)\.([^ \d])', r'\1. \2', text)

    # 2. Force newline: match "number.", and it is not preceded by a newline character
    # (?!\d) Exclude version numbers/decimals (such as 2.0, 3.5) to avoid misjudgment as list serial numbers
    result = re.sub(r'(?<=[^\n])\s+(\d+\.)(?!\d)', r'\n\1', result)
    
    # 3. Handle the situation "1.**Bold**" (although Prompt requires not to output Markdown, but it is handled defensively)
    result = re.sub(r'(?<=[^\n])(\d+\.\*\*)', r'\n\1', result)

    # 4. Process line breaks after Chinese punctuation (excluding version numbers/decimals)
    result = re.sub(r'([：:;,。；，])\s*(\d+\.)(?!\d)', r'\1\n\2', result)

    # 5. Process subtitles such as "XX aspect:", "XX field:" and other line breaks
    # Only trigger line breaks after Chinese punctuation (period, comma, semicolon, etc.) to avoid damaging the "1. XX field:" format
    result = re.sub(r'([.!?;,,])\s*([a-zA-Z0-9\u4e00-\u9fa5]+(aspect|field)[::])', r'\1\n\2', result)

    # 6. Processing [label] format
    # 6a. Make sure there is a blank line before the label (except at the beginning of the text)
    result = re.sub(r'(?<=\S)\n*(【[^】]+】)', r'\n\n\1', result)
    # 6b. Merge tags and colons separated by newlines: [tag]\n: → [tag]:
    result = re.sub(r'(【[^】]+】)\n+([:：])', r'\1\2', result)
    # 6c. After the label (including optional colon), if it is followed by non-blank and non-colon content, start a new line
    # Use (?=[^\s::]) to avoid regular backtracking from misjudging the colon as "content" and splitting it [tag]:
    result = re.sub(r'(【[^】]+】[:：]?)[ \t]*(?=[^\s:：])', r'\1\n', result)

    # 7. Add visual blank lines between list items (excluding version numbers/decimals)
    # Exclude the situation after the [label] line (ending with ]) and the subtitle line (ending with colon) to avoid empty lines between the title and the first item
    result = re.sub(r'(?<![:：】])\n(\d+\.)(?!\d)', r'\n\n\1', result)

    return result


def _format_standalone_summaries(summaries: dict) -> str:
    """The formatted independent display area is summarized as a line of plain text, with each source name on a separate line"""
    if not summaries:
        return ""
    lines = []
    for source_name, summary in summaries.items():
        if summary:
            lines.append(f"[{source_name}]:\n{summary}")
    return "\n\n".join(lines)


def render_ai_analysis_markdown(result: AIAnalysisResult) -> str:
    """Rendered to universal Markdown format (Telegram, WeChat Enterprise, ntfy, Bark, Slack)"""
    if not result.success:
        if result.skipped:
            return f"ℹ️ {result.error}"
        return f"⚠️ AI phân tích thất bại: {result.error}"

    lines = ["**✨ AI Phân tích điểm nóng**", ""]

    if result.core_trends:
        lines.extend(["**Xu hướng điểm nóng cốt lõi**", _format_list_content(result.core_trends), ""])

    if result.sentiment_controversy:
        lines.extend(
            ["**Tranh cãi và định hướng dư luận**", _format_list_content(result.sentiment_controversy), ""]
        )

    if result.signals:
        lines.extend(["**Tín hiệu yếu và biến động**", _format_list_content(result.signals), ""])

    if result.rss_insights:
        lines.extend(
            ["**Góc nhìn sâu từ RSS**", _format_list_content(result.rss_insights), ""]
        )

    if result.outlook_strategy:
        lines.extend(
            ["**Đề xuất chiến lược**", _format_list_content(result.outlook_strategy), ""]
        )

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            lines.extend(["**Điểm tin nguồn độc lập**", summaries_text])

    return "\n".join(lines)


def render_ai_analysis_feishu(result: AIAnalysisResult) -> str:
    """Rendered into Feishu Card Markdown format"""
    if not result.success:
        if result.skipped:
            return f"ℹ️ {result.error}"
        return f"⚠️ AI phân tích thất bại: {result.error}"

    lines = ["**✨ AI Phân tích điểm nóng**", ""]

    if result.core_trends:
        lines.extend(["**Xu hướng điểm nóng cốt lõi**", _format_list_content(result.core_trends), ""])

    if result.sentiment_controversy:
        lines.extend(
            ["**Tranh cãi và định hướng dư luận**", _format_list_content(result.sentiment_controversy), ""]
        )

    if result.signals:
        lines.extend(["**Tín hiệu yếu và biến động**", _format_list_content(result.signals), ""])

    if result.rss_insights:
        lines.extend(
            ["**Góc nhìn sâu từ RSS**", _format_list_content(result.rss_insights), ""]
        )

    if result.outlook_strategy:
        lines.extend(
            ["**Đề xuất chiến lược**", _format_list_content(result.outlook_strategy), ""]
        )

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            lines.extend(["**Điểm tin nguồn độc lập**", summaries_text])

    return "\n".join(lines)


def render_ai_analysis_dingtalk(result: AIAnalysisResult) -> str:
    """Rendered in DingTalk Markdown format"""
    if not result.success:
        if result.skipped:
            return f"ℹ️ {result.error}"
        return f"⚠️ AI phân tích thất bại: {result.error}"

    lines = ["### ✨ AI Phân tích điểm nóng", ""]

    if result.core_trends:
        lines.extend(
            ["#### Xu hướng điểm nóng cốt lõi", _format_list_content(result.core_trends), ""]
        )

    if result.sentiment_controversy:
        lines.extend(
            [
                "#### Tranh cãi và định hướng dư luận",
                _format_list_content(result.sentiment_controversy),
                "",
            ]
        )

    if result.signals:
        lines.extend(["#### Tín hiệu yếu và biến động", _format_list_content(result.signals), ""])

    if result.rss_insights:
        lines.extend(
            ["#### Góc nhìn sâu từ RSS", _format_list_content(result.rss_insights), ""]
        )

    if result.outlook_strategy:
        lines.extend(
            ["#### Đề xuất chiến lược", _format_list_content(result.outlook_strategy), ""]
        )

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            lines.extend(["#### Điểm tin nguồn độc lập", summaries_text])

    return "\n".join(lines)


def render_ai_analysis_plain(result: AIAnalysisResult) -> str:
    """Rendered as plain text"""
    if not result.success:
        if result.skipped:
            return result.error
        return f"AI phân tích thất bại: {result.error}"

    lines = ["【✨ AI Phân tích điểm nóng】", ""]

    if result.core_trends:
        lines.extend(["[Xu hướng điểm nóng cốt lõi]", _format_list_content(result.core_trends), ""])

    if result.sentiment_controversy:
        lines.extend(
            ["[Tranh cãi và định hướng dư luận]", _format_list_content(result.sentiment_controversy), ""]
        )

    if result.signals:
        lines.extend(["[Tín hiệu yếu và biến động]", _format_list_content(result.signals), ""])

    if result.rss_insights:
        lines.extend(["[Góc nhìn sâu từ RSS]", _format_list_content(result.rss_insights), ""])

    if result.outlook_strategy:
        lines.extend(["[Đề xuất chiến lược]", _format_list_content(result.outlook_strategy), ""])

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            lines.extend(["[Điểm tin nguồn độc lập]", summaries_text])

    return "\n".join(lines)


def render_ai_analysis_telegram(result: AIAnalysisResult) -> str:
    """Rendered to Telegram HTML format (with parse_mode: HTML)

    The HTML mode of the Telegram Bot API only supports limited tags:
    <b>, <i>, <u>, <s>, <code>, <pre>, <a href="">, <blockquote>
    Use \\n directly for line breaks. Tags such as <br>, <div>, <h1>-<h6> are not supported.
    """
    if not result.success:
        if result.skipped:
            return f"ℹ️ {_escape_html(result.error)}"
        return f"⚠️ AI phân tích thất bại: {_escape_html(result.error)}"

    lines = ["<b>✨ AI Phân tích điểm nóng</b>", ""]

    if result.core_trends:
        lines.extend(["<b>Xu hướng điểm nóng cốt lõi</b>", _escape_html(_format_list_content(result.core_trends)), ""])

    if result.sentiment_controversy:
        lines.extend(["<b>Tranh cãi và định hướng dư luận</b>", _escape_html(_format_list_content(result.sentiment_controversy)), ""])

    if result.signals:
        lines.extend(["<b>Tín hiệu yếu và biến động</b>", _escape_html(_format_list_content(result.signals)), ""])

    if result.rss_insights:
        lines.extend(["<b>Góc nhìn sâu từ RSS</b>", _escape_html(_format_list_content(result.rss_insights)), ""])

    if result.outlook_strategy:
        lines.extend(["<b>Đề xuất chiến lược</b>", _escape_html(_format_list_content(result.outlook_strategy)), ""])

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            lines.extend(["<b>Điểm tin nguồn độc lập</b>", _escape_html(summaries_text)])

    return "\n".join(lines)


def get_ai_analysis_renderer(channel: str):
    """Get the corresponding rendering function according to the channel"""
    renderers = {
        "feishu": render_ai_analysis_feishu,
        "dingtalk": render_ai_analysis_dingtalk,
        "wework": render_ai_analysis_markdown,
        "telegram": render_ai_analysis_telegram,
        "email": render_ai_analysis_html_rich, # The email uses rich styles and matches the CSS of the HTML report
        "ntfy": render_ai_analysis_markdown,
        "bark": render_ai_analysis_plain,
        "slack": render_ai_analysis_markdown,
    }
    return renderers.get(channel, render_ai_analysis_markdown)


def render_ai_analysis_html_rich(result: AIAnalysisResult) -> str:
    """Render to richly styled HTML format (for HTML reporting)"""
    if not result:
        return ""

    # Check if successful
    if not result.success:
        if result.skipped:
            return f"""
                <div class="ai-section">
                    <div class="ai-info">ℹ️ {_escape_html(str(result.error))}</div>
                </div>"""
        error_msg = result.error or "Unknown error"
        return f"""
                <div class="ai-section">
                    <div class="ai-warning">AI phân tích thất bại: {_escape_html(str(error_msg))}</div>
                </div>"""

    ai_html = """
                <div class="ai-section">
                    <div class="ai-section-header">
                        <div class="ai-section-title">✨ AI Phân tích điểm nóng</div>
                        <span class="ai-section-badge">AI</span>
                    </div>
                    <div class="ai-blocks-grid">"""

    if result.core_trends:
        content = _format_list_content(result.core_trends)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Xu hướng điểm nóng cốt lõi</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.sentiment_controversy:
        content = _format_list_content(result.sentiment_controversy)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Tranh cãi và định hướng dư luận</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.signals:
        content = _format_list_content(result.signals)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Tín hiệu yếu và biến động</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.rss_insights:
        content = _format_list_content(result.rss_insights)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Góc nhìn sâu từ RSS</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.outlook_strategy:
        content = _format_list_content(result.outlook_strategy)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Đề xuất chiến lược</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.standalone_summaries:
        summaries_text = _format_standalone_summaries(result.standalone_summaries)
        if summaries_text:
            summaries_html = _escape_html(summaries_text).replace("\n", "<br>")
            ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">Điểm tin nguồn độc lập</div>
                        <div class="ai-block-content">{summaries_html}</div>
                    </div>"""

    ai_html += """
                    </div>
                </div>"""
    return ai_html
