# coding=utf-8
"""
batch processing module

Provides helper functions for sending messages in batches
"""

from typing import List


def get_batch_header(format_type: str, batch_num: int, total_batches: int) -> str:
    """Generate the batch header of the corresponding format according to format_type

    Args:
        format_type: push type (telegram, slack, wework_text, bark, feishu, dingtalk, ntfy, wework)
        batch_num: current batch number
        total_batches: total number of batches

    Returns:
        Formatted batch header string
    """
    if format_type == "telegram":
        return f"<b>[Phần {batch_num}/{total_batches}]</b>\n\n"
    elif format_type == "slack":
        return f"*[Phần {batch_num}/{total_batches}]*\n\n"
    elif format_type in ("wework_text", "bark"):
        # Enterprise WeChat text mode and Bark use plain text format
        return f"[Phần {batch_num}/{total_batches}]\n\n"
    else:
        # Feishu, DingTalk, ntfy, enterprise WeChat markdown mode
        return f"**[Phần {batch_num}/{total_batches}]**\n\n"


def get_max_batch_header_size(format_type: str) -> int:
    """Estimate the maximum number of bytes in the batch header (assuming a maximum of 99 batches)

    Used to reserve space during batching to avoid subsequent truncation from destroying content integrity.

    Args:
        format_type: push type

    Returns:
        Maximum number of header bytes
    """
    # Generate worst case header (99/99 batches)
    max_header = get_batch_header(format_type, 99, 99)
    return len(max_header.encode("utf-8"))


def truncate_to_bytes(text: str, max_bytes: int) -> str:
    """Safely truncate the string to the specified number of bytes and avoid truncating multi-byte characters

    Args:
        text: text to truncate
        max_bytes: maximum number of bytes

    Returns:
        Truncated text
    """
    text_bytes = text.encode("utf-8")
    if len(text_bytes) <= max_bytes:
        return text

    truncated = text_bytes[:max_bytes]
    for i in range(min(4, len(truncated))):
        try:
            return truncated[: len(truncated) - i].decode("utf-8")
        except UnicodeDecodeError:
            continue
    return ""


def truncate_at_line_boundary(text: str, max_bytes: int) -> str:
    """Truncate at line boundaries, making sure not to break in the middle of titles or content

    First truncate by bytes, and then roll back to the nearest newline position to ensure that each line is complete.

    Args:
        text: text to truncate
        max_bytes: maximum number of bytes

    Returns:
        Truncated text ending at last full line
    """
    if len(text.encode("utf-8")) <= max_bytes:
        return text

    rough_cut = truncate_to_bytes(text, max_bytes)
    last_newline = rough_cut.rfind("\n")
    if last_newline > 0:
        return rough_cut[:last_newline]
    return rough_cut


def truncate_preserving_footer(content: str, max_bytes: int) -> str:
    """Truncate the content, giving priority to retaining the tail footer (Cập nhật time, etc.), and the main text is truncated at the line boundary

    Identify the footer area at the end of the content (Cập nhật time, version prompt, etc.),
    The text part before the footer is cut off at the line boundary, and then the complete footer is spliced.

    Args:
        content: complete content (text + footer)
        max_bytes: maximum number of bytes

    Returns:
        For the truncated content, the footer is kept intact and the text is truncated at the line boundary.
    """
    if len(content.encode("utf-8")) <= max_bytes:
        return content

    # Common opening patterns for footers on various platforms
    footer_markers = ["\n\n\n> ", "\n\n> ", "\n\n<font", "\n\n_", "\n\nCập nhật time"]
    footer_start = -1
    for marker in footer_markers:
        pos = content.rfind(marker)
        if pos > 0:
            footer_start = pos
            break

    if footer_start <= 0:
        return truncate_at_line_boundary(content, max_bytes)

    footer = content[footer_start:]
    body = content[:footer_start]
    footer_size = len(footer.encode("utf-8"))

    if footer_size >= max_bytes:
        return truncate_at_line_boundary(content, max_bytes)

    truncated_body = truncate_at_line_boundary(body, max_bytes - footer_size)
    return truncated_body + footer


def _split_oversized_batch(content: str, max_content_bytes: int) -> List[str]:
    """Split the over-limit batch into multiple sub-batches according to row boundaries (retain footer)

    Args:
        content: Excessive batch content (including footer)
        max_content_bytes: Maximum number of bytes per sub-batch

    Returns:
        Split sub-batch list
    """
    # Identify footer
    footer_markers = ["\n\n\n> ", "\n\n> ", "\n\n<font", "\n\n_", "\n\nCập nhật time"]
    footer = ""
    body = content
    for marker in footer_markers:
        pos = content.rfind(marker)
        if pos > 0:
            footer = content[pos:]
            body = content[:pos]
            break

    footer_size = len(footer.encode("utf-8"))
    available = max_content_bytes - footer_size
    if available <= 0:
        return [truncate_at_line_boundary(content, max_content_bytes)]

    # Split body by rows
    lines = body.split("\n")
    sub_batches = []
    current = ""

    for line in lines:
        candidate = current + line + "\n"
        if len(candidate.encode("utf-8")) > available and current.strip():
            sub_batches.append(current + footer)
            current = line + "\n"
        else:
            current = candidate

    if current.strip():
        sub_batches.append(current + footer)

    return sub_batches if sub_batches else [content]


def add_batch_headers(
    batches: List[str], format_type: str, max_bytes: int
) -> List[str]:
    """Add a header to the batch and split it into multiple sub-batches when the limit is exceeded (the content will not be discarded)

    Args:
        batches: original batch list
        format_type: push type (bark, telegram, feishu, etc.)
        max_bytes: The maximum byte limit for this push type

    Returns:
        Batch list after adding header
    """
    if len(batches) <= 1:
        return batches

    # First pass: Split over-limit batches
    expanded = []
    max_header_size = get_max_batch_header_size(format_type)
    for content in batches:
        if len(content.encode("utf-8")) + max_header_size > max_bytes:
            expanded.extend(_split_oversized_batch(content, max_bytes - max_header_size))
        else:
            expanded.append(content)

    # Second pass: add header
    if len(expanded) <= 1:
        return expanded

    total = len(expanded)
    result = []
    for i, content in enumerate(expanded, 1):
        header = get_batch_header(format_type, i, total)
        header_size = len(header.encode("utf-8"))
        max_content_size = max_bytes - header_size

        if len(content.encode("utf-8")) > max_content_size:
            # Still exceeds the limit (extreme case: a single line is too long), the line boundary is truncated
            content = truncate_preserving_footer(content, max_content_size)

        result.append(header + content)

    return result
