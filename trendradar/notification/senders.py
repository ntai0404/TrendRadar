# coding=utf-8
"""
Message sender module

Send report data to various notification channels:
- Feishu (Feishu/Lark)
- DingTalk (DingTalk)
- WeCom (WeCom/WeWork)
- Telegram
- Email (Email)
- ntfy
- Bark
- Slack

Each sending function supports batch sending and achieves decoupling from CONFIG through parameterized configuration.
"""

import smtplib
import time
import json
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import requests

from .batch import add_batch_headers, get_max_batch_header_size
from .formatters import convert_markdown_to_mrkdwn, strip_markdown


def _extract_ai_stats(ai_analysis) -> Optional[Dict]:
    """Extract statistical data from AI analysis results"""
    if not ai_analysis or not getattr(ai_analysis, "success", False):
        return None
    return {
        "total_news": getattr(ai_analysis, "total_news", 0),
        "analyzed_news": getattr(ai_analysis, "analyzed_news", 0),
        "max_news_limit": getattr(ai_analysis, "max_news_limit", 0),
        "hotlist_count": getattr(ai_analysis, "hotlist_count", 0),
        "rss_count": getattr(ai_analysis, "rss_count", 0),
        "hotlist_analyzed": getattr(ai_analysis, "hotlist_analyzed", 0),
        "rss_analyzed": getattr(ai_analysis, "rss_analyzed", 0),
        "standalone_analyzed": getattr(ai_analysis, "standalone_analyzed", 0),
        "ai_mode": getattr(ai_analysis, "ai_mode", ""),
        "include_rss": getattr(ai_analysis, "include_rss", True),
        "include_standalone": getattr(ai_analysis, "include_standalone", False),
    }


def _render_ai_analysis(ai_analysis: Any, channel: str) -> str:
    """Render AI analysis content into specified channel format"""
    if not ai_analysis:
        return ""

    try:
        from trendradar.ai.formatter import get_ai_analysis_renderer
        renderer = get_ai_analysis_renderer(channel)
        return renderer(ai_analysis)
    except ImportError:
        return ""


# === SMTP email configuration ===
SMTP_CONFIGS = {
    # Gmail (using STARTTLS)
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "encryption": "TLS"},
    # QQ Mail (using SSL, more stable)
    "qq.com": {"server": "smtp.qq.com", "port": 465, "encryption": "SSL"},
    # Outlook (using STARTTLS)
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    "live.com": {"server": "smtp-mail.outlook.com", "port": 587, "encryption": "TLS"},
    # NetEase Mail (using SSL, more stable)
    "163.com": {"server": "smtp.163.com", "port": 465, "encryption": "SSL"},
    "126.com": {"server": "smtp.126.com", "port": 465, "encryption": "SSL"},
    # Sina Mail (using SSL)
    "sina.com": {"server": "smtp.sina.com", "port": 465, "encryption": "SSL"},
    # Sohu Mail (using SSL)
    "sohu.com": {"server": "smtp.sohu.com", "port": 465, "encryption": "SSL"},
    # Tianyi Mail (using SSL)
    "189.cn": {"server": "smtp.189.cn", "port": 465, "encryption": "SSL"},
    # Alibaba Cloud Mail (using TLS)
    "aliyun.com": {"server": "smtp.aliyun.com", "port": 465, "encryption": "TLS"},
    # Yandex Mail (using TLS)
    "yandex.com": {"server": "smtp.yandex.com", "port": 465, "encryption": "TLS"},
    # iCloud Mail (using SSL)
    "icloud.com": {"server": "smtp.mail.me.com", "port": 587, "encryption": "SSL"},
}


def send_to_feishu(
    webhook_url: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 29000,
    batch_interval: float = 1.0,
    split_content_func: Callable = None,
    get_time_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to Feishu (supports batch sending, supports hot list + RSS merge + independent display area)

    Args:
        webhook_url: Feishu Webhook URL
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật info (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch sending interval (seconds)
        split_content_func: Content batching function
        get_time_func: Function to get current time
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new block)

    Returns:
        bool: Whether sending is successful
    """
    headers = {"Content-Type": "application/json"}
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"Feishu{account_label}" if account_label else "Feishu"

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "feishu") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Reserve batch header space to avoid exceeding limit after adding header
    header_reserve = get_max_batch_header_size("feishu")
    batches = split_content_func(
        report_data,
        "feishu",
        update_info,
        max_bytes=batch_size - header_reserve,
        mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "feishu", batch_size)

    print(f"{log_prefix}Message divided into {len(batches)} batches for sending [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        # Select payload format based on webhook domain
        # www.feishu.cn uses plain text format, other domains (open.feishu.cn/open.larksuite.com) use Card 2.0
        if "www.feishu.cn" in webhook_url:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": batch_content,
                },
            }
        else:
            payload = {
                "msg_type": "interactive",
                "card": {
                    "schema": "2.0",
                    "body": {
                        "elements": [
                            {"tag": "markdown", "content": batch_content}
                        ]
                    },
                },
            }

        try:
            response = requests.post(
                webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                # Check Feishu's response status
                if result.get("StatusCode") == 0 or result.get("code") == 0:
                    print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                    # Interval between batches
                    if i < len(batches):
                        time.sleep(batch_interval)
                else:
                    error_msg = result.get("msg") or result.get("StatusMessage", "Unknown error")
                    print(
                        f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], error: {error_msg}"
                    )
                    return False
            else:
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], status code: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Batch {i}/{len(batches)} sending error [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches sent completely [{report_type}]")

    return True


def send_to_dingtalk(
    webhook_url: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 20000,
    batch_interval: float = 1.0,
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to DingTalk (supports batch sending, supports hotlist+RSS merge+independent display area)

    Args:
        webhook_url: DingTalk Webhook URL
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật information (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch sending interval (seconds)
        split_content_func: Content batching function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new block)

    Returns:
        bool: Whether sending is successful
    """
    headers = {"Content-Type": "application/json"}
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"DingTalk{account_label}" if account_label else "DingTalk"

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "dingtalk") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Reserve batch header space to avoid exceeding limit after adding header
    header_reserve = get_max_batch_header_size("dingtalk")
    batches = split_content_func(
        report_data,
        "dingtalk",
        update_info,
        max_bytes=batch_size - header_reserve,
        mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "dingtalk", batch_size)

    print(f"{log_prefix}Message divided into {len(batches)} batches for sending [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"TrendRadar Hotspot analysis report - {report_type}",
                "text": batch_content,
            },
        }

        try:
            response = requests.post(
                webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                    # Interval between batches
                    if i < len(batches):
                        time.sleep(batch_interval)
                else:
                    print(
                        f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], error: {result.get('errmsg')}"
                    )
                    return False
            else:
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], status code: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Batch {i}/{len(batches)} send error [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches send complete [{report_type}]")

    return True


def send_to_wework(
    webhook_url: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 4000,
    batch_interval: float = 1.0,
    msg_type: str = "markdown",
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to WeCom (supports batch sending, supports markdown and text formats, supports hotlist+RSS merge+independent display area)

    Args:
        webhook_url: WeCom Webhook URL
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật info (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch send interval (seconds)
        msg_type: Message type (markdown/text)
        split_content_func: Content batch split function
        rss_items: RSS stats item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new block)

    Returns:
        bool: Whether the send was successful
    """
    headers = {"Content-Type": "application/json"}
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"WeCom{account_label}" if account_label else "WeCom"

    # Get message type config (markdown or text)
    is_text_mode = msg_type.lower() == "text"

    if is_text_mode:
        print(f"{log_prefix}Using text format (personal WeChat mode) [{report_type}]")
    else:
        print(f"{log_prefix}Using markdown format (group bot mode) [{report_type}]")

    # text mode uses wework_text, markdown mode uses wework
    header_format_type = "wework_text" if is_text_mode else "wework"

    # Render AI analysis content and extract stats data
    ai_content = _render_ai_analysis(ai_analysis, "wework") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content, reserve space for batch header
    header_reserve = get_max_batch_header_size(header_format_type)
    batches = split_content_func(
        report_data, "wework", update_info, max_bytes=batch_size - header_reserve, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, header_format_type, batch_size)

    print(f"{log_prefix}Message split into {len(batches)} batches to send [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        # Build payload based on message type
        if is_text_mode:
            # text format: remove markdown syntax
            plain_content = strip_markdown(batch_content)
            payload = {"msgtype": "text", "text": {"content": plain_content}}
            content_size = len(plain_content.encode("utf-8"))
        else:
            # markdown format: keep as is
            payload = {"msgtype": "markdown", "markdown": {"content": batch_content}}
            content_size = len(batch_content.encode("utf-8"))

        print(
            f"Sending {log_prefix} batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        try:
            response = requests.post(
                webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                    # Interval between batches
                    if i < len(batches):
                        time.sleep(batch_interval)
                else:
                    print(
                        f"{log_prefix}Batch {i}/{len(batches)} send failed [{report_type}], error: {result.get('errmsg')}"
                    )
                    return False
            else:
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} send failed [{report_type}], status code: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Batch {i}/{len(batches)} send error [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches send complete [{report_type}]")

    return True


def send_to_telegram(
    bot_token: str,
    chat_id: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 4000,
    batch_interval: float = 1.0,
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to Telegram (supports batch sending, supports hotlist+RSS merge+independent display area)

    Args:
        bot_token: Telegram Bot Token
        chat_id: Telegram Chat ID
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật information (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch send interval (seconds)
        split_content_func: Content splitting function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new blocks)

    Returns:
        bool: Whether the sending was successful
    """
    headers = {"Content-Type": "application/json"}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"Telegram{account_label}" if account_label else "Telegram"

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "telegram") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content, reserve space for batch header
    header_reserve = get_max_batch_header_size("telegram")
    batches = split_content_func(
        report_data, "telegram", update_info, max_bytes=batch_size - header_reserve, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "telegram", batch_size)

    print(f"{log_prefix}Message divided into {len(batches)} batches for sending [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        payload = {
            "chat_id": chat_id,
            "text": batch_content,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                    # Interval between batches
                    if i < len(batches):
                        time.sleep(batch_interval)
                else:
                    print(
                        f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], error: {result.get('description')}"
                    )
                    return False
            else:
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} failed to send [{report_type}], status code: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Error sending batch {i}/{len(batches)} [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches finished sending [{report_type}]")

    return True


def send_to_email(
    from_email: str,
    password: str,
    to_email: str,
    report_type: str,
    html_file_path: str,
    custom_smtp_server: Optional[str] = None,
    custom_smtp_port: Optional[int] = None,
    *,
    get_time_func: Callable = None,
) -> bool:
    """
    Send email notification

    Args:
        from_email: Sender email
        password: Email password/authorization code
        to_email: Recipient email (multiple separated by commas)
        report_type: Report type
        html_file_path: HTML report file path
        custom_smtp_server: Custom SMTP server (optional)
        custom_smtp_port: Custom SMTP port (optional)
        get_time_func: Function to get current time

    Returns:
        bool: Whether the sending was successful

    Note:
        AI analysis content is already embedded during HTML generation, no need to append
    """
    try:
        if not html_file_path or not Path(html_file_path).exists():
            print(f"Error: HTML file does not exist or is not provided: {html_file_path}")
            return False

        print(f"Using HTML file: {html_file_path}")
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        domain = from_email.split("@")[-1].lower()

        if custom_smtp_server and custom_smtp_port:
            # Use custom SMTP configuration
            smtp_server = custom_smtp_server
            smtp_port = int(custom_smtp_port)
            # Determine encryption method based on port: 465=SSL, 587=TLS
            if smtp_port == 465:
                use_tls = False  # SSL mode (SMTP_SSL)
            elif smtp_port == 587:
                use_tls = True  # TLS mode (STARTTLS)
            else:
                # Other ports prioritize trying TLS (more secure, more widely supported)
                use_tls = True
        elif domain in SMTP_CONFIGS:
            # Use preset configuration
            config = SMTP_CONFIGS[domain]
            smtp_server = config["server"]
            smtp_port = config["port"]
            use_tls = config["encryption"] == "TLS"
        else:
            print(f"Unrecognized email service provider: {domain}, using general SMTP configuration")
            smtp_server = f"smtp.{domain}"
            smtp_port = 587
            use_tls = True

        msg = MIMEMultipart("alternative")

        # Strictly set From header according to RFC standards
        sender_name = "TrendRadar"
        msg["From"] = formataddr((sender_name, from_email))

        # Set recipient
        recipients = [addr.strip() for addr in to_email.split(",")]
        if len(recipients) == 1:
            msg["To"] = recipients[0]
        else:
            msg["To"] = ", ".join(recipients)

        # Set email subject
        now = get_time_func() if get_time_func else datetime.now()
        subject = f"TrendRadar Hotspot Analysis Report - {report_type} - {now.strftime('%m-%d %H:%M')}"
        msg["Subject"] = Header(subject, "utf-8")

        # Set other standard headers
        msg["MIME-Version"] = "1.0"
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Add plain text part (as fallback)
        text_content = f"""
TrendRadar Hotspot Analysis Report
========================
Report type: {report_type}
Generation time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Please use an HTML-supported email client to view the full report content.
        """
        text_part = MIMEText(text_content, "plain", "utf-8")
        msg.attach(text_part)

        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        print(f"Sending email to {to_email}...")
        print(f"SMTP server: {smtp_server}:{smtp_port}")
        print(f"Sender: {from_email}")

        try:
            if use_tls:
                # TLS mode
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.set_debuglevel(0)  # Set to 1 to view detailed debug information
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                # SSL mode
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
                server.set_debuglevel(0)
                server.ehlo()

            # Login
            server.login(from_email, password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"Email sent successfully [{report_type}] -> {to_email}")
            return True

        except smtplib.SMTPServerDisconnected:
            print("Email sending failed: Server unexpectedly disconnected, please check the network or try again later")
            return False

    except smtplib.SMTPAuthenticationError as e:
        print("Email sending failed: Authentication error, please check email and password/authorization code")
        print(f"Detailed error: {str(e)}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Email sending failed: Recipient address rejected {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"Email sending failed: Sender address rejected {e}")
        return False
    except smtplib.SMTPDataError as e:
        print(f"Email sending failed: Email data error {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"Email sending failed: Unable to connect to SMTP server {smtp_server}:{smtp_port}")
        print(f"Detailed error: {str(e)}")
        return False
    except Exception as e:
        print(f"Email sending failed [{report_type}]: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_to_ntfy(
    server_url: str,
    topic: str,
    token: Optional[str],
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 3800,
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to ntfy (supports batch sending, strictly adheres to 4KB limit, supports hotlist + RSS merge + independent display area)

    Args:
        server_url: ntfy server URL
        topic: ntfy topic
        token: ntfy access token (optional)
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật information (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts exist)
        batch_size: Batch size (bytes)
        split_content_func: Content splitting function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new block)

    Returns:
        bool: Whether the sending was successful
    """
    # Log prefix
    log_prefix = f"ntfy{account_label}" if account_label else "ntfy"

    # Avoid HTTP header encoding issues
    report_type_en_map = {
        "Tổng hợp cả ngày": "Daily Summary",
        "Bảng xếp hạng hiện tại": "Current Ranking",
        "Incremental Analysis": "Incremental Update",
        "Notification Connectivity Test": "Notification Test",
    }
    report_type_en = report_type_en_map.get(report_type, "News Report")

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Markdown": "yes",
        "Title": report_type_en,
        "Priority": "default",
        "Tags": "news",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Build complete URL, ensure correct format
    base_url = server_url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    url = f"{base_url}/{topic}"

    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "ntfy") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content, reserve space for batch header
    header_reserve = get_max_batch_header_size("ntfy")
    batches = split_content_func(
        report_data, "ntfy", update_info, max_bytes=batch_size - header_reserve, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "ntfy", batch_size)

    total_batches = len(batches)
    print(f"{log_prefix}Message divided into {total_batches} batches for sending [{report_type}]")

    # Reverse batch order so that the display order is correct in the ntfy client
    # ntfy displays the latest message on top, so we push starting from the last batch
    reversed_batches = list(reversed(batches))

    print(f"{log_prefix}Will push in reverse order (last batch pushed first) to ensure correct display order on the client")

    # Send batch by batch (reverse order)
    success_count = 0
    for idx, batch_content in enumerate(reversed_batches, 1):
        # Calculate correct batch number (user perspective number)
        actual_batch_num = total_batches - idx + 1

        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {actual_batch_num}/{total_batches} (push order: {idx}/{total_batches}), size: {content_size} bytes [{report_type}]"
        )

        # Check message size to ensure it does not exceed 4KB
        if content_size > 4096:
            print(f"Warning: {log_prefix}batch {actual_batch_num} message is too large ({content_size} bytes), may be rejected")

        # Cập nhật headers batch identifier
        current_headers = headers.copy()
        if total_batches > 1:
            current_headers["Title"] = f"{report_type_en} ({actual_batch_num}/{total_batches})"

        try:
            response = requests.post(
                url,
                headers=current_headers,
                data=batch_content.encode("utf-8"),
                proxies=proxies,
                timeout=30,
            )

            if response.status_code == 200:
                print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} sent successfully [{report_type}]")
                success_count += 1
                if idx < total_batches:
                    # Public servers recommend 2-3 seconds, self-hosted can be shorter
                    interval = 2 if "ntfy.sh" in server_url else 1
                    time.sleep(interval)
            elif response.status_code == 429:
                print(
                    f"{log_prefix}Batch {actual_batch_num}/{total_batches} rate limited [{report_type}], waiting before retry"
                )
                time.sleep(10)  # Wait 10 seconds before retry
                # Retry once
                retry_response = requests.post(
                    url,
                    headers=current_headers,
                    data=batch_content.encode("utf-8"),
                    proxies=proxies,
                    timeout=30,
                )
                if retry_response.status_code == 200:
                    print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} retry successful [{report_type}]")
                    success_count += 1
                else:
                    print(
                        f"{log_prefix}Batch {actual_batch_num}/{total_batches} retry failed, status code: {retry_response.status_code}"
                    )
            elif response.status_code == 413:
                print(
                    f"{log_prefix}Batch {actual_batch_num}/{total_batches} message too large and rejected [{report_type}], message size: {content_size} bytes"
                )
            else:
                print(
                    f"{log_prefix}Batch {actual_batch_num}/{total_batches} sending failed [{report_type}], status code: {response.status_code}"
                )
                try:
                    print(f"Error details: {response.text}")
                except:
                    pass

        except requests.exceptions.ConnectTimeout:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} connection timeout [{report_type}]")
        except requests.exceptions.ReadTimeout:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} read timeout [{report_type}]")
        except requests.exceptions.ConnectionError as e:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} connection error [{report_type}]: {e}")
        except Exception as e:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} sending exception [{report_type}]: {e}")

    # Determine if overall sending was successful
    if success_count == total_batches:
        print(f"{log_prefix}All {total_batches} batches sent [{report_type}]")
    elif success_count > 0:
        print(f"{log_prefix}Partially sent successfully: {success_count}/{total_batches} batches [{report_type}]")
    else:
        print(f"{log_prefix}Sending completely failed [{report_type}]")
        return False

    return True


def send_to_bark(
    bark_url: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 3600,
    batch_interval: float = 1.0,
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to Bark (supports batch sending, uses markdown format, supports hotlist+RSS merge+independent display area)

    Args:
        bark_url: Bark URL (contains device_key)
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật information (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch sending interval (seconds)
        split_content_func: Content batching function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new block)

    Returns:
        bool: Whether sending is successful
    """
    # Log prefix
    log_prefix = f"Bark{account_label}" if account_label else "Bark"

    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Parse Bark URL, extract device_key and API endpoint
    # Bark URL format: https://api.day.app/device_key or https://bark.day.app/device_key
    parsed_url = urlparse(bark_url)
    device_key = parsed_url.path.strip('/').split('/')[0] if parsed_url.path else None

    if not device_key:
        print(f"{log_prefix} URL format error, cannot extract device_key: {bark_url}")
        return False

    # Build correct API endpoint
    api_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/push"

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "bark") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content, reserve batch header space
    header_reserve = get_max_batch_header_size("bark")
    batches = split_content_func(
        report_data, "bark", update_info, max_bytes=batch_size - header_reserve, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "bark", batch_size)

    total_batches = len(batches)
    print(f"{log_prefix}Message divided into {total_batches} batches for sending [{report_type}]")

    # Reverse batch order so that the order is correct when displayed in Bark client
    # Bark displays the latest message on top, so we start pushing from the last batch
    reversed_batches = list(reversed(batches))

    print(f"{log_prefix}Will push in reverse order (last batch pushed first) to ensure correct display order on client")

    # Send batch by batch (reverse order)
    success_count = 0
    for idx, batch_content in enumerate(reversed_batches, 1):
        # Calculate correct batch number (user perspective number)
        actual_batch_num = total_batches - idx + 1

        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {actual_batch_num}/{total_batches} (push order: {idx}/{total_batches}), size: {content_size} bytes [{report_type}]"
        )

        # Check message size (Bark uses APNs, limit 4KB)
        if content_size > 4096:
            print(
                f"Warning: {log_prefix}batch {actual_batch_num}/{total_batches} message is too large ({content_size} bytes), may be rejected"
            )

        # Build JSON payload
        payload = {
            "title": report_type,
            "markdown": batch_content,
            "device_key": device_key,
            "sound": "default",
            "group": "TrendRadar",
            "action": "none",  # Clicking push jumps to APP without popping up dialog, convenient for reading
        }

        try:
            response = requests.post(
                api_endpoint,
                json=payload,
                proxies=proxies,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} sent successfully [{report_type}]")
                    success_count += 1
                    # Interval between batches
                    if idx < total_batches:
                        time.sleep(batch_interval)
                else:
                    print(
                        f"{log_prefix}Batch {actual_batch_num}/{total_batches} sending failed [{report_type}], error: {result.get('message', 'Unknown error')}"
                    )
            else:
                print(
                    f"{log_prefix}Batch {actual_batch_num}/{total_batches} sending failed [{report_type}], status code: {response.status_code}"
                )
                try:
                    print(f"Error details: {response.text}")
                except:
                    pass

        except requests.exceptions.ConnectTimeout:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} connection timeout [{report_type}]")
        except requests.exceptions.ReadTimeout:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} read timeout [{report_type}]")
        except requests.exceptions.ConnectionError as e:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} connection error [{report_type}]: {e}")
        except Exception as e:
            print(f"{log_prefix}Batch {actual_batch_num}/{total_batches} send exception [{report_type}]: {e}")

    # Determine if overall sending is successful
    if success_count == total_batches:
        print(f"{log_prefix}All {total_batches} batches sending completed [{report_type}]")
    elif success_count > 0:
        print(f"{log_prefix}Partially sent successfully: {success_count}/{total_batches} batches [{report_type}]")
    else:
        print(f"{log_prefix}Sending completely failed [{report_type}]")
        return False

    return True


def send_to_slack(
    webhook_url: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 4000,
    batch_interval: float = 1.0,
    split_content_func: Callable = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to Slack (supports batch sending, uses mrkdwn format, supports hotlist+RSS merge+independent display area)

    Args:
        webhook_url: Slack Webhook URL
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật info (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch sending interval (seconds)
        split_content_func: Content batching function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new blocks)

    Returns:
        bool: Whether sending was successful
    """
    headers = {"Content-Type": "application/json"}
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"Slack{account_label}" if account_label else "Slack"

    # Render AI analysis content and extract statistical data
    ai_content = _render_ai_analysis(ai_analysis, "slack") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content, reserve space for batch header
    header_reserve = get_max_batch_header_size("slack")
    batches = split_content_func(
        report_data, "slack", update_info, max_bytes=batch_size - header_reserve, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header (space reserved, will not exceed limit)
    batches = add_batch_headers(batches, "slack", batch_size)

    print(f"{log_prefix}Message divided into {len(batches)} batches for sending [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        # Convert Markdown to mrkdwn format
        mrkdwn_content = convert_markdown_to_mrkdwn(batch_content)

        content_size = len(mrkdwn_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        # Build Slack payload (using simple text field, supports mrkdwn)
        payload = {"text": mrkdwn_content}

        try:
            response = requests.post(
                webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
            )

            # Slack Incoming Webhooks returns "ok" text upon success
            if response.status_code == 200 and response.text == "ok":
                print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                # Interval between batches
                if i < len(batches):
                    time.sleep(batch_interval)
            else:
                error_msg = response.text if response.text else f"Status code: {response.status_code}"
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} sending failed [{report_type}], error: {error_msg}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Batch {i}/{len(batches)} sending error [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches sending completed [{report_type}]")

    return True


def send_to_generic_webhook(
    webhook_url: str,
    payload_template: Optional[str],
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    account_label: str = "",
    *,
    batch_size: int = 4000,
    batch_interval: float = 1.0,
    split_content_func: Optional[Callable] = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    ai_analysis: Any = None,
    display_regions: Optional[Dict] = None,
    standalone_data: Optional[Dict] = None,
) -> bool:
    """
    Send to generic Webhook (supports batch sending, supports custom JSON template, supports hotlist+RSS merge+independent display area)

    Args:
        webhook_url: Webhook URL
        payload_template: JSON template string, supports {title} and {content} placeholders
        report_data: Report data
        report_type: Report type
        update_info: Cập nhật information (optional)
        proxy_url: Proxy URL (optional)
        mode: Report mode (daily/current)
        account_label: Account label (displayed when multiple accounts)
        batch_size: Batch size (bytes)
        batch_interval: Batch sending interval (seconds)
        split_content_func: Content batching function
        rss_items: RSS statistics item list (optional, used for merged push)
        rss_new_items: RSS new item list (optional, used for new blocks)

    Returns:
        bool: Whether the sending was successful
    """
    if split_content_func is None:
        raise ValueError("split_content_func is required")

    headers = {"Content-Type": "application/json"}
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Log prefix
    log_prefix = f"General Webhook{account_label}" if account_label else "General Webhook"

    # Render AI analysis content and extract statistical data (General Webhook uses markdown format)
    ai_content = _render_ai_analysis(ai_analysis, "wework") if ai_analysis else None
    ai_stats = _extract_ai_stats(ai_analysis)

    # Get batched content
    # Use 'wework' as format_type to get general output in markdown format
    # Reserve some space for the template shell
    template_overhead = 200
    batches = split_content_func(
        report_data, "wework", update_info, max_bytes=batch_size - template_overhead, mode=mode,
        rss_items=rss_items,
        rss_new_items=rss_new_items,
        ai_content=ai_content,
        standalone_data=standalone_data,
        ai_stats=ai_stats,
        report_type=report_type,
    )

    # Uniformly add batch header
    batches = add_batch_headers(batches, "wework", batch_size)

    print(f"{log_prefix}Message divided into {len(batches)} batches for sending [{report_type}]")

    # Send batch by batch
    for i, batch_content in enumerate(batches, 1):
        content_size = len(batch_content.encode("utf-8"))
        print(
            f"Sending {log_prefix}batch {i}/{len(batches)}, size: {content_size} bytes [{report_type}]"
        )

        try:
            # Build payload
            if payload_template:
                # Simple string replacement
                # Note: content may contain JSON special characters, needs to be escaped first
                json_content = json.dumps(batch_content)[1:-1] # Remove leading and trailing quotes
                json_title = json.dumps(report_type)[1:-1]
                
                payload_str = payload_template.replace("{content}", json_content).replace("{title}", json_title)
                
                # Try to parse as JSON object to verify validity
                try:
                    payload = json.loads(payload_str)
                except json.JSONDecodeError as e:
                    print(f"{log_prefix} JSON template parsing failed: {e}")
                    # Fallback to default format
                    payload = {"title": report_type, "content": batch_content}
            else:
                # Default format
                payload = {"title": report_type, "content": batch_content}

            response = requests.post(
                webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                print(f"{log_prefix}Batch {i}/{len(batches)} sent successfully [{report_type}]")
                if i < len(batches):
                    time.sleep(batch_interval)
            else:
                print(
                    f"{log_prefix}Batch {i}/{len(batches)} sending failed [{report_type}], status code: {response.status_code}, response: {response.text}"
                )
                return False
        except Exception as e:
            print(f"{log_prefix}Error sending batch {i}/{len(batches)} [{report_type}]: {e}")
            return False

    print(f"{log_prefix}All {len(batches)} batches sent completely [{report_type}]")

    return True
