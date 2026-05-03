#!/usr/bin/env python3
"""Send a PDF document to a model via OpenRouter and get a text response."""

import argparse
import base64
import json
import os
import sys
import urllib.request


def pdf_input(pdf_path: str, prompt: str = "Summarize this document.",
              model: str = "openrouter/auto"):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Read and base64-encode the PDF
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "file",
                        "file": {
                            "file_data": {
                                "url": f"data:application/pdf;base64,{pdf_b64}",
                            },
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
        with urllib.request.urlopen(req, timeout=180) as resp:
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
    parser = argparse.ArgumentParser(description="Send PDF to model via OpenRouter")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--prompt", "-p", default="Summarize this document.",
                        help="Prompt to send with the PDF")
    parser.add_argument("--model", default="openrouter/auto",
                        help="Model to use (must support PDF input)")
    args = parser.parse_args()
    pdf_input(args.pdf, args.prompt, args.model)
