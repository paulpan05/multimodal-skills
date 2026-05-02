#!/usr/bin/env python3
"""Speech-to-text via OpenRouter. Transcribes audio file to text."""

import argparse
import base64
import json
import os
import sys
import urllib.request


def stt(audio_path: str, model: str = "openai/whisper-1", language: str = None,
        format: str = None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    # Detect format from extension
    if format is None:
        ext = os.path.splitext(audio_path)[1].lstrip(".")
        format_map = {"mp3": "mp3", "wav": "wav", "flac": "flac", "m4a": "m4a",
                      "ogg": "ogg", "webm": "webm", "aac": "aac"}
        format = format_map.get(ext.lower(), "wav")

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": model,
        "input_audio": {"data": audio_b64, "format": format},
    }
    if language:
        payload["language"] = language

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/audio/transcriptions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    print(result.get("text", ""))
    usage = result.get("usage", {})
    if usage:
        print(f"\n--- Usage: {usage.get('seconds', '?')}s audio, cost: ${usage.get('cost', '?')} ---",
              file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STT via OpenRouter")
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument("--model", default="openai/whisper-1")
    parser.add_argument("--language", help="ISO-639-1 code (auto-detect if omitted)")
    parser.add_argument("--format", help="Audio format (auto-detected from extension)")
    args = parser.parse_args()
    stt(args.audio, args.model, args.language, args.format)
