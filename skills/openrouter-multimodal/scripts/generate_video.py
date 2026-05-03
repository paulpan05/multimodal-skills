#!/usr/bin/env python3
"""Generate video via OpenRouter (async: submit, poll, download).

Supports text-to-video and image-to-video (first/last frame).
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request


def _encode_image_file(path: str) -> str:
    """Read a local image file and return a base64 data URI."""
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def submit_video_job(prompt: str, model: str = "bytedance/seedance-2.0",
                     resolution: str = "720p", aspect_ratio: str = "16:9",
                     duration: int = None, callback_url: str = None,
                     frame_images: list = None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = {"model": model, "prompt": prompt, "resolution": resolution, "aspect_ratio": aspect_ratio}
    if duration:
        payload["duration"] = duration
    if callback_url:
        payload["callback_url"] = callback_url
    if frame_images:
        payload["frame_images"] = frame_images

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/videos",
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

    job_id = result.get("id")
    status = result.get("status")
    print(f"Job submitted: {job_id} (status: {status})")
    return job_id


def poll_job(job_id: str, interval: int = 30, max_wait: int = 600):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    elapsed = 0
    while elapsed < max_wait:
        req = urllib.request.Request(
            f"https://openrouter.ai/api/v1/videos/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"Poll error HTTP {e.code}", file=sys.stderr)
            time.sleep(interval)
            elapsed += interval
            continue

        status = result.get("status")
        print(f"[{elapsed}s] Status: {status}")

        if status == "completed":
            return result
        elif status in ("failed", "error"):
            print(f"Job failed: {json.dumps(result)}", file=sys.stderr)
            sys.exit(1)

        time.sleep(interval)
        elapsed += interval

    print(f"Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_content(job_id: str, output: str):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    req = urllib.request.Request(
        f"https://openrouter.ai/api/v1/videos/{job_id}/content",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(output, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    print(f"Downloaded: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate video via OpenRouter")
    parser.add_argument("prompt", help="Video generation prompt")
    parser.add_argument("--model", default="bytedance/seedance-2.0")
    parser.add_argument("--resolution", default="720p", help="480p, 720p, 1080p")
    parser.add_argument("--aspect-ratio", default="16:9", help="16:9, 9:16, 1:1")
    parser.add_argument("--duration", type=int, help="Duration in seconds")
    parser.add_argument("--output", "-o", default="generated.mp4", help="Output file path")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between polls")
    parser.add_argument("--max-wait", type=int, default=600, help="Max seconds to wait")
    parser.add_argument("--job-id", help="Skip submit, poll existing job ID")
    img_group = parser.add_argument_group("image-to-video")
    img_group.add_argument("--image", help="Local image file to use as a frame (base64-encoded)")
    img_group.add_argument("--image-url", help="Image URL to use as a frame")
    img_group.add_argument("--frame-type", default="first_frame",
                           choices=["first_frame", "last_frame"],
                           help="Whether image is the first or last frame (default: first_frame)")
    args = parser.parse_args()

    # Build frame_images if an image is provided
    frame_images = None
    if args.image or args.image_url:
        image_url = args.image_url if args.image_url else _encode_image_file(args.image)
        frame_images = [{
            "type": "image_url",
            "image_url": {"url": image_url},
            "frame_type": args.frame_type,
        }]

    job_id = args.job_id or submit_video_job(
        args.prompt, args.model, args.resolution, args.aspect_ratio, args.duration,
        frame_images=frame_images,
    )
    result = poll_job(job_id, args.poll_interval, args.max_wait)
    download_content(job_id, args.output)
