from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import json
import os

app = FastAPI()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

LANG_MAP = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese (Mandarin)",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

LEVEL_MAP = {
    "word":     "vocabulary level",
    "beginner": "beginner level (A2), short simple sentences",
    "daily":    "intermediate level (B1-B2), natural conversation",
    "business": "business level (B2-C1), formal professional expressions",
}

TOPIC_MAP = {
    "daily":  "everyday life (morning routine, cafe, weather)",
    "travel": "travel (hotel, airport, directions, ordering food)",
    "hobby":  "hobbies (cycling, camping, outdoor activities)",
    "work":   "workplace (meetings, feedback, presentations)",
}

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Daily Language</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;color:#1a1a1a;min-height:100vh}
    .header{background:#fff;padding:16px 20px;border-bottom:1px solid #e0e0e0;display:flex;align-items:center;gap:10px}
    .streak{font-size:13px;color:#888}.streak span{font-weight:700;color:#1a1a1a}
    .card{background:#fff;border-radius:16px;margin:16px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
    .label{font-size:12px;color:#888;margin-bottom:10px;font-weight:500}
    .btn-group{display:flex;gap:8px;flex-wrap:wrap}
    .lang-group{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
    .btn{border:1.5px solid #e0e0e0;border-radius:10px;padding:10px 14px;font-size:14px;background:#fff;cursor:pointer;transition:all .15s;text-align:center}
    .btn.active{background:#1a1a1a;color:#fff;border-color:#1a1a1a}
    .gen-btn{display:block;width:calc(100% - 32px);margin:0 16px 16px;padding:16px;background:#1a1a1a;color:#fff;border:none;border-radius:14px;font-size:16px;font-weight:600;cursor:pointer}
    .gen-btn:disabled{background:#ccc}
    .output{margin:0 16px 24px}
    .script-card{background:#fff;border-radius:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;margin-bottom:12px}
    .line{padding:14px 18px;border-bottom:1px solid #f0f0f0}
    .line:last-child{border-bottom:none}
    .spk{display:inline-flex;width:24px;height:24px;border-radius:50%;font-size:11px;font-weight:700;align-items:center;justify-content:center;margin-right:8px}
    .spk.a{background:#d0e8ff;color:#1a6fc4}.spk.b{background:#e8e8e8;color:#555}
    .main-text{font-size:16px;font-weight:500;line-height:1.5}
    .reading{font-size:12px;color:#aaa;margin-top:2px;margin-left:32px}
    .ko{font-size:13px;color:#888;margin-top:3px;margin-left:32px}
    .word-item{padding:16px 18px;border-bottom:1px solid #f0f0f0}
    .word-item:last-child{border-bottom:none}
    .word{font-size:22px;font-weight:700}
    .word-reading{font-size:14px;color:#888;margin-top:2px}
    .word-ko{font-size:14px;color:#555;margin-top:4px}
    .word-ex{font-size:13px;color:#aaa;margin-top:6px;font-style:italic}
    .bottom{display:flex;gap:10px;margin-top:4px}
    .bottom-btn{flex:1;padding:13px;border-radius:12px;font-size:14px;font-weight:500;cursor:pointer;border:1.5px solid #e0e0e0;background:#fff}
    .bottom-btn.dark{background:#1a1a1a;color:#fff;border-color:#1a1a1a}
    .loading{text-align:center;padding:40px;color:#888;background:#fff;border-radius:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
    .error{text-align:center;padding:40px;color:#e53e3e;background:#fff;border-radius:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
  </style>
</head>
<body>
  <div class="header">
    <span>🔥</span>
    <div class="streak">연속 학습 <span>0</span>일</div>
  </div>

  <div class="card">
    <div class="label">언어</div>
    <div class="lang-group" id="lang-group">
      <button class="btn active" data-val="en">🇺🇸 영어</button>
      <button class="btn" data-val="ja">🇯🇵 일본어</button>
      <button class="btn" data-val="zh">🇨🇳 중국어</button>
      <button class="btn" data-val="es">🇪🇸 스페인어</button>
      <button class="btn" data-val="fr">🇫🇷 프랑스어</button>
      <button class="btn" data-val="de">🇩🇪 독일어</button>
    </div>
  </div>

  <div class="card">
    <div class="label">난이도</div>
    <div class="btn-group" id="level-group">
      <button class="btn active" data-val="word">단어</button>
      <button class="btn" data-val="beginner">입문</button>
      <button class="btn" data-val="daily">일상</button>
      <button class="btn" data-val="business">비즈니스</button>
    </div>
  </div>

  <div class="card">
    <div class="label">주제</div>
    <div class="btn-group" id="topic-group">
      <button class="btn active" data-val="daily">☀️ 일상</button>
      <button class="btn" data-val="travel">✈️ 여행</button>
      <button class="btn" data-val="hobby">🚴 취미</button>
      <button class="btn" data-val="work">💼 직장</button>
    </div>
  </div>

  <button class="gen-btn" id="gen-btn" onclick="generate()">스크립트 생성</button>
  <div class="output" id="output"></div>

  <script>
    let lang='en', level='word', topic='daily';
    function setupGroup(id, setter) {
      document.getElementById(id).addEventListener('click', e => {
        const b = e.target.closest('[data-val]');
        if (!b) return;
        document.querySelectorAll('#'+id+' .btn').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        setter(b.dataset.val);
      });
    }
    setupGroup('lang-group',  v => { lang=v;  onSelectionChange(); });
    setupGroup('level-group', v => { level=v; onSelectionChange(); });
    setupGroup('topic-group', v => { topic=v; onSelectionChange(); });

    function onSelectionChange() {
      const key = `${lang}_${level}_${topic}`;
      const out = document.getElementById('output');
      koOn = false;
      pronunOn = false;
      if (cache[key]) {
        currentLang = lang;
        const data = cache[key];
        if (data.type === 'word') renderWords(data.items);
        else renderScript(data.lines);
      } else {
        out.innerHTML = '';
      }
    }

    async function generate() {
      const btn = document.getElementById('gen-btn');
      const out = document.getElementById('output');
      btn.disabled = true;
      out.innerHTML = '<div class="loading">생성 중...</div>';
      try {
        const res = await fetch(`/api/script?lang=${lang}&level=${level}&topic=${topic}`);
        const data = await res.json();
        if (data.error) { out.innerHTML = `<div class="error">오류: ${data.error}</div>`; }
        else if (data.type === 'word') renderWords(data.items);
        else renderScript(data.lines);
      } catch(e) {
        out.innerHTML = '<div class="error">네트워크 오류. 다시 시도해주세요.</div>';
      }
      btn.disabled = false;
    }

    let koOn = false;
    let pronunOn = false;
    let currentLang = 'en';
    const cache = {};
    const LANG_VOICE = {
      en:'en-US', ja:'ja-JP', zh:'zh-CN', es:'es-ES', fr:'fr-FR', de:'de-DE'
    };

    function toggleKo() {
      koOn = !koOn;
      document.querySelectorAll('.ko').forEach(el => el.style.visibility = koOn ? '' : 'hidden');
      document.getElementById('ko-btn').textContent = koOn ? '한국어 숨기기' : '한국어 보이기';
    }
    function togglePronun() {
      pronunOn = !pronunOn;
      document.querySelectorAll('.pronun').forEach(el => el.style.visibility = pronunOn ? '' : 'hidden');
      document.getElementById('pronun-btn').textContent = pronunOn ? '발음 숨기기' : '발음 보이기';
    }

    function speak(text, idx) {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.lang = LANG_VOICE[currentLang] || 'en-US';
      utt.rate = 0.9;
      window.speechSynthesis.speak(utt);
    }

    let playIndex = 0;
    let playLines = [];
    function playAll() {
      window.speechSynthesis.cancel();
      playIndex = 0;
      playNext();
    }
    function playNext() {
      if (playIndex >= playLines.length) return;
      const utt = new SpeechSynthesisUtterance(playLines[playIndex]);
      utt.lang = LANG_VOICE[currentLang] || 'en-US';
      utt.rate = 0.9;
      utt.onend = () => { playIndex++; setTimeout(playNext, 400); };
      window.speechSynthesis.speak(utt);
    }

    async function generate(force=false) {
      const btn = document.getElementById('gen-btn');
      const out = document.getElementById('output');
      const key = `${lang}_${level}_${topic}`;
      koOn = false;
      pronunOn = false;

      if (!force && cache[key]) {
        currentLang = lang;
        const data = cache[key];
        if (data.type === 'word') renderWords(data.items);
        else renderScript(data.lines);
        return;
      }

      btn.disabled = true;
      out.innerHTML = '<div class="loading">생성 중...</div>';
      currentLang = lang;
      try {
        const res = await fetch(`/api/script?lang=${lang}&level=${level}&topic=${topic}`);
        const data = await res.json();
        if (data.error) { out.innerHTML = `<div class="error">오류: ${data.error}</div>`; }
        else {
          cache[key] = data;
          if (data.type === 'word') renderWords(data.items);
          else renderScript(data.lines);
        }
      } catch(e) {
        out.innerHTML = '<div class="error">네트워크 오류. 다시 시도해주세요.</div>';
      }
      btn.disabled = false;
    }

    function renderScript(lines) {
      playLines = lines.map(l => l.text);
      let h = '<div class="script-card">';
      lines.forEach((l, i) => {
        h += `<div class="line">
          <div style="display:flex;align-items:center;gap:8px">
            <span class="spk ${l.speaker.toLowerCase()}">${l.speaker}</span>
            <span class="main-text">${l.text}</span>
            <button onclick="speak('${l.text.replace(/'/g,"\\'")}',${i})" style="margin-left:auto;background:none;border:none;cursor:pointer;font-size:16px;">🔊</button>
          </div>`;
        if (l.reading) h += `<div class="reading">${l.reading}</div>`;
        h += `<div class="ko" style="visibility:hidden">${l.ko || ''}</div>`;
        h += `<div class="reading pronun" style="color:#b0a0ff;visibility:hidden">${l.pronun || ''}</div>`;
        h += `</div>`;
      });
      h += '</div><div class="bottom">';
      h += `<button class="bottom-btn" id="ko-btn" onclick="toggleKo()">한국어 보이기</button>`;
      h += `<button class="bottom-btn" id="pronun-btn" onclick="togglePronun()">발음 보이기</button>`;
      h += `<button class="bottom-btn" onclick="playAll()">▶ 전체 듣기</button>`;
      h += `<button class="bottom-btn dark" onclick="generate(true)">다시 생성</button></div>`;
      document.getElementById('output').innerHTML = h;
    }

    function renderWords(items) {
      let h = '<div class="script-card">';
      items.forEach(w => {
        h += `<div class="word-item"><div class="word">${w.word}</div>`;
        if (w.reading) h += `<div class="word-reading">${w.reading}</div>`;
        h += `<div class="word-ko" style="visibility:hidden">${w.ko}</div>`;
        if (w.pronun) h += `<div class="word-reading" style="color:#b0a0ff">${w.pronun}</div>`;
        if (w.example) h += `<div class="word-ex">${w.example}</div>`;
        h += `</div>`;
      });
      h += `</div><div class="bottom"><button class="bottom-btn dark" onclick="generate(true)">다시 생성</button></div>`;
      document.getElementById('output').innerHTML = h;
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@app.get("/api/script")
async def get_script(lang: str = "en", level: str = "word", topic: str = "daily"):
    lang_name = LANG_MAP.get(lang, "English")
    level_desc = LEVEL_MAP.get(level, LEVEL_MAP["word"])
    topic_desc = TOPIC_MAP.get(topic, TOPIC_MAP["daily"])

    if level == "word":
        prompt = f"""Create a vocabulary list for a Korean adult learner studying {lang_name}.
Topic: {topic_desc}
Count: 8 words
Requirements:
- For Japanese: include hiragana in reading field
- For Chinese: include pinyin in reading field
- For others: set reading to empty string
- Respond ONLY with a JSON object, no markdown, no explanation
- Format: {{"type":"word","items":[{{"word":"...","reading":"...","ko":"...","pronun":"...","example":"..."}}]}}
- ko: Korean meaning (1-3 words)
- pronun: Korean phonetic transcription of how the {lang_name} word SOUNDS (not a translation). e.g. Japanese "ありがとう" → "아리가토우", French "merci" → "메르시"
- example: one short sentence in {lang_name} only"""
    else:
        prompt = f"""Create a short {lang_name} shadowing script for a Korean adult learner.
Level: {level_desc}
Topic: {topic_desc}
Lines: 8 to 10
Requirements:
- Natural dialogue between speaker A and speaker B
- For Japanese: include hiragana in reading field
- For Chinese: include pinyin in reading field
- For others: set reading to empty string
- EVERY line MUST have ALL fields: speaker, text, reading, ko, pronun
- ko and pronun are REQUIRED even if empty string
- Respond ONLY with a JSON object, no markdown, no explanation
- Format: {{"type":"script","lines":[{{"speaker":"A","text":"...","reading":"...","ko":"...","pronun":"..."}}]}}
- ko: natural Korean translation (REQUIRED)
- pronun: Korean phonetic transcription of how the {lang_name} sentence SOUNDS (not a translation). e.g. French "Bonjour" → "봉주르", Spanish "Buenos días" → "부에노스 디아스" (REQUIRED)"""

    url = f"https://generativelanguage.googleapis.com

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}]
            })
            data = res.json()

        if "candidates" not in data:
            return JSONResponse({"error": str(data)}, status_code=500)

        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
