# Mo's Solo Recital · prototype

A clickable phone prototype of an AI companion app. The character, Mo, is fictional and his look is AI-generated.
Coursework demo (HKU MAIB7005).

## 1. Just look around (no setup)

Double-click **`index_en.html`** (English) or **`index.html`** (Chinese).
It opens in your browser. Follow the tour on the right, or press **📱 Clean view** for a phone-only screen.

In this offline mode the story, Moments, the call and the ticket seats all work.
Free chat uses recorded replies matched by topic, so it can't follow a long conversation.

## 2. Let him really reply (needs an API key)

Free chat is then generated live by a model you choose.

1. Install Python 3 if you don't have it (https://www.python.org/downloads/; on Windows tick "Add Python to PATH").
2. Start it:
   - **Windows:** double-click `start_live.bat`
   - **Mac:** double-click `start_live.command` (first time: right-click → Open)
3. Paste your API key, then press Enter twice to keep the defaults, or type your provider's details:

   | Provider | Base URL | Model |
   |---|---|---|
   | OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
   | DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
   | Qwen (DashScope) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |

4. Your browser opens `http://127.0.0.1:8765/index_en.html`. A green **● Live mode** badge means it worked.
   Chinese version: `http://127.0.0.1:8765/index.html`.

Close the black window to stop.

**Your key stays on your computer.** It lives only in that window; the web page never sees it, and only your own computer can connect.
Each reply costs a fraction of a cent on most providers.

## Tips

- Long-press any message to translate it (English ↔ Chinese).
- The tour steps use recorded replies so the story always plays the same way; only free chat goes to the model.
- 60 AI chats a month (RMB 29 tier); story beats and Mo's scheduled messages do not count.

## Troubleshooting

- **Grey "Offline demo" badge:** the page was opened by double-clicking, not through `start_live`. Use the address above.
- **"Live mode error (http 401)":** the key is wrong or expired.
- **"python is not recognised":** reinstall Python and tick "Add Python to PATH".
