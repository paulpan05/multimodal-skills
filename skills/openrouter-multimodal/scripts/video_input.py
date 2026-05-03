#!/usr/bin/env python3
"""Send video input to a chat model via OpenRouter for analysis/description.

Supports video URLs (YouTube, direct links) and local video files (base64-encoded).
"""

import argparse
import base64
import json
import os
import sys
import urllib.request


def video_input(prompt: str, video_source: str, model: str = "google/gemini-2.5-flash",
                system_prompt: str = None, max_tokens: int = None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build video content part
    if os.path.exists(video_source):
        # Local file — base64 encode
        ext = os.path.splitext(video_source)[1].lstrip(".")
        mime_map = {"mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
                    "avi": "video/x-msvideo", "mkv": "video/x-matroska", "m4v": "video/mp4"}
        mime_type = mime_map.get(ext.lower(), "video/mp4")
        with open(video_source, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        video_url = f"data:{mime_type};base64,{b64_data}"
    elif video_source.startswith("http://") or video_source.startswith("https://"):
        video_url = video_source
    else:
        print(f"Error: '{video_source}' is not a valid URL or existing file path", file=sys.stderr)
        sys.exit(1)

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Best practice: text prompt before video content
    user_content = [
        {"type": "text", "text": prompt},
        {"type": "video_url", "video_url": {"url": video_url}},
    ]
    messages.append({"role": "user", "content": user_content})

    payload = {"model": model, "messages": messages}
    if max_tokens:
        payload["max_tokens"] = max_tokens

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(text)

    usage = result.get("usage", {})
    if usage:
        model_used = result.get("model", "?")
        print(f"\n--- Model: {model_used} | Tokens: {usage.get('total_tokens', '?')} "
              f"(prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}) "
              f"| Cost: ${usage.get('total_cost', '?')} ---", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send video to a chat model via OpenRouter")
    parser.add_argument("prompt", help="Text prompt / question about the video")
    parser.add_argument("video", help="Video URL or local file path")
    parser.add_argument("--model", default="openrouter/auto",
                        help="Chat model with multimodal understanding (default: openrouter/auto)")
    parser.add_argument("--system", help="Optional system prompt")
    parser.add_argument("--max-tokens", type=int, help="Max response tokens")
    args = parser.parse_args()
    video_input(args.prompt, args.video, args.model, args.system, args.max_tokens)
