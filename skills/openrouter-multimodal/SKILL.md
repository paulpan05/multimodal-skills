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

## Scripts

The preferred way to use this skill. Each script handles auth, API calls, base64 encoding/decoding, polling, and error handling automatically.

- `scripts/generate_image.py` — Generate image and save to file
- `scripts/generate_video.py` — Submit video gen job, poll, download
- `scripts/tts.py` — Text-to-speech, save audio file
- `scripts/stt.py` — Speech-to-text from audio file

### Image Generation

```bash
python3 scripts/generate_image.py "A sunset over mountains" -o sunset.png

# Options: --model, --aspect-ratio (1:1, 16:9, 9:16, etc.), --size (0.5K, 1K, 2K, 4K), --output
python3 scripts/generate_image.py "A cat wearing a hat" --aspect-ratio 16:9 --size 2K -o cat.png
```

**Key image models** (verify with API — models change):
| Model | Notes |
|-------|-------|
| `openrouter/auto` | **Default.** Auto-routes to best image-capable model |
| `google/gemini-3.1-flash-image-preview` | Extended aspect ratios, 0.5K–4K |
| `google/gemini-2.5-flash-image` | Standard |
| `black-forest-labs/flux.2-pro` | Image-only output |
| `black-forest-labs/flux.2-flex` | Image-only output |

### Video Generation

```bash
python3 scripts/generate_video.py "A golden retriever playing on a beach" -o video.mp4

# Options: --model, --resolution (480p, 720p, 1080p), --aspect-ratio, --duration, --poll-interval, --max-wait
# Resume polling an existing job:
python3 scripts/generate_video.py "unused" --job-id <JOB_ID> -o video.mp4
```

### Text-to-Speech

```bash
python3 scripts/tts.py "Hello world, this is a test." -o speech.mp3

# Options: --model, --voice (alloy, echo, fable, onyx, nova, shimmer), --format (mp3, pcm), --speed
python3 scripts/tts.py "Welcome to the show." --voice nova --speed 1.2 -o welcome.mp3
```

### Speech-to-Text

```bash
python3 scripts/stt.py recording.wav

# Options: --model, --language (ISO-639-1), --format (auto-detected from extension)
python3 scripts/stt.py recording.mp3 --language en
```

---

## API Reference

The scripts above wrap these OpenRouter endpoints. Use these directly if you need lower-level control.

### Authentication

All requests require:
```
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json
```

API Base URL: `https://openrouter.ai/api/v1`

### Image Generation

**Endpoint:** `POST /chat/completions` — returns base64 data URL in `choices[0].message.images[i].image_url.url`

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/auto",
    "messages": [{"role": "user", "content": "A sunset over mountains"}],
    "modalities": ["image", "text"]
  }'
```

**Image config options** (add to payload):
```json
"image_config": {
  "aspect_ratio": "16:9",   // 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
  "image_size": "2K"         // 0.5K, 1K (default), 2K, 4K
}
```

### Video Generation (Async)

Three-step process: Submit → Poll → Download.

```bash
# 1. Submit
JOB=$(curl -s https://openrouter.ai/api/v1/videos \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bytedance/seedance-2.0",
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

### Text-to-Speech

**Endpoint:** `POST /audio/speech` — returns raw audio bytes (not JSON).

| Param | Required | Description |
|-------|----------|-------------|
| `model` | Yes | TTS model slug |
| `input` | Yes | Text to synthesize |
| `voice` | Yes | Voice ID (alloy, echo, fable, onyx, nova, shimmer) |
| `response_format` | No | `mp3` or `pcm` (default: pcm) |
| `speed` | No | Playback speed (1.0 default, OpenAI only) |

### Speech-to-Text

**Endpoint:** `POST /audio/transcriptions` — returns `{ "text": "...", "usage": { "seconds": N, "cost": N } }`

| Param | Required | Description |
|-------|----------|-------------|
| `model` | Yes | STT model slug |
| `input_audio.data` | Yes | Base64-encoded audio (raw bytes, NOT data URI) |
| `input_audio.format` | Yes | wav, mp3, flac, m4a, ogg, webm, aac |
| `language` | No | ISO-639-1 code (auto-detected if omitted) |

### Sending Multimodal Inputs to Chat Models

All via `/chat/completions` with content arrays in messages:

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

### Discover Models

```bash
# Image
curl -s "https://openrouter.ai/api/v1/models?output_modalities=image" | jq '.data[].id'
# Video
curl -s "https://openrouter.ai/api/v1/videos/models" | jq '.[].id'
# TTS
curl -s "https://openrouter.ai/api/v1/models?output_modalities=speech" | jq '.data[].id'
# STT
curl -s "https://openrouter.ai/api/v1/models?output_modalities=transcription" | jq '.data[].id'
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
