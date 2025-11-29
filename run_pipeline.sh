#!/bin/bash
# YouTube Subscription Summarizer - Cron Wrapper Script
#
# This script is designed to be called by cron for automated pipeline execution.
# It handles virtual environment activation and logging.
#
# Usage:
#   ./run_pipeline.sh           # Normal execution
#   ./run_pipeline.sh --dry-run # Dry run (no emails sent)
#
# Cron example (hourly at minute 0):
#   0 * * * * /path/to/youtube-sub-summarizer/run_pipeline.sh
#
# Alternative cron schedules:
#   0 */2 * * * /path/to/run_pipeline.sh  # Every 2 hours
#   0 */6 * * * /path/to/run_pipeline.sh  # Every 6 hours
#   0 9 * * * /path/to/run_pipeline.sh    # Daily at 9 AM
#   0 9,18 * * * /path/to/run_pipeline.sh # Twice daily (9 AM and 6 PM)

set -e

# Change to script directory (repository root)
cd "$(dirname "$0")"

# Ensure logs directory exists
mkdir -p logs

# Log script start time
echo "=== Cron wrapper started at $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> logs/cron.log

# Activate virtual environment (try common names)
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Warning: No virtual environment found, using system Python" >> logs/cron.log
fi

# Run pipeline with any arguments passed to this script
# Output is appended to cron.log, errors included
python -m src.main "$@" >> logs/cron.log 2>&1

EXIT_CODE=$?

# Log script end time
echo "=== Cron wrapper finished at $(date -u +"%Y-%m-%dT%H:%M:%SZ") with exit code ${EXIT_CODE} ===" >> logs/cron.log
echo "" >> logs/cron.log

# Exit with pipeline exit code
exit $EXIT_CODE
