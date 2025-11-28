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
