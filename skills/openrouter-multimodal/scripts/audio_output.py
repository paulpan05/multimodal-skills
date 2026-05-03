#!/usr/bin/env python3
"""Generate audio output from a chat model via OpenRouter.

Sends a text prompt to a model that can produce audio output and saves the
returned audio to a file. Audio output requires streaming (stream: true).

Default model is openai/gpt-4o-audio-preview since openrouter/auto does not
route to audio-output capable models.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request


def audio_output(
    prompt: str,
    model: str = "openai/gpt-4o-audio-preview",
    output: str = "output_audio.wav",
    voice: str = "alloy",
    audio_format: str = "pcm16",
    temperature: float = None,
    max_tokens: int = None,
):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build the messages payload requesting audio output
    # Audio output REQUIRES stream: true
    payload = {
        "model": model,
        "stream": True,
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": audio_format},
        "messages": [{"role": "user", "content": prompt}],
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    # Parse SSE stream to collect audio chunks
    audio_data_chunks = []
    transcript_chunks = []
    model_used = None
    usage_info = None

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            buffer = ""
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace")
                buffer += line

                if not line.strip():
                    # End of SSE event — process buffer
                    if buffer.startswith("data: "):
                        event_data = buffer[6:].strip()
                        buffer = ""
                        if event_data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(event_data)
                        except json.JSONDecodeError:
                            continue

                        if not model_used:
                            model_used = chunk.get("model", model)

                        # Extract audio and transcript from delta
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            audio = delta.get("audio", {})
                            if audio.get("data"):
                                audio_data_chunks.append(audio["data"])
                            if audio.get("transcript"):
                                transcript_chunks.append(audio["transcript"])

                        # Check for usage in final chunk
                        if chunk.get("usage"):
                            usage_info = chunk["usage"]
                    else:
                        buffer = ""

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    # Combine and save audio
    if audio_data_chunks:
        full_audio_b64 = "".join(audio_data_chunks)
        audio_bytes = base64.b64decode(full_audio_b64)
        with open(output, "wb") as f:
            f.write(audio_bytes)
        print(f"Saved audio: {output} ({len(audio_bytes)} bytes)")
    else:
        print("No audio data received from model.", file=sys.stderr)
        sys.exit(1)

    # Print transcript if available
    transcript = "".join(transcript_chunks)
    if transcript:
        print(f"\nTranscript: {transcript}")

    # Print usage info
    if usage_info:
        print(
            f"\n--- Model: {model_used} | Tokens: "
            f"{usage_info.get('prompt_tokens', '?')} prompt + "
            f"{usage_info.get('completion_tokens', '?')} completion, "
            f"cost: ${usage_info.get('total_cost', usage_info.get('cost', '?'))} ---",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate audio output from a chat model via OpenRouter"
    )
    parser.add_argument("prompt", help="Text prompt for audio generation")
    parser.add_argument("--model", "-m", default="openai/gpt-4o-audio-preview",
                        help="Model to use (default: openai/gpt-4o-audio-preview)")
    parser.add_argument("--output", "-o", default="output_audio.wav",
                        help="Output audio file path")
    parser.add_argument("--voice", "-v", default="alloy",
                        help="Voice: alloy, echo, fable, onyx, nova, shimmer")
    parser.add_argument("--format", "-f", default="pcm16",
                        help="Audio format: pcm16, mp3, flac, opus, aac (default: pcm16)")
    # Note: wav is not supported in streaming mode; pcm16 is raw PCM
    parser.add_argument("--temperature", "-t", type=float, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max tokens in response")
    args = parser.parse_args()

    audio_output(
        args.prompt, args.model, args.output, args.voice,
        args.format, args.temperature, args.max_tokens,
    )
