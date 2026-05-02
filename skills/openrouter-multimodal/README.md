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
npx skills add paulpan05/multimodal-skills
```

## Prerequisites

- An [OpenRouter API key](https://openrouter.ai/settings/keys)
- Set `OPENROUTER_API_KEY` in your environment or agent config (e.g. `~/.hermes/.env`)

## Usage

### Generate an image

```bash
python3 scripts/generate_image.py "A sunset over mountains" -o sunset.png

# With options
python3 scripts/generate_image.py "A cat wearing a hat" --aspect-ratio 16:9 --size 2K -o cat.png
```

### Generate a video

```bash
python3 scripts/generate_video.py "A golden retriever playing on a beach" -o video.mp4

# Custom resolution and aspect ratio
python3 scripts/generate_video.py "Ocean waves crashing" --resolution 1080p --aspect-ratio 16:9 -o waves.mp4
```

### Text-to-speech

```bash
python3 scripts/tts.py "Hello world, this is a test." -o speech.mp3

# With voice and speed options
python3 scripts/tts.py "Welcome to the show." --voice nova --speed 1.2 -o welcome.mp3
```

### Speech-to-text

```bash
python3 scripts/stt.py recording.wav

# Specify language
python3 scripts/stt.py recording.mp3 --language en
```

### Discover available models

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

See [SKILL.md](./SKILL.md) for the complete endpoint reference covering all parameters, configuration options, and multimodal input formats.

## License

MIT
