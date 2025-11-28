# Task: Main Pipeline & Scheduler Deployment

## Objective
Integrate all components into a main processing pipeline and deploy as an hourly cron job.

## Acceptance Criteria
- [ ] `main.py` orchestrates entire pipeline: fetch → extract → summarize → email
- [ ] Pipeline processes all new videos from subscriptions
- [ ] Logging tracks execution: start time, videos processed, errors
- [ ] Cron job configured to run every hour
- [ ] Error handling prevents pipeline crashes
- [ ] Documentation for deployment and monitoring
- [ ] Dry-run mode for testing without sending emails

## Implementation Approach
1. Create `src/main.py` with pipeline logic:
   ```python
   def run_pipeline():
       # 1. Get subscriptions
       # 2. Get recent videos from each channel
       # 3. Filter out already-processed videos
       # 4. For each new video:
       #    a. Extract transcript
       #    b. Generate summary & audio
       #    c. Send email
       #    d. Mark as processed
       # 5. Log summary statistics
   ```
2. Add comprehensive logging
3. Create shell script wrapper for cron
4. Configure cron job: `0 * * * * /path/to/run_pipeline.sh`
5. Add monitoring/alerting for failures

## Dependencies
- Blocked by: All other tasks
- Blocks: None (final task)
- Requires: All components integrated

## Estimated Effort
3-4 hours

## Subtasks
1. [ ] Create `src/main.py` with `run_pipeline()` function
2. [ ] Integrate all components (YouTube, transcript, AI, email, database)
3. [ ] Add comprehensive logging (file + console)
4. [ ] Implement dry-run mode (`--dry-run` flag)
5. [ ] Create `run_pipeline.sh` wrapper script
6. [ ] Configure cron job (`crontab -e`)
7. [ ] Test end-to-end with real subscriptions
8. [ ] Document deployment steps in README.md
9. [ ] Add monitoring: daily summary email or log rotation

## Notes
- Cron syntax: `0 * * * *` = every hour at minute 0
- Shell script should activate venv and set working directory
- Example wrapper script:
  ```bash
  #!/bin/bash
  cd /path/to/youtube-sub-summarizer
  source venv/bin/activate
  python src/main.py >> logs/cron.log 2>&1
  ```
- Consider adding command-line flags: `--dry-run`, `--verbose`, `--test-channel`
- Log rotation: use `logrotate` or Python's `RotatingFileHandler`
