#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News crawler container management tool - supercronic
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime

# Web server configuration
WEBSERVER_PORT = int(os.environ.get("WEBSERVER_PORT", "8080"))
WEBSERVER_DIR = "/app/output"
WEBSERVER_PID_FILE = "/tmp/webserver.pid"
def get_timestamp():
    """Get current timestamp string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_command(cmd, shell=True, capture_output=True):
    """Execute system command"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def manual_run():
    """Manually execute crawler once"""
    print("🔄 Manually executing crawler...")
    try:
        result = subprocess.run(
            ["python", "-m", "trendradar"], cwd="/app", capture_output=False, text=True
        )
        if result.returncode == 0:
            print("✅ Execution completed")
        else:
            print(f"❌ Execution failed, exit code: {result.returncode}")
    except Exception as e:
        print(f"❌ Execution error: {e}")


def parse_cron_schedule(cron_expr):
    """Parse cron expression and return human-readable description"""
    if not cron_expr or cron_expr == "Not set":
        return "Not set"
    
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return f"Original expression: {cron_expr}"
        
        minute, hour, day, month, weekday = parts
        
        # Analyze minutes
        if minute == "*":
            minute_desc = "Every minute"
        elif minute.startswith("*/"):
            interval = minute[2:]
            minute_desc = f"Every {interval} minutes"
        elif "," in minute:
            minute_desc = f"At minute {minute}"
        else:
            minute_desc = f"At minute {minute}"
        
        # Analyze hours
        if hour == "*":
            hour_desc = "Every hour"
        elif hour.startswith("*/"):
            interval = hour[2:]
            hour_desc = f"Every {interval} hours"
        elif "," in hour:
            hour_desc = f"At {hour} o'clock"
        else:
            hour_desc = f"At {hour} o'clock"
        
        # Analyze days
        if day == "*":
            day_desc = "Every day"
        elif day.startswith("*/"):
            interval = day[2:]
            day_desc = f"Every {interval} days"
        else:
            day_desc = f"On day {day} of every month"
        
        # Analyze months
        if month == "*":
            month_desc = "Every month"
        else:
            month_desc = f"In month {month}"
        
        # Analyze weekdays
        weekday_names = {
            "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
            "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday"
        }
        if weekday == "*":
            weekday_desc = ""
        else:
            weekday_desc = f"On {weekday_names.get(weekday, weekday)}"
        
        # Combine descriptions
        if minute.startswith("*/") and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # Simple interval pattern, e.g. */30 * * * *
            return f"Execute once every {minute[2:]} minutes"
        elif hour != "*" and minute != "*" and day == "*" and month == "*" and weekday == "*":
            # Specific time every day, e.g. 0 9 * * *
            return f"Execute every day at {hour}:{minute.zfill(2)}"
        elif weekday != "*" and day == "*":
            # Specific time every week
            return f"{weekday_desc}{hour}:{minute.zfill(2)} run"
        else:
            # Complex mode, show detailed information
            desc_parts = [part for part in [month_desc, day_desc, weekday_desc, hour_desc, minute_desc] if part and part != "Every month" and part != "Every day" and part != "Every hour"]
            if desc_parts:
                return " ".join(desc_parts) + " run"
            else:
                return f"Complex expression: {cron_expr}"
    
    except Exception as e:
        return f"Parsing failed: {cron_expr}"


def show_status():
    """Show container status"""
    print("📊 Container status:")

    # Check PID 1 status
    supercronic_is_pid1 = False
    pid1_cmdline = ""
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 PID 1 process: {pid1_cmdline}")
        
        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ supercronic is running correctly as PID 1")
            supercronic_is_pid1 = True
        else:
            print("  ❌ PID 1 is not supercronic")
            print(f"  📋 Actual PID 1: {pid1_cmdline}")
    except Exception as e:
        print(f"  ❌ Failed to read PID 1 info: {e}")

    # Check environment variables
    cron_schedule = os.environ.get("CRON_SCHEDULE", "Not set")
    run_mode = os.environ.get("RUN_MODE", "Not set")
    immediate_run = os.environ.get("IMMEDIATE_RUN", "Not set")
    
    print(f"  ⚙️ Run configuration:")
    print(f"    CRON_SCHEDULE: {cron_schedule}")
    
    # Parse and display the meaning of the cron expression
    cron_description = parse_cron_schedule(cron_schedule)
    print(f"    ⏰ Execution frequency: {cron_description}")
    
    print(f"    RUN_MODE: {run_mode}")
    print(f"    IMMEDIATE_RUN: {immediate_run}")

    # Check configuration files
    config_files = ["/app/config/config.yaml", "/app/config/frequency_words.txt"]
    print("  📁 Configuration files:")
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"    ✅ {Path(file_path).name}")
        else:
            print(f"    ❌ {Path(file_path).name} missing")

    # Check key files
    key_files = [
        ("/usr/local/bin/supercronic-linux-amd64", "supercronic binary file"),
        ("/usr/local/bin/supercronic", "supercronic symlink"),
        ("/tmp/crontab", "crontab file"),
        ("/entrypoint.sh", "startup script")
    ]
    
    print("  📂 Key file check:")
    for file_path, description in key_files:
        if Path(file_path).exists():
            print(f"    ✅ {description}: exists")
            # For crontab file, display content
            if file_path == "/tmp/crontab":
                try:
                    with open(file_path, 'r') as f:
                        crontab_content = f.read().strip()
                        print(f"         Content: {crontab_content}")
                except:
                    pass
        else:
            print(f"    ❌ {description}: does not exist")

    # Check container uptime
    print("  ⏱️ Container time info:")
    try:
        # Check PID 1 start time
        with open('/proc/1/stat', 'r') as f:
            stat_content = f.read().strip().split()
            if len(stat_content) >= 22:
                # starttime is the 22nd field (index 21)
                starttime_ticks = int(stat_content[21])
                
                # Read system boot time
                with open('/proc/stat', 'r') as stat_f:
                    for line in stat_f:
                        if line.startswith('btime'):
                            boot_time = int(line.split()[1])
                            break
                    else:
                        boot_time = 0
                
                # Read system clock frequency
                clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                
                if boot_time > 0:
                    pid1_start_time = boot_time + (starttime_ticks / clock_ticks)
                    current_time = time.time()
                    uptime_seconds = int(current_time - pid1_start_time)
                    uptime_minutes = uptime_seconds // 60
                    uptime_hours = uptime_minutes // 60
                    
                    if uptime_hours > 0:
                        print(f"    PID 1 uptime: {uptime_hours} hours {uptime_minutes % 60} minutes")
                    else:
                        print(f"    PID 1 uptime: {uptime_minutes} minutes ({uptime_seconds} seconds)")
                else:
                    print(f"    PID 1 uptime: unable to calculate precisely")
            else:
                print("    ❌ Unable to parse PID 1 statistics")
    except Exception as e:
        print(f"    ❌ Time check failed: {e}")

    # Status summary and suggestions
    print("  📊 Status summary:")
    if supercronic_is_pid1:
        print("    ✅ supercronic is running correctly as PID 1")
        print("    ✅ Cron jobs should be working normally")
        
        # Show current schedule information
        if cron_schedule != "Not set":
            print(f"    ⏰ Current schedule: {cron_description}")
            
            # Provide some common scheduling suggestions
            if "minute" in cron_description and "every 30 minutes" not in cron_description and "every 60 minutes" not in cron_description:
                print("    💡 Frequent execution mode, suitable for real-time monitoring")
            elif "hour" in cron_description:
                print("    💡 Hourly execution mode, suitable for periodic summaries")
            elif "day" in cron_description:
                print("    💡 Daily execution mode, suitable for daily report generation")
        
        print("    💡 If cron jobs do not execute, check:")
        print("       • if crontab format is correct")
        print("       • if timezone setting is correct")
        print("       • if the application has errors")
    else:
        print("    ❌ supercronic status is abnormal")
        if pid1_cmdline:
            print(f"    📋 Current PID 1: {pid1_cmdline}")
        print("    💡 Suggested actions:")
        print("       • Restart container: docker restart trendradar")
        print("       • Check container logs: docker logs trendradar")

    # Show log check suggestions
    print("  📋 Running status check:")
    print("    • View full container logs: docker logs trendradar")
    print("    • View real-time logs: docker logs -f trendradar")
    print("    • Manually execute test: python manage.py run")
    print("    • Restart container service: docker restart trendradar")


def show_config():
    """Show current configuration"""
    print("⚙️ Current configuration:")

    env_vars = [
        # Run configuration
        "CRON_SCHEDULE",
        "RUN_MODE",
        "IMMEDIATE_RUN",
        # Notification channels
        "FEISHU_WEBHOOK_URL",
        "DINGTALK_WEBHOOK_URL",
        "WEWORK_WEBHOOK_URL",
        "WEWORK_MSG_TYPE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "NTFY_SERVER_URL",
        "NTFY_TOPIC",
        "NTFY_TOKEN",
        "BARK_URL",
        "SLACK_WEBHOOK_URL",
        # AI analysis configuration
        "AI_ANALYSIS_ENABLED",
        "AI_API_KEY",
        "AI_PROVIDER",
        "AI_MODEL",
        "AI_BASE_URL",
        # Remote storage configuration
        "S3_BUCKET_NAME",
        "S3_ACCESS_KEY_ID",
        "S3_ENDPOINT_URL",
        "S3_REGION",
    ]

    for var in env_vars:
        value = os.environ.get(var, "Not set")
        # Hide sensitive information
        if any(sensitive in var for sensitive in ["WEBHOOK", "TOKEN", "KEY", "SECRET"]):
            if value and value != "Not set":
                masked_value = value[:10] + "***" if len(value) > 10 else "***"
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: {value}")

    crontab_file = "/tmp/crontab"
    if Path(crontab_file).exists():
        print("  📅 Crontab content:")
        try:
            with open(crontab_file, "r") as f:
                content = f.read().strip()
                print(f"    {content}")
        except Exception as e:
            print(f"    Read failed: {e}")
    else:
        print("  📅 Crontab file does not exist")


def show_files():
    """Show output files"""
    print("📁 Output files:")

    output_dir = Path("/app/output")
    if not output_dir.exists():
        print("  📭 Output directory does not exist")
        return

    # New structure: flattened directory
    # - output/news/*.db
    # - output/rss/*.db
    # - output/txt/{date}/*.txt
    # - output/html/{date}/*.html

    # Check news database
    news_dir = output_dir / "news"
    if news_dir.exists():
        db_files = sorted(news_dir.glob("*.db"), key=lambda x: x.name, reverse=True)
        if db_files:
            print(f"  💾 Hotlist database (news/): {len(db_files)} items")
            for db_file in db_files[:5]:
                mtime = time.ctime(db_file.stat().st_mtime)
                size_kb = db_file.stat().st_size // 1024
                print(f"    📀 {db_file.name} ({size_kb}KB, {mtime.split()[3][:5]})")
            if len(db_files) > 5:
                print(f"    ... and {len(db_files) - 5} more")

    # Check RSS database
    rss_dir = output_dir / "rss"
    if rss_dir.exists():
        db_files = sorted(rss_dir.glob("*.db"), key=lambda x: x.name, reverse=True)
        if db_files:
            print(f"  📰 RSS database (rss/): {len(db_files)} items")
            for db_file in db_files[:5]:
                mtime = time.ctime(db_file.stat().st_mtime)
                size_kb = db_file.stat().st_size // 1024
                print(f"    📀 {db_file.name} ({size_kb}KB, {mtime.split()[3][:5]})")
            if len(db_files) > 5:
                print(f"    ... and {len(db_files) - 5} more")

    # Check TXT snapshot directory
    txt_dir = output_dir / "txt"
    if txt_dir.exists():
        date_dirs = sorted([d for d in txt_dir.iterdir() if d.is_dir()], reverse=True)
        if date_dirs:
            print(f"  📄 TXT snapshot (txt/): {len(date_dirs)} days")
            for date_dir in date_dirs[:3]:
                txt_files = list(date_dir.glob("*.txt"))
                if txt_files:
                    recent = sorted(txt_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                    mtime = time.ctime(recent.stat().st_mtime)
                    print(f"    📅 {date_dir.name}: {len(txt_files)} files (latest: {mtime.split()[3][:5]})")

    # Check HTML report directory
    html_dir = output_dir / "html"
    if html_dir.exists():
        date_dirs = sorted([d for d in html_dir.iterdir() if d.is_dir()], reverse=True)
        if date_dirs:
            print(f"  🌐 HTML report (html/): {len(date_dirs)} days")
            for date_dir in date_dirs[:3]:
                html_files = list(date_dir.glob("*.html"))
                if html_files:
                    recent = sorted(html_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                    mtime = time.ctime(recent.stat().st_mtime)
                    print(f"    📅 {date_dir.name}: {len(html_files)} files (latest: {mtime.split()[3][:5]})")


def show_logs():
    """Show real-time logs"""
    print("📋 Real-time logs (press Ctrl+C to exit):")
    print("💡 Tip: This will show the output of the PID 1 process")
    try:
        # Try multiple methods to view logs
        log_files = [
            "/proc/1/fd/1",  # Standard output of PID 1
            "/proc/1/fd/2",  # Standard error of PID 1
        ]
        
        for log_file in log_files:
            if Path(log_file).exists():
                print(f"📄 Trying to read: {log_file}")
                subprocess.run(["tail", "-f", log_file], check=True)
                break
        else:
            print("📋 Cannot find standard log file, recommend using: docker logs trendradar")
            
    except KeyboardInterrupt:
        print("\n👋 Exiting log view")
    except Exception as e:
        print(f"❌ Failed to view logs: {e}")
        print("💡 Recommend using: docker logs trendradar")


def restart_supercronic():
    """Restart supercronic process"""
    print("🔄 Restarting supercronic...")
    print("⚠️ Note: supercronic is PID 1, cannot be restarted directly")

    # Check current PID 1
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 Current PID 1: {pid1_cmdline}")

        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ PID 1 is supercronic")
            print("  💡 To restart supercronic, you need to restart the entire container:")
            print("    docker restart trendradar")
        else:
            print("  ❌ PID 1 is not supercronic, this is an abnormal state")
            print("  💡 Suggest restarting the container to fix the issue:")
            print("    docker restart trendradar")
    except Exception as e:
        print(f"  ❌ Unable to check PID 1: {e}")
        print("  💡 Suggest restarting the container: docker restart trendradar")


def _read_proc_cmdline(pid: int) -> str:
    """Read process cmdline, return empty string on failure."""
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if not proc_cmdline.exists():
        return ""
    try:
        with open(proc_cmdline, "rb") as f:
            return f.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def _is_expected_webserver_process(pid: int) -> bool:
    """Check if pid is the http.server process for the current port."""
    cmdline = _read_proc_cmdline(pid)
    if not cmdline:
        return False
    return "http.server" in cmdline and str(WEBSERVER_PORT) in cmdline


def _terminate_webserver_process(pid: int, require_expected: bool = True) -> bool:
    """Attempt to terminate the Web server process.

    When require_expected=True, only terminate processes confirmed to be http.server to avoid accidental kills.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return True

    if require_expected and not _is_expected_webserver_process(pid):
        print(f"  ⚠️ PID {pid} exists but is not a Web server process, skipping termination")
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
            print(f"  ⚠️ Force stopping Web server (PID: {pid})")
        except OSError:
            print(f"  ✅ Web server stopped (PID: {pid})")
        return True
    except OSError:
        return True


def _is_webserver_running(pid: int) -> bool:
    """Check if the Web server process is actually running."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False

    if not _is_expected_webserver_process(pid):
        return False

    try:
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{WEBSERVER_PORT}/", method="HEAD")
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        try:
            time.sleep(1)
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{WEBSERVER_PORT}/", method="HEAD")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            return False


def _cleanup_stale_pid():
    """Clean up invalid PID files"""
    if not Path(WEBSERVER_PID_FILE).exists():
        return False

    try:
        with open(WEBSERVER_PID_FILE, 'r') as f:
            old_pid = int(f.read().strip())
        os.remove(WEBSERVER_PID_FILE)
        print(f"  🧹 Cleaning up invalid PID file (PID: {old_pid})")
        return True
    except Exception:
        return False


def start_webserver():
    """Start Web server to host the output directory"""
    print(f"🌐 Starting Web server (Port: {WEBSERVER_PORT})...")
    print(f"  🔒 Security tip: Only provides static file access, restricted to the {WEBSERVER_DIR} directory")

    # Check if already running
    if Path(WEBSERVER_PID_FILE).exists():
        try:
            with open(WEBSERVER_PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            # Use enhanced process check
            if _is_webserver_running(old_pid):
                print(f"  ⚠️ Web server is already running (PID: {old_pid})")
                print(f"  💡 Access: http://localhost:{WEBSERVER_PORT}")
                print("  💡 Stop service: python manage.py stop_webserver")
                return

            # When process is abnormal, prioritize attempting to terminate the old process to avoid restart failure due to port occupation
            _terminate_webserver_process(old_pid, require_expected=True)
            _cleanup_stale_pid()
            print(f"  ℹ️ Detected invalid PID file, cleaned up")

        except Exception as e:
            print(f"  ⚠️ Clean up old PID file: {e}")
            _cleanup_stale_pid()

    # Check if directory exists
    if not Path(WEBSERVER_DIR).exists():
        print(f"  ❌ Directory does not exist: {WEBSERVER_DIR}")
        return

    try:
        # Start HTTP server
        # Use --bind to bind to 0.0.0.0 to make it accessible inside the container
        # Working directory restricted to WEBSERVER_DIR to prevent access to other directories
        process = subprocess.Popen(
            [sys.executable, '-m', 'http.server', str(WEBSERVER_PORT), '--bind', '0.0.0.0'],
            cwd=WEBSERVER_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Wait a moment to ensure the server starts
        time.sleep(1)

        # Check if the process is still running
        if process.poll() is None:
            # Save PID
            with open(WEBSERVER_PID_FILE, 'w') as f:
                f.write(str(process.pid))
            print(f"  ✅ Web server started (PID: {process.pid})")
            print(f"  📁 Service directory: {WEBSERVER_DIR} (read-only, static files only)")
            print(f"  🌐 Access address: http://localhost:{WEBSERVER_PORT}")
            print(f"  📄 Homepage: http://localhost:{WEBSERVER_PORT}/index.html")
            print("  💡 Stop service: python manage.py stop_webserver")
        else:
            print(f"  ❌ Web server failed to start")
    except Exception as e:
        print(f"  ❌ Failed to start: {e}")


def stop_webserver():
    """Stop Web Server"""
    print("🛑 Stopping Web Server...")

    if not Path(WEBSERVER_PID_FILE).exists():
        print("  ℹ️ Web Server is not running")
        return

    try:
        with open(WEBSERVER_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        _terminate_webserver_process(pid, require_expected=True)
        if Path(WEBSERVER_PID_FILE).exists():
            os.remove(WEBSERVER_PID_FILE)
    except Exception as e:
        print(f"  ❌ Stop failed: {e}")
        # Try to clean up PID file
        try:
            os.remove(WEBSERVER_PID_FILE)
        except:
            pass


def webserver_status():
    """Check Web Server status"""
    print("🌐 Web Server status:")

    if not Path(WEBSERVER_PID_FILE).exists():
        print("  ⭕ Not running")
        print(f"  💡 Start service: python manage.py start_webserver")
        return

    try:
        with open(WEBSERVER_PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Use enhanced process check
        if _is_webserver_running(pid):
            print(f"  ✅ Running (PID: {pid})")
            print(f"  📁 Service directory: {WEBSERVER_DIR}")
            print(f"  🌐 Access URL: http://localhost:{WEBSERVER_PORT}")
            print(f"  📄 Homepage: http://localhost:{WEBSERVER_PORT}/index.html")
            print("  💡 Stop service: python manage.py stop_webserver")
        else:
            print(f"  ⭕ Not running (PID file exists but process is unavailable)")
            _cleanup_stale_pid()
            print("  💡 Start service: python manage.py start_webserver")
    except Exception as e:
        print(f"  ❌ Status check failed: {e}")


def show_help():
    """Show help information"""
    help_text = """
🐳 TrendRadar Container Management Tool

📋 Command list:
  run              - Manually execute crawler once
  status           - Show container running status
  config           - Show current configuration
  files            - Show output files
  logs             - View logs in real-time
  restart          - Restart instructions
  start_webserver  - Start Web Server to host output directory
  stop_webserver   - Stop Web Server
  webserver_status - Check Web Server status
  help             - Show this help

📖 Usage examples:
  # Execute in container
  python manage.py run
  python manage.py status
  python manage.py logs
  python manage.py start_webserver

  # Execute on host machine
  docker exec -it trendradar python manage.py run
  docker exec -it trendradar python manage.py status
  docker exec -it trendradar python manage.py start_webserver
  docker logs trendradar

💡 Common operation guide:
  1. Check running status: status
     - Check if supercronic is PID 1
     - Check configuration files and key files
     - Check cron schedule settings

  2. Manually execute test: run
     - Execute a news crawl immediately
     - Test if the program is working properly

  3. View logs: logs
     - Monitor running status in real-time
     - Can also use: docker logs trendradar

  4. Restart service: restart
     - Since supercronic is PID 1, the entire container needs to be restarted
     - Use: docker restart trendradar

  5. Web server management:
     - Start: start_webserver
     - Stop: stop_webserver
     - Status: webserver_status
     - Access: http://localhost:8080
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    commands = {
        "run": manual_run,
        "status": show_status,
        "config": show_config,
        "files": show_files,
        "logs": show_logs,
        "restart": restart_supercronic,
        "start_webserver": start_webserver,
        "stop_webserver": stop_webserver,
        "webserver_status": webserver_status,
        "help": show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n👋 Operation cancelled")
        except Exception as e:
            print(f"❌ Execution error: {e}")
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py help' to view available commands")


if __name__ == "__main__":
    main()
