# FanTake — Digital Merch That Keeps Updating

MAIB7005 Advanced Machine Learning and Deep Learning · Group 16 final project (HKU, Nov 2026)

**Demo and prototype:** Zhao Xuan

FanTake is a B2B2C app concept. Artist studios commission authorised, 30-day interactive stories, and fans chat with an AI character and make choices that shape later chapters. The demo character, Mo, is fictional.

## Contents

| Folder | What's inside |
|---|---|
| `demo/` | `FanTake_demo_EN.html`: the clickable demo. Open it in a browser and it runs offline with scripted replies. `FanTake_demo_EN_final.mp4`: a 1:55 walkthrough with English narration, subtitles and sound effects (subtitles also as `.srt`). `fantake_server.py`: optional live mode. |
| `prototype/Mo_prototype/` | The earlier Mo chat prototype, with persona, photos, stickers and a live-mode server. |
| `assets/` | Story images used in the demo and poster. |

## Run the demo in live mode (optional)

The demo calls an OpenAI-compatible model API. No API key is stored in this repo, so you supply your own:

```bash
export FANTAKE_API_BASE="https://your-gateway/v1"
export FANTAKE_API_KEY="your-key"
cd demo && python fantake_server.py
# then open http://127.0.0.1:8765/FanTake_demo_EN.html
```

On Windows PowerShell, use `$env:FANTAKE_API_KEY="your-key"`.

## Notes

- The clickable demo has no voice: its "pre-recorded voice call" scene shows a transcript only. The narrated video uses a synthetic narrator voice (Kokoro, offline TTS).
- Mo and all story content are fictional. The business plan and poster are group work and are not included here.
