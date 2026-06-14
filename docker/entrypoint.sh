#!/bin/bash
set -e

# Check configuration file
if [ ! -f "/app/config/config.yaml" ] || [ ! -f "/app/config/frequency_words.txt" ]; then
    echo "❌ Configuration file is missing"
    exit 1
fi

case "${RUN_MODE:-cron}" in
"once")
    echo "🔄 single execution"
    exec python -m trendradar
    ;;
"cron")
    # Verify CRON_SCHEDULE format (only legal characters in cron expression are allowed)
    CRON_EXPR="${CRON_SCHEDULE:-*/30 * * * *}"
    if ! echo "$CRON_EXPR" | grep -qE '^[0-9*/,[:space:]-]+$'; then
        echo "❌ CRON_SCHEDULE format is illegal: $CRON_EXPR"
        exit 1
    fi

    # Generate crontab
    echo "$CRON_EXPR cd /app && python -m trendradar" > /tmp/crontab
    
    echo "📅 Generated crontab content:"
    cat /tmp/crontab

    if ! /usr/local/bin/supercronic -test /tmp/crontab; then
        echo "❌ crontab format verification failed"
        exit 1
    fi

    # Execute once immediately (if configured)
    if [ "${IMMEDIATE_RUN:-false}" = "true" ]; then
        echo "▶️ Execute once immediately"
        python -m trendradar
    fi

    # Start the web server
    echo "🌐 Start web server..."
    python manage.py start_webserver

    echo "⏰ Start supercronic: $CRON_EXPR"
    echo "🎯 supercronic will run as PID 1"

    exec /usr/local/bin/supercronic -passthrough-logs /tmp/crontab
    ;;
*)
    exec "$@"
    ;;
esac
