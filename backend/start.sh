#!/bin/sh
set -e

# Run Grafana Alloy in the background only if remote write URL is provided
if [ -n "$GRAFANA_CLOUD_REMOTE_WRITE_URL" ]; then
    echo "Starting Grafana Alloy..."
    export ALLOY_DISABLE_REPORTING=true
    export GOMEMLIMIT=100MiB
    alloy run /app/config.alloy > /dev/null 2>&1 &
fi

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
