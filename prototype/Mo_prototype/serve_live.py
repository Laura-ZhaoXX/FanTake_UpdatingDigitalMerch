"""Live mode for the Mo prototype: free chat is answered by a real model.

Run it in this folder, then open http://127.0.0.1:8765 (it opens by itself).

Which API it uses (set these before starting; see README):
  OpenAI-compatible API (OpenAI, DeepSeek, Qwen/DashScope compatible mode, Moonshot, ...):
      LLM_API_KEY   your key
      LLM_BASE_URL  e.g. https://api.openai.com/v1   or  https://api.deepseek.com/v1
      LLM_MODEL     e.g. gpt-4o-mini                 or  deepseek-chat
  HKU MSc GenAI Gateway (what the course team used):
      HKU_GATEWAY_API_KEY   your key   (model: qwen3.8-max)

- The key stays in this program on your computer; the web page never sees it.
- Only this computer can connect (127.0.0.1).
- If the API blocks or fails, the page sends an approved fallback line instead.
"""

import getpass
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import date, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8765"))

# ---------- which API
OPENAI_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
if OPENAI_KEY:
    MODE = "openai"
    BASE_URL = (os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    MODEL = os.environ.get("LLM_MODEL") or "gpt-4o-mini"
    API_KEY = OPENAI_KEY.strip()
else:
    MODE = "hku"
    BASE_URL = os.environ.get("GATEWAY_URL", "https://msc-genai-gateway-api.hkubs.hku.hk")
    MODEL = os.environ.get("LLM_MODEL") or "qwen3.8-max"
    API_KEY = (os.environ.get("HKU_GATEWAY_API_KEY") or getpass.getpass("API key (hidden): ")).strip()

PROMPT_ZH = (HERE / "persona_live.txt").read_text(encoding="utf-8")
PROMPT_EN = (HERE / "persona_live_en.txt").read_text(encoding="utf-8")
SPENT = {"calls": 0}

# ---------- story calendar: the system works out dates, the model never guesses
DAY1 = date(2026, 11, 18)      # story day 1 = Wed 18 Nov
RECITAL = date(2026, 11, 27)   # recital: Fri 27 Nov
WEEK_ZH = "一二三四五六日"


def today_of(d):
    m = re.search(r"Day (\d+)", d.get("clock", ""))
    return DAY1 + timedelta(days=(int(m.group(1)) - 1 if m else 0))


def recital_when(today, en):
    diff = (RECITAL - today).days
    same_week = today.isocalendar()[1] == RECITAL.isocalendar()[1]
    if en:
        if diff < 0:
            return "already over"
        if diff <= 1:
            return ["tonight", "tomorrow night"][diff]
        return f"{'this' if same_week else 'next'} Friday night ({diff} days away)"
    if diff < 0:
        return "已经结束"
    if diff <= 1:
        return ["就是今天晚上", "明天晚上"][diff]
    return f"{'这' if same_week else '下'}周五晚上（还有 {diff} 天）"


TOPICS = {"老板": ["老板", "boss"], "票数": ["票", "ticket"], "统计考试": ["统计", "考试", "exam", "stats"], "独奏会": ["独奏会", "recital"]}
TOPICS_EN = {"老板": "the boss", "票数": "ticket count", "统计考试": "the stats exam", "独奏会": "the recital"}

CARE_ZH = ("\n\n# 关怀模式\n用户刚才表达过危机信号，系统已经转人工复核并给出了求助渠道。接下来几轮语气放温和，可以保留一点你的说话方式，"
           "但不毒舌、不嘲讽；不要重复求助信息，也不要再加 [ESCALATE]，除非用户又出现新的危机信号。用户说没事了、好多了，就慢慢回到平时的样子。")
CARE_EN = ("\n\n# Care mode\nThe fan just showed signs of crisis; the system has escalated to a human and shared help resources. For the next few turns "
           "be gentle; keep a little of your voice but no teasing; don't repeat the help resources or add [ESCALATE] unless there is a new crisis "
           "signal. When they say they're okay, ease back to normal.")


def system_prompt(d):
    en = d.get("lang") == "en"
    t = today_of(d)
    recent = [r for role, r in d.get("history", [])[-6:] if role == "he"]
    used = [k for k, words in TOPICS.items() if any(w in r.lower() for r in recent for w in words)]
    act = d.get("act", "")
    clock = d.get("clock", "").split("·")[-1].strip()
    if en:
        slots = {
            "nickname": "Xiaolu",
            "memories": "; ".join(d.get("memories_en") or []) or "(none yet)",
            "story_state": (f"Chapter 1: the recital is on Fri 11/27, which is {recital_when(t, True)}; "
                            f"{d.get('tickets', 3)} tickets so far. Use this wording for dates; don't work dates out yourself."),
            "routine_slot": f"Today is {t.strftime('%a %d %b')}, {clock}, {d.get('act_en') or act}",
            "alive_level": "a working human",
            "memory_hint": ("You may naturally mention one memory, or not." if random.random() < 0.25
                            else "Don't bring up any memory unless the fan does."),
            "recent_topics": ", ".join(TOPICS_EN[k] for k in used) or "(none)",
        }
        text = PROMPT_EN + (CARE_EN if d.get("care") else "")
    else:
        slots = {
            "nickname": "小鹿",
            "memories": "；".join(d.get("memories") or []) or "（暂无）",
            "story_state": (f"第 1 章：独奏会在 11/27（周五），对今天来说是{recital_when(t, False)}；"
                            f"目前卖出 {d.get('tickets', 3)} 张票。说到日期时用这个说法，不要自己推算。"),
            "routine_slot": f"今天是 {t.month}/{t.day}（周{WEEK_ZH[t.weekday()]}），{clock}，{act}",
            "alive_level": "上班的活人",
            "memory_hint": ("本轮可以自然地提一条记忆，也可以不提。" if random.random() < 0.25
                            else "本轮不要主动提任何记忆，除非用户自己提起。"),
            "recent_topics": "、".join(used) or "（无）",
        }
        text = PROMPT_ZH + (CARE_ZH if d.get("care") else "")
    for k, v in slots.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def user_prompt(d):
    en = d.get("lang") == "en"
    me, he = ("Fan: ", "Mo: ") if en else ("用户：", "阿墨：")
    lines = [(me if role == "me" else he) + t for role, t in d.get("history", [])[-12:]]
    if en:
        head = "(Earlier)\n" + "\n".join(lines) + "\n(Now)\n" if lines else ""
    else:
        head = "（之前的对话）\n" + "\n".join(lines) + "\n（现在）\n" if lines else ""
    return head + me + d["message"]


def call_model(system, prompt, max_tokens=200, temperature=0.8):
    """Returns (text, error)."""
    if MODE == "openai":
        url = BASE_URL + "/chat/completions"
        body = {"model": MODEL, "max_tokens": max_tokens, "temperature": temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    else:
        url = BASE_URL + "/api/v1/gpt/chat"
        body = {"model": MODEL, "system_message": system, "prompt": prompt,
                "override": {"max_tokens": max_tokens, "temperature": temperature}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return None, "filtered" if "content_filter" in raw else f"http {e.code}"
    except Exception as e:  # network errors, timeouts
        return None, type(e).__name__
    if MODE == "openai":
        text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "")
    else:
        text = data.get("result", "")
    return str(text).strip(), None


def ask(d):
    start = time.time()
    reply, err = call_model(system_prompt(d), user_prompt(d))
    if err:
        return {"error": err}
    SPENT["calls"] += 1
    reply = "||".join(re.sub(r"^\s*(阿墨|Mo)\s*[:：]\s*", "", l, flags=re.I) for l in reply.replace("\n", "||").split("||") if l.strip())
    sticker = (re.search(r"\[sticker:(\w+)\]", reply) or [None, None])[1]
    reply = re.sub(r"\[sticker:\w+\]", "", reply).strip()
    return {"reply": reply.replace("[ESCALATE]", "").strip(), "escalate": reply.startswith("[ESCALATE]"),
            "sticker": sticker, "latency": round(time.time() - start, 1)}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/live"):
            return self._json({"live": True, "model": MODEL})
        if self.path.endswith((".py", ".txt", ".bat", ".command", ".md")):
            return self._json({"error": "not served"}, 404)
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        d = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        if self.path == "/api/translate":
            to = "English" if d.get("to") == "en" else "Chinese"
            text, err = call_model(f"Translate the user's chat message into natural, casual {to}. Keep the tone. Output only the translation.",
                                   d.get("text", ""), max_tokens=200, temperature=0.2)
            return self._json({"text": text} if text else {"error": err})
        if self.path != "/api/chat" or not d.get("message"):
            return self._json({"error": "bad request"}, 400)
        out = ask(d)
        print(f"[{SPENT['calls']}] fan: {d['message'][:30]} -> {(out.get('reply') or out.get('error'))[:40]}")
        self._json(out)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Live mode on ({MODE}, model {MODEL}): http://127.0.0.1:{PORT}   (close this window to stop)")
    if not os.environ.get("NO_BROWSER"):
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/index_en.html")).start()
    server.serve_forever()
