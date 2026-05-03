#!/usr/bin/env python3
"""Send an image to a vision model via OpenRouter and get a text response."""

import argparse
import base64
import json
import os
import sys
import urllib.request


def image_input(image_path: str, prompt: str = "Describe this image.",
                model: str = "openrouter/auto", detail: str = "auto"):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Read and base64-encode the image
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lstrip(".").lower()
    mime_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/png")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{img_b64}",
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    }

    # Include detail level if not default
    if detail != "auto":
        payload["messages"][0]["content"][0]["image_url"]["detail"] = detail

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

    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not text:
        print("No text response returned.", file=sys.stderr)
        sys.exit(1)

    print(text)

    usage = result.get("usage", {})
    if usage:
        print(f"\n--- Usage: {usage.get('prompt_tokens', '?')} prompt + "
              f"{usage.get('completion_tokens', '?')} completion tokens, "
              f"cost: ${usage.get('total_cost', usage.get('cost', '?'))} ---",
              file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send image to vision model via OpenRouter")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--prompt", "-p", default="Describe this image.",
                        help="Prompt to send with the image")
    parser.add_argument("--model", default="openrouter/auto",
                        help="Vision model to use")
    parser.add_argument("--detail", default="auto",
                        help="Image detail level: auto, low, high")
    args = parser.parse_args()
    image_input(args.image, args.prompt, args.model, args.detail)
