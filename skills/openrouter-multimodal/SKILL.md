---
name: openrouter-multimodal
description: "Generate images, video, audio (TTS/STT), and process multimodal content via OpenRouter's unified API. Trigger when user wants to generate images, video, TTS, STT, or send multimodal inputs (images, PDFs, audio, video) to models through OpenRouter."
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [OpenRouter, Image-Generation, Video-Generation, TTS, STT, Multimodal, API]
    homepage: https://openrouter.ai/docs
prerequisites:
  env_vars: [OPENROUTER_API_KEY]
---

# OpenRouter Multimodal API

Generate images, video, audio, and process multimodal content through OpenRouter's unified API with a single API key.

## Prerequisites

1. **OpenRouter API key** — get one at https://openrouter.ai/settings/keys
2. Set `OPENROUTER_API_KEY` in `~/.hermes/.env` or export in shell

## API Base URL

```
https://openrouter.ai/api/v1
```

## Authentication

All requests require:
```
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json
```

## Scripts

- `scripts/generate_image.py` — Generate image and save to file
- `scripts/generate_video.py` — Submit video gen job, poll, download
- `scripts/tts.py` — Text-to-speech, save audio file
- `scripts/stt.py` — Speech-to-text from audio file

## Quick Reference

### Image Generation

```bash
# Generate an image via chat completions
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash-image",
    "messages": [{"role": "user", "content": "A sunset over mountains"}],
    "modalities": ["image", "text"]
  }'
```

Response: `choices[0].message.images[i].image_url.url` (base64 data URL, typically PNG)

**Image config options** (add to payload):
```json
"image_config": {
  "aspect_ratio": "16:9",   // 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
  "image_size": "2K"         // 0.5K, 1K (default), 2K, 4K
}
```

**Image generation models** (verify with API — models change):
- `google/gemini-3.1-flash-image-preview` — extended aspect ratios, 0.5K–4K
- `google/gemini-2.5-flash-image` — standard
- `black-forest-labs/flux.2-pro` — image-only output
- `black-forest-labs/flux.2-flex` — image-only output
- `sourceful/riverflow-v2-standard-preview` — font inputs, super resolution

**Discover image models:**
```bash
curl -s "https://openrouter.ai/api/v1/models?output_modalities=image" | jq '.data[].id'
```

### Video Generation (Async)

Video generation is **asynchronous** — submit, get job ID, poll until done, then download.

```bash
# 1. Submit
JOB=$(curl -s https://openrouter.ai/api/v1/videos \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/veo-3.1",
    "prompt": "A golden retriever playing on a beach",
    "resolution": "720p",
    "aspect_ratio": "16:9"
  }')
JOB_ID=$(echo "$JOB" | jq -r '.id')

# 2. Poll every ~30s until status is "completed"
curl -s "https://openrouter.ai/api/v1/videos/$JOB_ID" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# 3. Download content
curl -s "https://openrouter.ai/api/v1/videos/$JOB_ID/content" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -o video.mp4
```

**Image-to-video** (provide first/last frame):
```json
"frame_images": [
  {"type": "image_url", "image_url": {"url": "https://example.com/frame.png"}, "frame_type": "first_frame"}
]
```

**Discover video models:**
```bash
curl -s "https://openrouter.ai/api/v1/videos/models" | jq '.[].id'
```

### Text-to-Speech (TTS)

Dedicated endpoint — returns **raw audio bytes** (not JSON).

```bash
curl -s https://openrouter.ai/api/v1/audio/speech \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini-tts-2025-12-15",
    "input": "Hello world, this is a test.",
    "voice": "alloy",
    "response_format": "mp3"
  }' -o speech.mp3
```

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `model` | Yes | TTS model slug |
| `input` | Yes | Text to synthesize |
| `voice` | Yes | Voice ID (varies by model: alloy, echo, fable, onyx, nova, shimmer) |
| `response_format` | No | `mp3` or `pcm` (default: pcm) |
| `speed` | No | Playback speed (1.0 default, OpenAI only) |

**Discover TTS models:**
```bash
curl -s "https://openrouter.ai/api/v1/models?output_modalities=speech" | jq '.data[].id'
```

### Speech-to-Text (STT)

Dedicated endpoint — returns JSON with transcribed text.

```bash
# Encode audio first
AUDIO_B64=$(base64 -w0 audio.wav)

curl -s https://openrouter.ai/api/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"openai/whisper-1\",
    \"input_audio\": {\"data\": \"$AUDIO_B64\", \"format\": \"wav\"}
  }"
```

**Response:** `{ "text": "...", "usage": { "seconds": N, "cost": N } }`

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `model` | Yes | STT model slug |
| `input_audio.data` | Yes | Base64-encoded audio (raw bytes, NOT data URI) |
| `input_audio.format` | Yes | `wav`, `mp3`, `flac`, `m4a`, `ogg`, `webm`, `aac` |
| `language` | No | ISO-639-1 code (auto-detected if omitted) |

**Discover STT models:**
```bash
curl -s "https://openrouter.ai/api/v1/models?output_modalities=transcription" | jq '.data[].id'
```

### Sending Multimodal Inputs to Chat Models

All via `/api/v1/chat/completions` with content arrays in messages:

```python
# Image input
{"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}}
# or base64: {"url": "data:image/jpeg;base64,..."}

# PDF input
{"type": "file", "file": {"filename": "doc.pdf", "file_data": "https://example.com/doc.pdf"}}
# or base64: {"file_data": "data:application/pdf;base64,..."}

# Audio input (base64 only, no URLs)
{"type": "input_audio", "input_audio": {"data": "<base64>", "format": "wav"}}

# Video input
{"type": "video_url", "video_url": {"url": "https://youtube.com/watch?v=..."}}
# or base64: {"url": "data:video/mp4;base64,..."}
```

## Tips

- **Best practice**: Send text prompt BEFORE images/other content in the messages array
- **Multiple modalities** can be mixed in a single request
- **Video gen polling**: poll every ~30s; generation takes 30s to several minutes
- **Image response**: always base64 data URL; decode and save as PNG/JPEG
- **Streaming image gen**: set `"stream": true`, parse SSE chunks for `delta.images`
- **PDF parsing**: use `plugins: [{"id": "file-parser", "pdf": {"engine": "cloudflare-ai"}}]` for free parsing
- **Model discovery**: always verify current model slugs via the models API — models change frequently

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 401 Unauthorized | Check `OPENROUTER_API_KEY` is set and valid |
| Model not found | Verify slug via `curl .../models?output_modalities=...` |
| No image in response | Ensure `"modalities": ["image", "text"]` is in payload |
| Video still pending | Generation takes 30s–minutes; keep polling |
| Audio input rejected | Must be base64-encoded; URLs not supported for audio |
| Poor image quality | Use `image_config.image_size: "2K"` or `"4K"` |
| Gemini video URL fails | Use YouTube links for AI Studio, base64 for Vertex AI |
