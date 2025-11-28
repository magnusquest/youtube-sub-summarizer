# Task: Email Delivery System

## Objective
Send formatted emails with video summary text and audio narration attachment via SMTP.

## Acceptance Criteria
- [ ] Email sent successfully via SMTP (Gmail, SendGrid, or other)
- [ ] Email contains well-formatted HTML with video title, channel, link, summary
- [ ] Audio file attached as MP3
- [ ] Email subject line is descriptive: "[Channel Name] - Video Title Summary"
- [ ] Error handling for SMTP failures with retry logic
- [ ] Configuration supports multiple SMTP providers
- [ ] Unit tests verify email composition and sending

## Implementation Approach
1. Use Python's `smtplib` and `email` libraries
2. Create HTML email template with:
   - Video thumbnail (optional)
   - Channel name
   - Video title (with link to YouTube)
   - Summary text
   - Audio player hint (attachment)
3. Attach MP3 audio file
4. Configure SMTP with TLS/SSL
5. Add retry logic for transient failures

## Dependencies
- Blocked by: Project Setup, AI Summarization
- Blocks: Main Pipeline
- Requires: SMTP server credentials

## Estimated Effort
2-3 hours

## Subtasks
1. [ ] Create `src/email_sender.py` module
2. [ ] Implement `EmailSender` class with SMTP configuration
3. [ ] Create HTML email template
4. [ ] Implement `send_summary_email(video_data, summary, audio_path)` method
5. [ ] Add audio file attachment functionality
6. [ ] Test with real email account (send test email)
7. [ ] Add retry logic (3 attempts with exponential backoff)

## Notes
- Gmail requires "App Password" if 2FA enabled
- Consider using SendGrid for better deliverability
- HTML template should be responsive (mobile-friendly)
- Audio attachment size limit: most SMTP servers allow 10-25MB
- OpenAI TTS audio files typically small (<1MB for short summaries)
