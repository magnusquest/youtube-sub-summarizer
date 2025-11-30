# Project Intent: YouTube Subscription Summarizer

## Vision
Transform overwhelming YouTube subscription feeds into digestible email summaries. Instead of watching every video or missing important content, receive AI-generated summaries of each new video from subscribed channels, enabling efficient information filtering and time-saving consumption.

## Core Values
- **Simplicity**: Email delivery, no complex UI needed for v1
- **Efficiency**: Automated processing, minimal user intervention
- **Privacy**: Self-hosted option, user controls their own data
- **Extensibility**: Architecture should support future multi-user deployment

## Constraints
- **User Scope**: Primary user is you, but design for self-hosted deployment by others
- **Delivery**: Email-based summaries (one email per new video)
- **Infrastructure**: Self-hosted, can run on personal machine/server
- **Cost**: Minimize API costs (YouTube API quotas, AI summarization costs)

## Success Metrics
- [ ] Automatically detects new videos from all subscribed channels
- [ ] Generates accurate, concise summaries of video content
- [ ] Delivers summaries via email within reasonable time of video publication
- [ ] Runs reliably without manual intervention
- [ ] Easy to deploy and configure for other users

## Context
User subscribes to multiple YouTube channels and wants to stay informed without watching every video. Current state: manually checking subscriptions or relying on YouTube's algorithmic recommendations (which may miss content). Desired state: proactive, comprehensive email digest of all new content with AI summaries.

## Decision Log
- 2025-11-27: Initial intent established - email-first, self-hosted, single-user with multi-user potential
- 2025-11-27: Chosen implementation approach - YouTube Data API polling (hourly), caption-based transcripts, OpenAI GPT-4 + TTS, SMTP email delivery
- 2025-11-27: Created task breakdown in `docs/ideas/email-digest-system/` with 7 implementation tasks
- 2025-11-27: Created GitHub repository at https://github.com/magnusquest/youtube-sub-summarizer
- 2025-11-27: Created Issue #1 - Project Setup & Configuration (first task, blocks all others)
- 2025-11-28: Completed Issue #1 (Project Setup) - established project structure, dependencies, configuration management
- 2025-11-28: Completed Issue #3 (YouTube Data API Integration) - implemented YouTubeClient with quota tracking and retry logic
- 2025-11-28: Completed Issue #4 (Video Transcript Extraction) - implemented transcript.py with multi-language support
- 2025-11-29: Completed Issue #5 (AI Summarization & Audio Narration) - implemented GPT-4 summarization and OpenAI TTS integration
- 2025-11-29: Completed Issue #6 (Email Delivery System) - implemented SMTP email delivery with HTML templates and audio attachments
- 2025-11-29: Completed Issue #7 (State Management & Video Tracking) - implemented SQLite database for tracking processed videos
- 2025-11-29: Completed Issue #8 (Main Pipeline & Scheduler Deployment) - integrated all components into main.py with CLI interface and cron wrapper script
- 2025-11-29: All 7 core implementation tasks completed - system is fully functional and ready for deployment
- 2025-11-29: Created Issue #18 - Improve summarization prompt to restate transcript content concisely rather than describing/interpreting
