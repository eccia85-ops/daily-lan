from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import json
import os
import asyncio

app = FastAPI()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "eccia85-ops/daily-lan")

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

def build_prompt(lang, lang_name, level, level_desc, topic, topic_desc):
    if level == "word":
        return (
            f"Create a vocabulary list for a Korean adult learner studying {lang_name}.\n"
            f"Topic: {topic_desc}\n"
            f"Count: 8 words\n"
            f"Requirements:\n"
            f"- For Japanese: include hiragana in reading field\n"
            f"- For Chinese: include pinyin in reading field\n"
            f"- For others: set reading to empty string\n"
            f"- Respond ONLY with a JSON object, no markdown, no explanation\n"
            f'- Format: {{"type":"word","items":[{{"word":"...","reading":"...","ko":"...","pronun":"...","example":"..."}}]}}\n'
            f"- ko: Korean meaning (1-3 words)\n"
            f"- pronun: Korean phonetic transcription of how the {lang_name} word SOUNDS (not translation). e.g. 'merci' -> '메르시'\n"
            f"- example: one short sentence in {lang_name} only"
        )
    else:
        return (
            f"Create a short {lang_name} shadowing script for a Korean adult learner.\n"
            f"Level: {level_desc}\n"
            f"Topic: {topic_desc}\n"
            f"Lines: 8 to 10\n"
            f"Requirements:\n"
            f"- Natural dialogue between speaker A and speaker B\n"
            f"- For Japanese: include hiragana in reading field\n"
            f"- For Chinese: include pinyin in reading field\n"
            f"- For others: set reading to empty string\n"
            f"- EVERY line MUST have ALL fields: speaker, text, reading, ko, pronun\n"
            f"- Respond ONLY with a JSON object, no markdown, no explanation\n"
            f'- Format: {{"type":"script","lines":[{{"speaker":"A","text":"...","reading":"...","ko":"...","pronun":"..."}}]}}\n'
            f"- ko: natural Korean translation (REQUIRED)\n"
            f"- pronun: Korean phonetic transcription of how the {lang_name} sentence SOUNDS (not translation). e.g. 'Bonjour' -> '봉주르' (REQUIRED)"
        )

async def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_KEY}"
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        data = res.json()
    if "candidates" not in data:
        return None
    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

async def save_to_github(scripts):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/data/scripts.json"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    content = json.dumps(scripts, ensure_ascii=False, indent=2)
    import base64
    encoded = base64.b64encode(content.encode()).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        # 현재 파일 SHA 가져오기
        res = await client.get(url, headers=headers)
        sha = res.json().get("sha", "")
        # 업데이트
        await client.put(url, headers=headers, json={
            "message": "Auto-generate daily scripts",
            "content": encoded,
            "sha": sha
        })

@app.get("/api/generate_all")
async def generate_all():
    scripts = {}
    for lang, lang_name in LANG_MAP.items():
        for level, level_desc in LEVEL_MAP.items():
            for topic, topic_desc in TOPIC_MAP.items():
                key = f"{lang}_{level}_{topic}"
                prompt = build_prompt(lang, lang_name, level, level_desc, topic, topic_desc)
                try:
                    result = await call_gemini(prompt)
                    if result:
                        scripts[key] = result
                except Exception as e:
                    scripts[key] = {"error": str(e)}
                await asyncio.sleep(2)  # rate limit 방지

    await save_to_github(scripts)
    return JSONResponse({"status": "ok", "count": len(scripts)})
