#!/usr/bin/env python3
"""Generate audio output from a chat model via OpenRouter.

Sends a text prompt to a model that can produce audio output and saves the
returned audio to a file. Supports models that return audio as part of their
chat completion response.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request


def audio_output(
    prompt: str,
    model: str = "openrouter/auto",
    output: str = "output_audio.wav",
    voice: str = "alloy",
    audio_format: str = "wav",
    temperature: float = None,
    max_tokens: int = None,
):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build the messages payload requesting audio output
    payload = {
        "model": model,
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

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    # Extract audio from the response
    choices = result.get("choices", [])
    if not choices:
        print("No response from model.", file=sys.stderr)
        sys.exit(1)

    message = choices[0].get("message", {})

    # Check for audio in the response
    audio_data = message.get("audio", {})
    audio_id = audio_data.get("id")

    if audio_id:
        # The audio content may be returned as base64 data
        audio_b64 = audio_data.get("data")
        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            with open(output, "wb") as f:
                f.write(audio_bytes)
            print(f"Saved audio: {output} ({len(audio_bytes)} bytes)")
        else:
            print(f"Audio ID returned: {audio_id}", file=sys.stderr)
            print("No inline audio data. Check if the model requires a separate fetch.", file=sys.stderr)
            # Print any text content as well
            text = message.get("content", "")
            if text:
                print(f"\nModel text response:\n{text}")
    else:
        # Fallback: check if audio is in a different location in the response
        content_parts = message.get("content", "")
        if isinstance(content_parts, list):
            for part in content_parts:
                if isinstance(part, dict) and part.get("type") == "input_audio":
                    b64_data = part.get("input_audio", {}).get("data", "")
                    if b64_data:
                        audio_bytes = base64.b64decode(b64_data)
                        with open(output, "wb") as f:
                            f.write(audio_bytes)
                        print(f"Saved audio: {output} ({len(audio_bytes)} bytes)")
                        break
            else:
                print("No audio data found in response.", file=sys.stderr)
                if isinstance(content_parts, str) and content_parts:
                    print(f"\nModel text response:\n{content_parts}")
                sys.exit(1)
        else:
            print("No audio data found in response.", file=sys.stderr)
            if isinstance(content_parts, str) and content_parts:
                print(f"\nModel text response:\n{content_parts}")
            sys.exit(1)

    # Print usage info to stderr
    usage = result.get("usage", {})
    if usage:
        print(
            f"\n--- Usage: {usage.get('prompt_tokens', '?')} prompt + "
            f"{usage.get('completion_tokens', '?')} completion tokens, "
            f"cost: ${usage.get('total_cost', usage.get('cost', '?'))} ---",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate audio output from a chat model via OpenRouter"
    )
    parser.add_argument("prompt", help="Text prompt for audio generation")
    parser.add_argument("--model", "-m", default="openrouter/auto",
                        help="Model to use (default: openrouter/auto)")
    parser.add_argument("--output", "-o", default="output_audio.wav",
                        help="Output audio file path")
    parser.add_argument("--voice", "-v", default="alloy",
                        help="Voice: alloy, echo, fable, onyx, nova, shimmer")
    parser.add_argument("--format", "-f", default="wav",
                        help="Audio format: wav, mp3, flac, opus, aac (default: wav)")
    parser.add_argument("--temperature", "-t", type=float, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max tokens in response")
    args = parser.parse_args()

    audio_output(
        args.prompt, args.model, args.output, args.voice,
        args.format, args.temperature, args.max_tokens,
    )
