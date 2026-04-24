// Daily News LINE Bot — Cloudflare Worker webhook
//
// Routes:
//   POST /webhook   → LINE Messaging API webhook (events from LINE servers)
//   GET  /          → health check
//
// Events handled:
//   follow          → send welcome + today's news
//   message (text)  → reply based on keyword:
//                       今日 / today / 最新 / 新聞  → today
//                       昨日 / 昨天 / yesterday     → yesterday
//                       日期 M/D or YYYY-MM-DD      → that day (if archived)
//                       清單 / 列表 / list           → last 7 archived dates
//                       anything else                → help text

const LINE_API = "https://api.line.me/v2/bot/message";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return new Response("daily-news-line-bot ok", { status: 200 });
    }

    if (request.method === "POST" && url.pathname === "/webhook") {
      return handleWebhook(request, env, ctx);
    }

    return new Response("not found", { status: 404 });
  },

  // Cloudflare cron triggers fire here. We POST repository_dispatch to GitHub,
  // which in turn fires the daily.yml workflow — CF cron is second-accurate,
  // unlike GitHub's free-tier cron which can lag 6+ hours.
  async scheduled(event, env, ctx) {
    ctx.waitUntil(triggerDailyWorkflow(env));
  },
};

async function triggerDailyWorkflow(env) {
  const repo = env.GITHUB_REPO; // e.g. "Jason852145/daily-news-comics"
  const res = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "daily-news-line-bot-cron",
    },
    body: JSON.stringify({ event_type: "daily-news-trigger" }),
  });
  if (!res.ok) {
    console.error("GitHub dispatch failed:", res.status, await res.text());
  } else {
    console.log(`GitHub dispatch OK → ${repo}`);
  }
}

async function handleWebhook(request, env, ctx) {
  const bodyText = await request.text();
  const signature = request.headers.get("x-line-signature") || "";

  const valid = await verifySignature(env.LINE_CHANNEL_SECRET, bodyText, signature);
  if (!valid) {
    return new Response("bad signature", { status: 401 });
  }

  let payload;
  try {
    payload = JSON.parse(bodyText);
  } catch {
    return new Response("bad json", { status: 400 });
  }

  // ACK LINE immediately (must be <5s). Process events async via waitUntil.
  ctx.waitUntil(processEvents(payload.events || [], env));
  return new Response("ok", { status: 200 });
}

async function processEvents(events, env) {
  for (const ev of events) {
    try {
      if (ev.type === "follow") {
        await handleFollow(ev, env);
      } else if (ev.type === "message" && ev.message?.type === "text") {
        await handleTextMessage(ev, env);
      }
    } catch (err) {
      console.error("event handler error:", err, JSON.stringify(ev));
    }
  }
}

// ───── Event handlers ─────────────────────────────────────────────

async function handleFollow(ev, env) {
  const replyToken = ev.replyToken;
  const latest = await fetchLatestStories(env);

  const greetingText = latest
    ? `歡迎加入每日新聞漫畫！\n\n這是今天 (${latest.date}) 的國際新聞，每天早上 06:12 會自動送達。\n\n隨時輸入：\n・「今日」看今天\n・「昨日」看昨天\n・「4/21」查特定日期\n・「清單」看可查日期`
    : `歡迎加入每日新聞漫畫！\n\n每天早上 06:12 會自動送達國際新聞摘要。\n明天見 👋`;

  const messages = [{ type: "text", text: greetingText }];
  if (latest) messages.push(buildCarousel(latest));

  await replyMessage(env, replyToken, messages);
}

async function handleTextMessage(ev, env) {
  const replyToken = ev.replyToken;
  const raw = (ev.message.text || "").trim();
  const text = raw.toLowerCase();

  // List of archived dates
  if (/^(清單|列表|list|歷史)$/i.test(text)) {
    const idx = await fetchIndex(env);
    if (!idx || !idx.dates?.length) {
      return replyMessage(env, replyToken, [{ type: "text", text: "目前還沒有歷史存檔。" }]);
    }
    const list = idx.dates.slice(0, 7).map((d, i) => `${i + 1}. ${d}`).join("\n");
    return replyMessage(env, replyToken, [
      { type: "text", text: `最近可查日期：\n${list}\n\n輸入日期（例如 4/21）可查該日新聞。` },
    ]);
  }

  // Today
  if (/^(今日|today|最新|新聞|今天)$/i.test(text)) {
    const s = await fetchLatestStories(env);
    if (!s) return replyMessage(env, replyToken, [{ type: "text", text: "今日尚未產出新聞。" }]);
    return replyMessage(env, replyToken, [buildCarousel(s)]);
  }

  // Yesterday
  if (/^(昨日|昨天|yesterday)$/i.test(text)) {
    const idx = await fetchIndex(env);
    const yest = idx?.dates?.[1]; // index 0 is today, 1 is yesterday
    if (!yest) return replyMessage(env, replyToken, [{ type: "text", text: "昨天沒有存檔。" }]);
    const s = await fetchStoriesByDate(env, yest);
    if (!s) return replyMessage(env, replyToken, [{ type: "text", text: `找不到 ${yest} 的存檔。` }]);
    return replyMessage(env, replyToken, [buildCarousel(s)]);
  }

  // Date format: 4/21, 04/21, 2026-04-21, 2026/04/21
  const dateKey = parseDateKey(raw);
  if (dateKey) {
    const s = await fetchStoriesByDate(env, dateKey);
    if (!s) {
      return replyMessage(env, replyToken, [
        { type: "text", text: `找不到 ${dateKey} 的新聞，輸入「清單」看可查日期。` },
      ]);
    }
    return replyMessage(env, replyToken, [buildCarousel(s)]);
  }

  // Help / default
  return replyMessage(env, replyToken, [
    {
      type: "text",
      text:
        "指令：\n・今日 — 今天新聞\n・昨日 — 昨天新聞\n・4/21 或 2026-04-21 — 特定日期\n・清單 — 最近可查日期",
    },
  ]);
}

// ───── LINE API helpers ────────────────────────────────────────────

async function replyMessage(env, replyToken, messages) {
  const res = await fetch(`${LINE_API}/reply`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.LINE_CHANNEL_ACCESS_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ replyToken, messages }),
  });
  if (!res.ok) {
    console.error("LINE reply failed:", res.status, await res.text());
  }
}

function buildCarousel(day) {
  const bubbles = day.stories.map((s) => ({
    type: "bubble",
    hero: {
      type: "image",
      url: s.image_url,
      size: "full",
      aspectRatio: "1:1",
      aspectMode: "cover",
    },
    body: {
      type: "box",
      layout: "vertical",
      spacing: "sm",
      contents: [
        { type: "text", text: s.title, weight: "bold", size: "lg", wrap: true, color: "#8B0000" },
        { type: "text", text: s.tagline, size: "xs", color: "#6B4423", wrap: true, margin: "sm" },
        { type: "text", text: s.body, size: "sm", color: "#2C1810", wrap: true, margin: "md" },
      ],
    },
    footer: {
      type: "box",
      layout: "vertical",
      spacing: "sm",
      contents: [
        {
          type: "button",
          style: "primary",
          color: "#8B4513",
          action: { type: "uri", label: "閱讀完整", uri: s.anchor_url },
        },
        ...(s.source_url
          ? [
              {
                type: "button",
                style: "secondary",
                action: { type: "uri", label: "新聞出處", uri: s.source_url },
              },
            ]
          : []),
      ],
    },
  }));

  return {
    type: "flex",
    altText: `📰 新聞漫畫 · ${day.date}`,
    contents: { type: "carousel", contents: bubbles },
  };
}

// ───── Data fetchers (read JSON from GitHub Pages) ────────────────

async function fetchIndex(env) {
  const res = await fetch(`${env.PAGES_URL}/stories/index.json`, {
    cf: { cacheTtl: 60 }, // cache 60s — accept slight staleness
  });
  if (!res.ok) return null;
  return res.json();
}

async function fetchLatestStories(env) {
  const idx = await fetchIndex(env);
  if (!idx?.latest) return null;
  return fetchStoriesByDate(env, idx.latest);
}

async function fetchStoriesByDate(env, date) {
  const res = await fetch(`${env.PAGES_URL}/stories/${date}.json`, {
    cf: { cacheTtl: 300 },
  });
  if (!res.ok) return null;
  return res.json();
}

// ───── Utilities ───────────────────────────────────────────────────

function parseDateKey(input) {
  // Accept: 4/21, 04/21, 2026-04-21, 2026/04/21
  const today = new Date();
  const yyyy = today.getFullYear();

  let m, d, y;
  let match;

  match = input.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
  if (match) {
    y = parseInt(match[1]);
    m = parseInt(match[2]);
    d = parseInt(match[3]);
  } else if ((match = input.match(/^(\d{1,2})[/-](\d{1,2})$/))) {
    y = yyyy;
    m = parseInt(match[1]);
    d = parseInt(match[2]);
  } else {
    return null;
  }

  if (m < 1 || m > 12 || d < 1 || d > 31) return null;
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

async function verifySignature(secret, body, signatureB64) {
  if (!secret || !signatureB64) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const digest = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  const expected = btoa(String.fromCharCode(...new Uint8Array(digest)));
  // constant-time compare
  if (expected.length !== signatureB64.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ signatureB64.charCodeAt(i);
  }
  return diff === 0;
}
