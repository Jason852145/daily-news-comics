"""
Daily News Comics Generator
Runs in GitHub Actions every morning at 08:30 Taiwan time (00:30 UTC).

Pipeline:
  1. Fetch international news from RSS (BBC World + NYT World)
  2. Use GPT-4o-mini to pick top 3 and rewrite in 古風 style
  3. Generate SD chibi style images via gpt-image-1
  4. Build HTML + save PNGs to /docs/ (GitHub Pages serves these)
  5. Broadcast a Flex Message to LINE subscribers (= you)
"""

import os
import json
import base64
import datetime
import feedparser
import requests
from pathlib import Path
from zoneinfo import ZoneInfo

# ===== Config =====
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "user/daily-news-comics")  # e.g. "jason/daily-news-comics"
GH_OWNER, GH_REPO = GITHUB_REPO.split("/")
# GitHub Pages uses lowercase for the user subdomain
PAGES_URL = f"https://{GH_OWNER.lower()}.github.io/{GH_REPO}"

TZ_TAIPEI = ZoneInfo("Asia/Taipei")
NOW_TPE = datetime.datetime.now(TZ_TAIPEI)
TODAY = NOW_TPE.date().isoformat()                   # YYYY-MM-DD
RUN_STAMP = NOW_TPE.strftime("%Y%m%d-%H%M")          # for cache-busting image filenames

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)

STYLE_SUFFIX = (
    "super deformed (SD) chibi cartoon style, big head small body proportions, "
    "Japanese anime デフォルメ stylization, exaggerated cute expressions, "
    "bold clean outlines, bright flat colors, soft pastel palette, "
    "kawaii mascot look, simple minimal background"
)

TOP_N = 5

# ===== Step 1: Fetch news =====
print("Step 1: Fetching news from RSS...")
feeds = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]
raw_stories = []
for url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries[:10]:
        raw_stories.append({
            "title": entry.get("title", "").strip(),
            "summary": entry.get("summary", "").strip()[:500],
            "link": entry.get("link", ""),
        })
print(f"  Collected {len(raw_stories)} raw stories")

# ===== Step 2: Ask GPT to pick top 3 + rewrite =====
print("Step 2: GPT picking top 3 and rewriting in 古風...")
rewrite_prompt = f"""You are a friendly journalist writing a daily international news digest for a Taiwanese audience. Your tone is modern, casual Traditional Chinese (繁體中文、白話文) with light humor — but humor is the STYLE, not the selection criterion. Your job is to help readers understand what's actually happening in the world today.

Here are {len(raw_stories)} international news items from today. From these, select the {TOP_N} MOST IMPORTANT / NEWSWORTHY stories — the ones a well-informed person should know about today.

SELECTION PRINCIPLES (in priority order):
1. Importance: pick stories with real impact — major political events, significant economic moves, breaking international developments, notable scientific/tech advances, major cultural moments
2. Diversity: try to cover different regions (not all from one country) and different topic types (e.g., one politics, one economy, one tech/culture) if possible given the source material
3. DO NOT pick stories just because they're funny or absurd — pick them because they matter. Humor is applied in the WRITING, not the selection.

TONE / WRITING STYLE:
- Modern Traditional Chinese (白話文), like explaining to a friend over coffee
- Light humor via observation and witty framing, NOT jokes or mockery
- For serious stories (politics, economics, tragic events): factual + insightful commentary + maybe one light closing line. DO NOT force humor on tragedy.
- For lighter stories (cultural quirks, sports, tech oddities): can be more playful
- NEVER use classical Chinese (文言文). NEVER use 曰/爾/矣/吾/上曰/下應/章回體

For each of the {TOP_N} selected stories, produce:

- title: Traditional Chinese, format "其N · [國家或城市] · [事件重點]". Location is REQUIRED so readers know this is international news.
  Examples:
  - "其一 · 菲律賓馬尼拉 · 熱帶低壓重創首都"
  - "其二 · 美國華府 · 聯準會升息半碼"
  - "其三 · 日本東京 · AI 法案進入國會審議"

- tagline: Traditional Chinese, one sentence explaining WHERE + WHAT in plain language. 25-40 characters. Should tell the reader the essence of the news.
  Examples:
  - "菲律賓首都馬尼拉連日暴雨，多處淹水、交通癱瘓"
  - "美國聯準會宣布升息 0.25%，市場反應兩極"

- body: Traditional Chinese, 白話文 with light humor where appropriate. 150-250 characters. MUST include:
  1. 事件地點（國家/城市）
  2. 具體發生什麼事（時間、規模、誰受影響）
  3. 為什麼這則新聞重要 / 有什麼後續或意義
  4. （如合適）一句輕鬆的觀察或俏皮收尾 —— 但嚴肅新聞就平實收尾，別硬搞笑

- scene_en: Short English scene description for image generation. 1-2 clauses describing 1-3 cute chibi characters in a scene that VISUALLY represents the story. Include ethnicity/clothing context if relevant. Do NOT include any style keywords — those are appended separately.

- source_url: Copy the exact "link" field from the original news item you selected. This will be shown as a "news source" button so readers can read the original article.

Return ONLY valid JSON (no markdown fences, no extra text) with this exact structure:
{{"stories": [{{"title": "...", "tagline": "...", "body": "...", "scene_en": "...", "source_url": "..."}}, ... {TOP_N} items]}}

News items to choose from:
{json.dumps(raw_stories, ensure_ascii=False, indent=2)}
"""

resp = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": rewrite_prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    },
    timeout=60,
)
resp.raise_for_status()
rewritten = json.loads(resp.json()["choices"][0]["message"]["content"])
stories = rewritten["stories"][:TOP_N]
assert len(stories) == TOP_N, f"Expected {TOP_N} stories, got {len(stories)}"
for s in stories:
    print(f"  - {s['title']}")

# ===== Step 3: Generate images =====
print("Step 3: Generating SD chibi images...")
for i, s in enumerate(stories, 1):
    img_prompt = f"{s['scene_en']}, {STYLE_SUFFIX}"
    print(f"  [{i}/{TOP_N}] prompt: {s['scene_en'][:60]}...")
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": img_prompt,
            "size": "1024x1024",
            "n": 1,
            "quality": "low",
        },
        timeout=120,
    )
    r.raise_for_status()
    b64 = r.json()["data"][0]["b64_json"]
    # Use RUN_STAMP (date + time) so LINE/browser can't serve a cached old image
    img_name = f"img-{RUN_STAMP}-{i}.png"
    (OUT_DIR / img_name).write_bytes(base64.b64decode(b64))
    s["img_filename"] = img_name
    s["story_index"] = i   # used for anchor IDs in HTML
    print(f"    ✓ saved {img_name}")

# ===== Step 4: Build HTML =====
print("Step 4: Building HTML...")
html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>每日新聞漫畫 · {TODAY}</title>
<style>
  body {{
    font-family: "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
    background: linear-gradient(180deg, #f5e6c8 0%, #e8d5a8 100%);
    margin: 0; padding: 20px;
    color: #2c1810;
  }}
  .wrap {{ max-width: 780px; margin: 0 auto; }}
  header {{
    text-align: center;
    border-bottom: 3px double #8b4513;
    padding-bottom: 16px;
    margin-bottom: 28px;
  }}
  header h1 {{
    margin: 0;
    font-size: 28px;
    color: #8b0000;
    letter-spacing: 3px;
  }}
  header p {{ margin: 6px 0 0; color: #6b4423; font-size: 14px; }}
  .comic {{
    background: #fffaf0;
    border: 2px solid #8b4513;
    border-radius: 4px;
    box-shadow: 6px 6px 0 rgba(139, 69, 19, 0.4);
    padding: 20px;
    margin-bottom: 28px;
  }}
  .comic h2 {{
    margin: 0 0 8px;
    font-size: 20px;
    color: #8b0000;
    letter-spacing: 2px;
  }}
  .comic .tagline {{
    color: #6b4423;
    font-style: italic;
    margin: 0 0 14px;
    font-size: 14px;
    border-left: 3px solid #c9a66b;
    padding-left: 10px;
  }}
  .comic img {{
    width: 100%;
    border-radius: 8px;
    border: 1px solid #c9a66b;
    margin-bottom: 12px;
  }}
  .comic p.body {{
    line-height: 1.8;
    margin: 0 0 12px;
    font-size: 15px;
  }}
  .comic .source {{
    margin: 0;
    padding-top: 10px;
    border-top: 1px dashed #c9a66b;
    font-size: 13px;
  }}
  .comic .source a {{
    color: #8b4513;
    text-decoration: none;
  }}
  .comic .source a:hover {{
    text-decoration: underline;
  }}
  .comic {{
    scroll-margin-top: 20px;
  }}
  footer {{
    text-align: center;
    font-size: 12px;
    color: #6b4423;
    margin-top: 24px;
  }}
  .archive {{ text-align: center; margin: 20px 0; }}
  .archive a {{ color: #8b4513; }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>◇ 每日新聞 · 古風漫畫 ◇</h1>
      <p>{TODAY} · 以古觀今，以笑抗愁</p>
    </header>
"""
for s in stories:
    source_url = s.get('source_url', '').strip()
    source_html = (
        f'<p class="source">🔗 <a href="{source_url}" target="_blank" rel="noopener">原始新聞 ↗</a></p>'
        if source_url else ''
    )
    html += f"""
    <article class="comic" id="story-{s['story_index']}">
      <h2>{s['title']}</h2>
      <p class="tagline">{s['tagline']}</p>
      <img src="{s['img_filename']}" alt="{s['title']}">
      <p class="body">{s['body']}</p>
      {source_html}
    </article>
"""
html += f"""
    <footer>
      ◇ 由 GitHub Actions + OpenAI 於每日 8:30 自動生成 ◇<br>
      歷史存檔：查看 repo 的 /docs/ 資料夾
    </footer>
  </div>
</body>
</html>
"""

# Save today's file + update index.html (latest)
(OUT_DIR / f"{TODAY}.html").write_text(html, encoding="utf-8")
(OUT_DIR / "index.html").write_text(html, encoding="utf-8")
print(f"  ✓ HTML saved: {TODAY}.html + index.html")

# ===== Step 5: Broadcast to LINE =====
print("Step 5: Broadcasting to LINE...")

# Build Flex Message carousel (up to 12 bubbles; we use {TOP_N})
bubbles = []
for s in stories:
    source_url = s.get("source_url", "").strip()
    # Build the footer buttons: always "閱讀完整" (anchor-linked to this story),
    # plus "新聞出處" if we have a source URL
    footer_buttons = [{
        "type": "button",
        "style": "primary",
        "color": "#8B4513",
        "action": {
            "type": "uri",
            "label": "閱讀完整",
            "uri": f"{PAGES_URL}/{TODAY}.html#story-{s['story_index']}",
        },
    }]
    if source_url:
        footer_buttons.append({
            "type": "button",
            "style": "secondary",
            "action": {
                "type": "uri",
                "label": "新聞出處",
                "uri": source_url,
            },
        })

    bubbles.append({
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": f"{PAGES_URL}/{s['img_filename']}",
            "size": "full",
            "aspectRatio": "1:1",
            "aspectMode": "cover",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": s["title"], "weight": "bold", "size": "lg", "wrap": True, "color": "#8B0000"},
                {"type": "text", "text": s["tagline"], "size": "xs", "color": "#6B4423", "wrap": True, "margin": "sm"},
                {"type": "text", "text": s["body"], "size": "sm", "color": "#2C1810", "wrap": True, "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": footer_buttons,
        },
    })

flex_message = {
    "type": "flex",
    "altText": f"📰 今日新聞漫畫 · {TODAY}",
    "contents": {"type": "carousel", "contents": bubbles},
}

line_resp = requests.post(
    "https://api.line.me/v2/bot/message/broadcast",
    headers={
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"messages": [flex_message]},
    timeout=30,
)
if line_resp.status_code == 200:
    print(f"  ✓ LINE broadcast sent")
else:
    print(f"  ✗ LINE broadcast failed: {line_resp.status_code} {line_resp.text}")
    # Don't raise — HTML is still generated

print(f"\n✓ Done for {TODAY}")
print(f"  View at: {PAGES_URL}")
