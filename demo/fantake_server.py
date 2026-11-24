#!/usr/bin/env python3
"""FanTake demo · optional live mode.

The HTML files work offline on their own (free chat uses recorded replies).
Run this server only if you want Mo's free-chat replies generated live by your model.

Setup (any OpenAI-compatible endpoint, e.g. the HKUBS GenAI Gateway or DashScope):
    export FANTAKE_API_BASE="https://your-gateway/v1"     # must end where /chat/completions starts
    export FANTAKE_API_KEY="sk-..."
    export FANTAKE_MODEL="qwen3.8-max"                    # the model name your gateway uses
    python3 fantake_server.py

Then open  http://127.0.0.1:8765/FanTake_demo_EN.html  (or _ZH.html).
A green "Live mode" badge appears in the tour panel when it is connected.
Windows (PowerShell): use  $env:FANTAKE_API_KEY="sk-..."  instead of export.
"""
import json, os, re, sys, urllib.request, urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ.get("FANTAKE_API_BASE", "").rstrip("/")
KEY = os.environ.get("FANTAKE_API_KEY", "")
MODEL = os.environ.get("FANTAKE_MODEL", "qwen3.8-max")
PORT = int(os.environ.get("FANTAKE_PORT", "8765"))
HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = bool(BASE and KEY)


def call_model(messages, max_tokens=300):
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps({"model": MODEL, "messages": messages, "temperature": 0.8,
                         "max_tokens": max_tokens}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        # Qwen/DashScope and most gateways report content-filter blocks this way
        if re.search(r"data_inspection|content_filter|inappropriate|sensitive", body, re.I):
            return None, "filtered"
        return None, f"HTTP {e.code}"
    except Exception as e:  # network, timeout
        return None, type(e).__name__
    choice = (j.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "content_filter":
        return None, "filtered"
    return ((choice.get("message") or {}).get("content") or "").strip(), None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=HERE, **k)

    def log_message(self, fmt, *args):
        if args and "/api/" in str(args[0]):
            sys.stderr.write("  " + (fmt % args) + "\n")

    def send_json(self, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/live"):
            return self.send_json({"live": LIVE, "model": MODEL})
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/FanTake_demo_EN.html")
            self.end_headers()
            return
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self.send_json({"error": "bad request"})
        if not LIVE:
            return self.send_json({"error": "no API key set"})
        if self.path == "/api/chat":
            msgs = [{"role": "system", "content": data.get("prompt", "")}]
            for who, text in data.get("history", [])[-12:]:
                msgs.append({"role": "user" if who == "me" else "assistant", "content": text})
            msgs.append({"role": "user", "content": data.get("message", "")})
            out, err = call_model(msgs)
            if err or not out:
                return self.send_json({"error": err or "empty"})
            esc = out.startswith("[ESCALATE]")
            st = re.search(r"\[sticker:(\w+)\]", out)
            reply = re.sub(r"\[sticker:\w+\]", "", out.replace("[ESCALATE]", "")).strip()
            return self.send_json({"reply": reply, "escalate": esc, "sticker": st.group(1) if st else None})
        if self.path == "/api/translate":
            to = data.get("to", "en")
            ask = ("Translate this chat message into natural, casual English. Keep the dry, deadpan tone. "
                   "Output only the translation." if to == "en" else "把这句聊天翻译成自然的中文口语，保留语气，只输出译文。")
            out, err = call_model([{"role": "system", "content": ask},
                                   {"role": "user", "content": data.get("text", "")}], 200)
            return self.send_json({"text": out} if out else {"error": err or "empty"})
        self.send_json({"error": "unknown endpoint"})


if __name__ == "__main__":
    print(f"FanTake demo on http://127.0.0.1:{PORT}/FanTake_demo_EN.html  (中文: /FanTake_demo_ZH.html)")
    print(f"Live mode: {'ON · ' + MODEL if LIVE else 'OFF (set FANTAKE_API_BASE and FANTAKE_API_KEY)'}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
