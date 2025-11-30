"""AI Summarization and Audio Narration module.

This module provides functions to generate concise restatements of YouTube video
transcripts using OpenAI GPT-4 and convert them to audio using OpenAI TTS.
The summarization approach focuses on restating the transcript content in a more
condensed form while preserving all key points and the speaker's perspective.

Cost Estimation:
- GPT-4 Turbo: ~$0.01/1K input tokens, ~$0.03/1K output tokens
- TTS: ~$15 per 1M characters (standard)

Average cost per video: ~$0.06-0.10 for summary + audio
"""

import logging
import os
from typing import Optional

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_TTS_VOICE

# Configure logging
logger = logging.getLogger(__name__)

# Lazily initialized OpenAI client
_client = None


def get_openai_client() -> OpenAI:
    """Get or create the OpenAI client instance.

    Returns:
        OpenAI client instance.

    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def summarize_transcript(
    transcript: str,
    video_title: str,
    video_url: Optional[str] = None
) -> str:
    """Generate a concise restatement of a YouTube video transcript.

    Uses OpenAI GPT-4 to create a 3-5 sentence restatement of
    the transcript content in a more concise form while preserving
    all key points and the speaker's perspective.

    Args:
        transcript: Full transcript text of the video.
        video_title: Title of the video.
        video_url: Optional YouTube URL for context.

    Returns:
        3-5 sentence concise restatement of the video content.

    Raises:
        Exception: If the OpenAI API call fails.
    """
    # Create prompt
    prompt = f"""You are restating the content of a YouTube video transcript for an email digest.

Video Title: {video_title}
{'Video URL: ' + video_url if video_url else ''}

Transcript:
{transcript}

Please restate everything discussed in this transcript in a more concise form:
1. Preserve all key points and information from the original
2. Condense redundancy, repetition, and unnecessary verbosity
3. Maintain the speaker's actual points and perspective
4. Present as a concise restatement (3-5 sentences) without adding interpretation

Restatement:"""

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at restating video content "
                               "concisely while preserving all key points."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()

        # Log token usage for cost tracking
        tokens_used = response.usage.total_tokens
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        # GPT-4 Turbo pricing: $0.01/1K input, $0.03/1K output
        estimated_cost = (input_tokens / 1000) * 0.01 + (output_tokens / 1000) * 0.03
        logger.info(
            f"Summarization: {tokens_used} tokens "
            f"(input: {input_tokens}, output: {output_tokens}), "
            f"~${estimated_cost:.4f}"
        )

        return summary

    except Exception as e:
        logger.error(f"Error summarizing transcript: {e}")
        raise


def generate_audio_narration(
    summary_text: str,
    video_id: str,
    output_dir: str = 'data/audio'
) -> str:
    """Generate audio narration of the summary using OpenAI TTS.

    Converts text summary to speech and saves as MP3 file.

    Args:
        summary_text: Text to convert to speech.
        video_id: YouTube video ID for unique filename.
        output_dir: Directory to save audio files (default: 'data/audio').

    Returns:
        Path to the generated audio file.

    Raises:
        Exception: If the OpenAI TTS API call fails.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create output filename
    output_path = os.path.join(output_dir, f"{video_id}_summary.mp3")

    try:
        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=OPENAI_TTS_VOICE,
            input=summary_text
        )

        # Save audio to file
        response.stream_to_file(output_path)

        # Log cost estimate
        # TTS pricing: $15 per 1M characters (standard)
        char_count = len(summary_text)
        estimated_cost = (char_count / 1_000_000) * 15
        logger.info(f"TTS: {char_count} characters, ~${estimated_cost:.6f}")

        logger.info(f"Audio narration saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating audio narration: {e}")
        raise


def create_summary_with_audio(
    transcript: str,
    video_title: str,
    video_id: str,
    video_url: Optional[str] = None,
    output_dir: str = 'data/audio'
) -> dict:
    """Generate both text summary and audio narration.

    Convenience function that combines text summarization and
    audio narration generation in a single call.

    Args:
        transcript: Full transcript text.
        video_title: Title of the video.
        video_id: YouTube video ID.
        video_url: Optional YouTube URL.
        output_dir: Directory to save audio files.

    Returns:
        Dictionary with 'summary' (str) and 'audio_path' (str).

    Raises:
        Exception: If either the summarization or TTS API call fails.
    """
    # Generate text summary
    summary = summarize_transcript(transcript, video_title, video_url)

    # Generate audio narration
    audio_path = generate_audio_narration(summary, video_id, output_dir)

    return {
        'summary': summary,
        'audio_path': audio_path
    }


def chunk_transcript(transcript: str, max_tokens: int = 100000) -> list[str]:
    """Split very long transcripts into chunks if needed.

    GPT-4 has a 128k token context window, but we use a conservative
    default to leave room for the prompt and response.

    Args:
        transcript: Full transcript text.
        max_tokens: Maximum tokens per chunk (default: 100000).

    Returns:
        List of transcript chunks.
    """
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4

    if len(transcript) <= max_chars:
        return [transcript]

    # Split into sentences and group into chunks
    sentences = transcript.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    separator_length = 2  # Length of '. '

    for sentence in sentences:
        sentence_length = len(sentence)
        # Account for separator when calculating if we'd exceed max_chars
        additional_length = sentence_length
        if current_chunk:
            additional_length += separator_length

        if current_length + additional_length > max_chars and current_chunk:
            # Join sentences and only add period if chunk doesn't already end with one
            chunk_text = '. '.join(current_chunk)
            if not chunk_text.endswith('.'):
                chunk_text += '.'
            chunks.append(chunk_text)
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += additional_length

    if current_chunk:
        # Join sentences and only add period if chunk doesn't already end with one
        chunk_text = '. '.join(current_chunk)
        if not chunk_text.endswith('.'):
            chunk_text += '.'
        chunks.append(chunk_text)

    return chunks


def summarize_long_transcript(
    transcript: str,
    video_title: str,
    video_url: Optional[str] = None
) -> str:
    """Summarize very long transcripts by chunking and then combining summaries.

    For transcripts that exceed the token limit, this function:
    1. Splits the transcript into manageable chunks
    2. Summarizes each chunk separately
    3. Combines the chunk summaries and creates a final summary

    Args:
        transcript: Full transcript text.
        video_title: Title of the video.
        video_url: Optional YouTube URL.

    Returns:
        Final 3-5 sentence summary of the entire video.

    Raises:
        Exception: If any OpenAI API call fails.
    """
    chunks = chunk_transcript(transcript)

    if len(chunks) == 1:
        return summarize_transcript(transcript, video_title, video_url)

    # Summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Summarizing chunk {i + 1}/{len(chunks)}")
        summary = summarize_transcript(chunk, f"{video_title} (Part {i + 1})")
        chunk_summaries.append(summary)

    # Combine and re-summarize
    combined = '\n\n'.join(chunk_summaries)
    final_summary = summarize_transcript(combined, video_title, video_url)

    return final_summary
