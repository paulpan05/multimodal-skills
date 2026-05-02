# OpenRouter Multimodal Skill

Generate images, video, audio (TTS/STT), and process multimodal content via [OpenRouter's](https://openrouter.ai) unified API — with a single API key.

## What it does

This skill teaches AI agents how to use OpenRouter's multimodal endpoints:

- **🎨 Image generation** — Create images from text prompts (Gemini, Flux, etc.)
- **🎥 Video generation** — Submit async video gen jobs, poll, download
- **🔊 Text-to-speech** — Synthesize speech from text
- **🎤 Speech-to-text** — Transcribe audio files
- **📎 Multimodal input** — Send images, PDFs, audio, and video to chat models

## Install

```bash
npx skills add paulpan05/openrouter-multimodal-skill
```

## Prerequisites

- An [OpenRouter API key](https://openrouter.ai/settings/keys)
- Set `OPENROUTER_API_KEY` in your environment or agent config (e.g. `~/.hermes/.env`)

## Quick examples

### Generate an image

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash-image",
    "messages": [{"role": "user", "content": "A sunset over mountains"}],
    "modalities": ["image", "text"]
  }'
```

### Generate a video

```bash
# Submit job
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

# Poll until complete, then download
curl -s "https://openrouter.ai/api/v1/videos/$JOB_ID/content" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -o video.mp4
```

### Text-to-speech

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

## Included scripts

| Script | Description |
|--------|-------------|
| `scripts/generate_image.py` | Generate an image and save to file |
| `scripts/generate_video.py` | Submit video gen job, poll, download |
| `scripts/tts.py` | Text-to-speech, save audio file |
| `scripts/stt.py` | Speech-to-text from audio file |

## Discover models

```bash
# Image models
curl -s "https://openrouter.ai/api/v1/models?output_modalities=image" | jq '.data[].id'

# Video models
curl -s "https://openrouter.ai/api/v1/videos/models" | jq '.[].id'

# TTS models
curl -s "https://openrouter.ai/api/v1/models?output_modalities=speech" | jq '.data[].id'

# STT models
curl -s "https://openrouter.ai/api/v1/models?output_modalities=transcription" | jq '.data[].id'
```

## Full API reference

See [SKILL.md](./SKILL.md) for the complete reference covering all endpoints, parameters, and configuration options.

## License

MIT
