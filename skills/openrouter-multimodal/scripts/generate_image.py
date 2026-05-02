#!/usr/bin/env python3
"""Generate an image via OpenRouter and save to file."""

import argparse
import base64
import json
import os
import sys
import urllib.request


def generate_image(prompt: str, model: str = "google/gemini-2.5-flash-preview-image-generation",
                   aspect_ratio: str = "1:1", image_size: str = "1K",
                   output: str = "generated.png", modalities: list = None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if modalities is None:
        modalities = ["image", "text"]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": modalities,
    }

    if aspect_ratio != "1:1" or image_size != "1K":
        payload["image_config"] = {}
        if aspect_ratio != "1:1":
            payload["image_config"]["aspect_ratio"] = aspect_ratio
        if image_size != "1K":
            payload["image_config"]["image_size"] = image_size

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

    images = result.get("choices", [{}])[0].get("message", {}).get("images", [])
    if not images:
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"No images returned. Model response: {text[:500]}", file=sys.stderr)
        sys.exit(1)

    for i, img in enumerate(images):
        url = img.get("image_url", {}).get("url", "")
        if url.startswith("data:"):
            b64_data = url.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)
            out_path = output if len(images) == 1 else output.replace(".", f"_{i}.", 1)
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {out_path} ({len(img_bytes)} bytes)")
        else:
            print(f"Image {i}: {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate image via OpenRouter")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--model", default="google/gemini-2.5-flash-preview-image-generation")
    parser.add_argument("--aspect-ratio", default="1:1", help="1:1, 16:9, 9:16, etc.")
    parser.add_argument("--size", default="1K", help="0.5K, 1K, 2K, 4K")
    parser.add_argument("--output", "-o", default="generated.png", help="Output file path")
    args = parser.parse_args()
    generate_image(args.prompt, args.model, args.aspect_ratio, args.size, args.output)
