# Task: AI Summarization & Audio Narration

## Objective
Generate concise text summaries and audio narrations of video transcripts using OpenAI APIs (GPT-4 for summarization, TTS for audio).

## Acceptance Criteria
- [ ] Given transcript text, generate 3-5 sentence summary using GPT-4
- [ ] Summary captures key points and maintains factual accuracy
- [ ] Generate audio narration (MP3) of the summary using OpenAI TTS
- [ ] Audio file saved to local storage with unique filename
- [ ] Error handling for API failures and token limits
- [ ] Cost tracking/logging for API usage
- [ ] Unit tests verify summarization and TTS work

## Implementation Approach
1. Use OpenAI Python SDK
2. Create prompt template for summarization:
   - "Summarize the following YouTube video transcript in 3-5 sentences, focusing on key insights and main points."
3. Call GPT-4 API with transcript text
4. Call OpenAI TTS API with summary text
5. Save audio file with naming convention: `{video_id}_summary.mp3`
6. Return both summary text and audio file path

## Dependencies
- Blocked by: Project Setup, Transcript Extraction
- Blocks: Email Delivery
- Requires: OpenAI API key with GPT-4 and TTS access

## Estimated Effort
2-3 hours

## Subtasks
1. [ ] Create `src/summarizer.py` module
2. [ ] Implement `summarize_transcript(transcript, video_title)` function
3. [ ] Implement `generate_audio_narration(summary_text, output_path)` function
4. [ ] Add prompt engineering for optimal summaries
5. [ ] Handle long transcripts (GPT-4 token limits: 128k context)
6. [ ] Test with various transcript lengths and content types
7. [ ] Add cost estimation logging (GPT-4: ~$0.01-0.03/1k tokens, TTS: ~$15/1M chars)

## Notes
- GPT-4 Turbo recommended for cost efficiency
- TTS voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` (choose one)
- Audio format: MP3 for broad compatibility
- Consider chunking very long transcripts (>100k tokens) if needed
- Store audio files in `data/audio/` directory
