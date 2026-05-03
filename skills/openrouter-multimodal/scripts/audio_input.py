#!/usr/bin/env python3
"""Send audio as input to a chat model via OpenRouter for analysis/transcription.

Supports sending an audio file (base64-encoded) along with a text prompt to any
OpenRouter chat model that accepts audio input. Returns the model's text response.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request


def audio_input(
    audio_path: str,
    prompt: str = "Please transcribe and describe this audio.",
    model: str = "openrouter/auto",
    audio_format: str = None,
    temperature: float = None,
    max_tokens: int = None,
):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    # Detect format from extension
    if audio_format is None:
        ext = os.path.splitext(audio_path)[1].lstrip(".")
        format_map = {
            "mp3": "mp3", "wav": "wav", "flac": "flac", "m4a": "m4a",
            "ogg": "ogg", "webm": "webm", "aac": "aac",
        }
        audio_format = format_map.get(ext.lower(), "wav")

    # Read and base64-encode the audio file
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Build the messages payload with audio input content
    content = [
        {"type": "text", "text": prompt},
        {
            "type": "input_audio",
            "input_audio": {"data": audio_b64, "format": audio_format},
        },
    ]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
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

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    # Extract and print the model's text response
    choices = result.get("choices", [])
    if not choices:
        print("No response from model.", file=sys.stderr)
        sys.exit(1)

    message = choices[0].get("message", {})
    text = message.get("content", "")
    print(text)

    # Print usage info to stderr
    usage = result.get("usage", {})
    if usage:
        print(
            f"\n--- Usage: {usage.get('prompt_tokens', '?')} prompt + "
            f"{usage.get('completion_tokens', '?')} completion tokens, "
            f"cost: ${usage.get('total_cost', usage.get('cost', '?'))} ---",
            file=sys.stderr,
        )

    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send audio as input to a chat model via OpenRouter"
    )
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument(
        "--prompt", "-p",
        default="Please transcribe and describe this audio.",
        help="Text prompt to accompany the audio",
    )
    parser.add_argument("--model", "-m", default="openrouter/auto",
                        help="Model to use (default: openrouter/auto)")
    parser.add_argument("--format", "-f", dest="audio_format",
                        help="Audio format: wav, mp3, flac, m4a, ogg, webm, aac (auto-detected)")
    parser.add_argument("--temperature", "-t", type=float, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max tokens in response")
    args = parser.parse_args()

    audio_input(
        args.audio, args.prompt, args.model, args.audio_format,
        args.temperature, args.max_tokens,
    )
