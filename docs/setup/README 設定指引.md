# 雲端每日新聞 LINE Bot · 設定指引

> 目標：每天早上 8:30，LINE 收到一則「三張 SD 古風漫畫 + 新聞摘要」的訊息，電腦關機也照常送。
>
> 架構：GitHub Actions 雲端定時跑 → Python 抓新聞、叫 OpenAI 產圖 → GitHub Pages 免費 host 網頁 → LINE Bot 推播訊息給你
>
> 預估時間：第一次設定約 60–90 分鐘。設完就終身自動。

---

## 📋 你要先準備的東西

- [ ] 一個信箱（給 GitHub / LINE Developers 註冊用）
- [ ] 你的 LINE 帳號（用來加機器人好友）
- [ ] 手機（掃 QR code 加好友）
- [ ] `C:\Jason\claude\每日新聞\openai-key.txt` 裡面的 OpenAI API key

---

## 第一階段：開帳號（約 30 分鐘）

### 步驟 1️⃣：註冊 GitHub 帳號

1. 打開 <https://github.com/signup>
2. 填 email、密碼、username（**username 會變成你網址的一部分**，例如 `jason-chen`，挑好記的）
3. 收信收驗證碼
4. 完成

**記下你的 GitHub username**（後面會用到多次）

### 步驟 2️⃣：建一個新 repo

1. 登入 GitHub 後按右上角 **+** → **New repository**
2. Repository name 填：`daily-news-comics`
3. 設為 **Public**（公開，這樣 GitHub Pages 免費可用）
4. 勾選 **Add a README file**（這樣會自動初始化）
5. 按 **Create repository**

**此時你會得到一個 URL 像：** `https://github.com/你的username/daily-news-comics`

### 步驟 3️⃣：註冊 LINE Developers

1. 打開 <https://developers.line.biz/console/>
2. 選 **Log in with LINE account**，用你平常的 LINE 帳號登入
3. 第一次會叫你建 Developer Account，填你的名字 + email
4. 同意條款

### 步驟 4️⃣：建一個 Provider

1. LINE Developers Console 登入後，按 **Create a new provider**
2. Name 填：`Jason Personal`（隨便）
3. 按 Create

### 步驟 5️⃣：建一個 Messaging API Channel（機器人）

1. 進剛建好的 Provider 頁面
2. 點 **Create a new channel** → 選 **Messaging API**
3. 填：
   - Channel name：`每日新聞漫畫` (這會變成機器人的名字)
   - Channel description：`每天早上推播國際新聞 SD 漫畫`
   - Category：隨便選（例如「News」）
   - Subcategory：隨便
   - 勾選同意條款
4. 按 **Create**

### 步驟 6️⃣：拿到 Channel Access Token

1. 進入剛建好的 Channel
2. 切到 **Messaging API** 分頁
3. 往下滾到 **Channel access token**（長期 token）
4. 按 **Issue**
5. **複製**跑出來的 token 字串（很長），**貼到你桌面一個記事本暫存**
6. 同一頁往上看到 **Bot basic ID**（例如 `@123abcde`），也記下來

### 步驟 7️⃣：加機器人為好友

1. 同一 Channel 的 **Messaging API** 分頁，會看到一張 **QR code**
2. 拿你手機打開 LINE → 加朋友 → 掃 QR code → 加好友
3. **這步是關鍵**：這樣 Broadcast 訊息才能發到你手機

### 步驟 8️⃣：關閉自動回覆（避免機器人每次你傳訊息都亂回）

1. Channel 的 **Messaging API** 分頁
2. 往下找到 **Auto-reply messages**
3. 按旁邊的 **Edit**（會跳到 LINE Official Account Manager）
4. 把 **自動回應訊息** 關掉
5. 把 **歡迎訊息** 關掉（可選）
6. **加入好友的歡迎** 也關掉

---

## 第二階段：放檔案上 GitHub（約 30 分鐘）

### 步驟 9️⃣：複製 3 個檔案到 repo

我已經幫你準備好 3 個檔案在 `C:\Jason\claude\每日新聞\cloud-line-bot\` 資料夾裡。

**在 GitHub 上操作**（不需要安裝 git，直接用瀏覽器）：

#### 檔案 A：`.github/workflows/daily.yml`
1. 進 repo 首頁
2. 按 **Add file** → **Create new file**
3. 檔名欄輸入：`.github/workflows/daily.yml`（注意前面那個點和斜線，GitHub 會自動建資料夾）
4. 打開你電腦的 `C:\Jason\claude\每日新聞\cloud-line-bot\daily.yml`，全選複製
5. 貼到 GitHub 的編輯框
6. 拉到頁面最下方，按 **Commit changes** → **Commit changes**

#### 檔案 B：`generate.py`
1. 同樣流程
2. 檔名：`generate.py`
3. 內容：從 `C:\Jason\claude\每日新聞\cloud-line-bot\generate.py` 複製貼上

#### 檔案 C：`requirements.txt`
1. 同樣流程
2. 檔名：`requirements.txt`
3. 內容：從 `C:\Jason\claude\每日新聞\cloud-line-bot\requirements.txt` 複製貼上

### 步驟 🔟：設 GitHub Secrets（安全存放 key）

1. 進 repo 首頁
2. 點 **Settings**（上方 tab，要點一下 repo 的名字那列才會出現）
3. 左側選單 → **Secrets and variables** → **Actions**
4. 按 **New repository secret**

**新增第一個 secret：**
- Name: `OPENAI_API_KEY`
- Value: 打開 `C:\Jason\claude\每日新聞\openai-key.txt` 裡的內容，貼進去
- 按 **Add secret**

**新增第二個 secret：**
- 再按 **New repository secret**
- Name: `LINE_CHANNEL_ACCESS_TOKEN`
- Value: 步驟 6 你記下的那串長 token
- 按 **Add secret**

### 步驟 1️⃣1️⃣：開啟 GitHub Pages

1. Settings 左側選單 → **Pages**
2. **Source**：選 **Deploy from a branch**
3. **Branch**：選 `main`（或你的主分支名稱），資料夾選 **/docs**
4. 按 **Save**
5. 等 1–2 分鐘，這頁上方會出現你的網址：`https://你的username.github.io/daily-news-comics/`
6. 把這個網址記下來（第一次可能跑完才有內容，之後每天會自動更新）

### 步驟 1️⃣2️⃣：手動跑一次測試

1. 進 repo 首頁 → 上方 tab **Actions**
2. 左側看到 **Daily News Comics**
3. 點進去 → 右邊按 **Run workflow** → 再按綠色 **Run workflow**
4. 等 2–5 分鐘跑完（會看到綠色勾勾）
5. **預期**：
   - 手機 LINE 會收到一則卡片訊息（三張 SD 漫畫 + 按鈕）
   - GitHub Pages 網址打開會看到完整 HTML
   - repo 的 `/docs/` 資料夾會多出 HTML + PNG

**如果失敗：**
- 點失敗那次 run，看 log 紅色字是什麼錯
- 截圖給我，我們一起除錯

---

## 第三階段：自動化生效

從明天起，**每天早上 8:30**（實際因 GitHub Actions 排隊可能 8:30–8:45 之間）你的 LINE 會自動收到新聞漫畫。

---

## 常見問題

### Q: 不想讓別人看到我的新聞漫畫網址怎麼辦？
用一個難猜的 repo 名（例如 `my-secret-news-xyz123`）。Public repo 的網址除非有人猜對，否則找不到。

### Q: OpenAI 扣款太兇怎麼辦？
到 <https://platform.openai.com/settings/organization/limits> 設月上限 US$3。每天 3 張 low 品質圖約 US$0.03，一個月約 US$1，設 US$3 很安全。

### Q: LINE 訊息跟以前不一樣、超醜？
這是 Flex Message 格式，可以很漂亮，但如果圖片 URL 有問題會顯示空白。先確認 GitHub Pages 網址能打開 PNG 檔。

### Q: 每天早上沒收到訊息？
1. 檢查 GitHub Actions 那次 run 是成功還是失敗（紅色 = 失敗）
2. 檢查有沒有把機器人加好友（步驟 7）
3. 檢查 LINE channel access token 是不是過期（長期 token 有 30 天的 issue 限制但不會自動過期，除非你手動 reissue）

### Q: 我想改風格怎麼辦？
改 `generate.py` 裡面 `STYLE_SUFFIX` 那個變數，commit 後下次就用新風格。

### Q: 我想改時間怎麼辦？
改 `.github/workflows/daily.yml` 裡面 `cron: '30 0 * * *'` 這行。注意 GitHub 用 **UTC 時間**，台灣是 UTC+8，所以：
- 台灣 8:30 → UTC 0:30 → `'30 0 * * *'`
- 台灣 18:00 → UTC 10:00 → `'0 10 * * *'`

---

## 這個系統你之後能做的事

- 新聞來源換成你有興趣的（體育、科技、財經）→ 改 `generate.py` 裡的 RSS URL
- 不只三則，改成五則或十則 → 改 `TOP_N = 3` 改成 `5`
- 換風格（水墨、水彩、3D 渲染、Pixel art）→ 改 `STYLE_SUFFIX`
- 換語言（用英文寫給朋友看）→ 改 prompt
- 加天氣 / 股市 / 生日提醒 → 擴充 `generate.py`

先把基本版跑起來，之後你想客製隨時找我。
