#!/usr/bin/env python3
"""Text-to-speech via OpenRouter. Saves raw audio to file."""

import argparse
import json
import os
import sys
import urllib.request


def tts(input_text: str, model: str = "openai/gpt-4o-mini-tts-2025-12-15",
        voice: str = "alloy", response_format: str = "mp3",
        speed: float = 1.0, output: str = "speech.mp3"):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": model,
        "input": input_text,
        "voice": voice,
        "response_format": response_format,
    }
    if speed != 1.0:
        payload["speed"] = speed

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/audio/speech",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content_type = resp.headers.get("Content-Type", "")
            audio_bytes = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    with open(output, "wb") as f:
        f.write(audio_bytes)

    print(f"Saved: {output} ({len(audio_bytes)} bytes, content-type: {content_type})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TTS via OpenRouter")
    parser.add_argument("input", help="Text to synthesize")
    parser.add_argument("--model", default="openai/gpt-4o-mini-tts-2025-12-15")
    parser.add_argument("--voice", default="alloy", help="alloy, echo, fable, onyx, nova, shimmer")
    parser.add_argument("--format", default="mp3", help="mp3 or pcm")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed")
    parser.add_argument("--output", "-o", default="speech.mp3", help="Output file path")
    args = parser.parse_args()
    tts(args.input, args.model, args.voice, args.format, args.speed, args.output)
