"""
One-shot script: create a LINE Rich Menu (bottom button bar) and set as default.

Usage:
  LINE_CHANNEL_ACCESS_TOKEN=xxxx python setup-richmenu.py

Layout (2500 x 843 compact):
  ┌──────────┬──────────┬──────────┐
  │  今日     │  昨日     │  清單     │
  └──────────┴──────────┴──────────┘
  Tapping each sends a text message to the bot that our Worker already handles.
"""
import os
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
if not TOKEN:
    print("ERROR: LINE_CHANNEL_ACCESS_TOKEN env var required", file=sys.stderr)
    sys.exit(1)

WIDTH, HEIGHT = 2500, 843
OUT_IMG = Path(__file__).parent / "richmenu.png"

# ───── Style (matches bot's brown/beige aesthetic) ─────────────────
BG = (245, 230, 200)          # #f5e6c8
BORDER = (201, 166, 107)       # #c9a66b
BTN_BG = (139, 69, 19)         # #8b4513
BTN_BG_ALT = (160, 82, 45)     # #a0522d  (alternating subtle)
TEXT = (255, 255, 255)
SUB = (245, 230, 200)

BUTTONS = [
    {"icon": "📰", "label": "今日新聞", "send": "今日"},
    {"icon": "📅", "label": "昨日新聞", "send": "昨日"},
    {"icon": "📋", "label": "歷史清單", "send": "清單"},
]

# ───── Draw image ──────────────────────────────────────────────────
def pick_font(size, emoji=False):
    # Windows font fallbacks. PIL on Windows can load emoji from seguiemj.ttf
    candidates = (
        ["C:/Windows/Fonts/seguiemj.ttf"] if emoji else []
    ) + [
        "C:/Windows/Fonts/msjh.ttc",  # 微軟正黑體
        "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

img = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

col_w = WIDTH // 3
label_font = pick_font(130)
icon_font = pick_font(180, emoji=True)

for i, btn in enumerate(BUTTONS):
    x0 = i * col_w
    x1 = (i + 1) * col_w if i < 2 else WIDTH
    # background block (alternating shade for visual separation)
    fill = BTN_BG if i % 2 == 0 else BTN_BG_ALT
    draw.rectangle([x0, 0, x1, HEIGHT], fill=fill)

    # vertical separator between buttons
    if i > 0:
        draw.line([(x0, 40), (x0, HEIGHT - 40)], fill=BORDER, width=3)

    cx = (x0 + x1) // 2

    # icon (centered, upper portion)
    icon_bbox = draw.textbbox((0, 0), btn["icon"], font=icon_font)
    icon_w = icon_bbox[2] - icon_bbox[0]
    icon_h = icon_bbox[3] - icon_bbox[1]
    draw.text(
        (cx - icon_w // 2, 180 - icon_bbox[1]),
        btn["icon"],
        font=icon_font,
        embedded_color=True,  # keeps emoji colors
    )

    # label (centered, lower portion)
    label_bbox = draw.textbbox((0, 0), btn["label"], font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text(
        (cx - label_w // 2, 500),
        btn["label"],
        font=label_font,
        fill=TEXT,
    )

# top + bottom border bars
draw.rectangle([0, 0, WIDTH, 8], fill=BORDER)
draw.rectangle([0, HEIGHT - 8, WIDTH, HEIGHT], fill=BORDER)

img.save(OUT_IMG, "PNG", optimize=True)
print(f"✓ image saved: {OUT_IMG} ({OUT_IMG.stat().st_size // 1024} KiB)")

# ───── LINE API calls ─────────────────────────────────────────────
HEADERS_JSON = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
HEADERS_IMG = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "image/png"}

# Purge any existing default menus so we don't accumulate zombies
print("Cleaning up old rich menus...")
r = requests.get("https://api.line.me/v2/bot/richmenu/list", headers=HEADERS_JSON, timeout=30)
r.raise_for_status()
for rm in r.json().get("richmenus", []):
    rid = rm["richMenuId"]
    dr = requests.delete(f"https://api.line.me/v2/bot/richmenu/{rid}", headers=HEADERS_JSON, timeout=30)
    print(f"  deleted {rid}: {dr.status_code}")

# 1) Create rich menu definition
print("Creating rich menu...")
definition = {
    "size": {"width": WIDTH, "height": HEIGHT},
    "selected": True,
    "name": "Daily News Menu v1",
    "chatBarText": "新聞選單",
    "areas": [
        {
            "bounds": {"x": i * col_w, "y": 0, "width": col_w, "height": HEIGHT},
            "action": {"type": "message", "text": btn["send"]},
        }
        for i, btn in enumerate(BUTTONS)
    ],
}
r = requests.post(
    "https://api.line.me/v2/bot/richmenu",
    headers=HEADERS_JSON,
    json=definition,
    timeout=30,
)
r.raise_for_status()
rich_menu_id = r.json()["richMenuId"]
print(f"  ✓ rich menu id: {rich_menu_id}")

# 2) Upload image
print("Uploading image...")
with OUT_IMG.open("rb") as f:
    r = requests.post(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        headers=HEADERS_IMG,
        data=f.read(),
        timeout=60,
    )
r.raise_for_status()
print(f"  ✓ image uploaded")

# 3) Set as default for ALL users (including new joins)
print("Setting as default menu for all users...")
r = requests.post(
    f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
    headers=HEADERS_JSON,
    timeout=30,
)
r.raise_for_status()
print(f"  ✓ default menu set (status {r.status_code})")

print("\n🎉 Rich menu live. Open LINE chat with the bot — menu should appear at the bottom.")
print("   (If you don't see it immediately, close and reopen the chat.)")
