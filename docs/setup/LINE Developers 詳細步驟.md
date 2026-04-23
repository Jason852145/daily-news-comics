# LINE Developers 帳號 + Messaging API Channel 建立步驟（超詳細版）

> 目標：拿到一個機器人的 **Channel Access Token**，後面 GitHub Actions 要靠這個 token 幫你發訊息。
>
> 時間：約 15–25 分鐘
>
> 你會用到：平常那個 LINE 帳號（跟朋友聊天的那個就好）

---

## 📱 開始前的心理準備

LINE Developers 介面全英文，有些專有名詞第一次看會懵，我都幫你翻譯了。**照步驟做，不用懂那些術語也能完成**。

重要名詞速記：
- **Provider**（供應商）= 你的「公司 / 組織」的容器（個人用隨便填名字就好）
- **Channel**（頻道）= 一個機器人的設定（一個 Provider 可以裝很多個 Channel）
- **Messaging API** = 讓機器人能發訊息的 API 類型（另外還有 LINE Login 等，我們不用）
- **Channel Access Token** = 機器人的「通行證」，有這個就能發訊息
- **User ID / Broadcast** = 發給特定人 vs 發給所有好友（我們用後者，簡單）

---

## 🚀 Part 1：註冊 LINE Developers 開發者帳號

### Step 1-1：打開官網

打開瀏覽器，輸入：
```
https://developers.line.biz/console/
```

或 google 搜尋「LINE Developers」第一個連結。

### Step 1-2：登入

頁面正中央會看到兩個選項：
- **Log in with LINE account** ← 選這個
- Log in with business account

點 **Log in with LINE account**，會跳出 LINE 登入視窗。

**三種登入方式**（選你方便的）：
- A. Email + 密碼（你平常 LINE 的那組）
- B. 手機掃 QR code（最快）
- C. 手機號碼

### Step 1-3：首次登入填資料

第一次登入會要你建 Developer account，填：
- **Developer name**：填你的英文名（例：`Jason Chen`）
- **Email**：你常用的 email
- 勾 **I have read and agree to...**（同意條款）

按 **Create my account**。

### Step 1-4：收驗證信

LINE 會寄一封確認信到你的 email，點信裡的**驗證連結**完成驗證。

驗證完之後你會看到 **LINE Developers Console** 的主畫面，中間會寫類似 "You don't have any providers yet"。

---

## 🏢 Part 2：建立 Provider（組織容器）

### Step 2-1：點「Create」

主畫面中央有一個藍色按鈕 **Create a new provider**，按它。

（如果沒看到，右上角也會有 **+ Create** 按鈕）

### Step 2-2：填 Provider 名稱

跳出一個小視窗，只有一個欄位：
- **Provider name**：填 `Jason Personal`（隨便取，個人用無所謂，中英文都可，以後可以改）

按 **Create**。

### Step 2-3：確認

建完之後會跳到 Provider 的頁面，上方會看到你剛才填的名字。

下方有一個區塊 **Create a new channel**，顯示四種 channel 類型的卡片：
- LINE Login
- Messaging API  ← 等等要選這個
- LINE Mini App
- Blockchain

---

## 🤖 Part 3：建立 Messaging API Channel（你的機器人）

### Step 3-1：選 Messaging API

點 **Messaging API** 那張卡片（有機器人 icon）。

### Step 3-2：填機器人資訊

會跳出一個很長的表單，一個一個填：

| 欄位名稱 | 填什麼 | 說明 |
|---|---|---|
| **Channel type** | Messaging API（已選） | 不用動 |
| **Provider** | Jason Personal（已選） | 不用動 |
| **Company or owner's country or region** | Taiwan | 選你的國家 |
| **Channel icon** | （可選）上傳一張圖當機器人頭像 | 可以先跳過，之後再改 |
| **Channel name** | `每日新聞漫畫` | 這會變成機器人的「名字」，加好友時你看到的就是這個 |
| **Channel description** | `每天早上 8:30 自動推播國際新聞 SD 漫畫` | 隨便填，描述用途 |
| **Category** | 從下拉選單選 **News** | 類別 |
| **Subcategory** | 選 **General news** 或其他 | 子類別 |
| **Email address** | 你的 email | 自動填好 |
| **Privacy policy URL**（選填） | 空白 | 個人用可跳過 |
| **Terms of use URL**（選填） | 空白 | 個人用可跳過 |

下方三個**勾選框**：
- ✅ I have read and agree to the **LINE Official Account Terms of Use**
- ✅ I have read and agree to the **LINE Official Account API Terms of Use**
- （有可能第三個）I confirm that the person in charge is aware that...

全部打勾。

### Step 3-3：按 Create

按最下方藍色的 **Create** 按鈕。

會跳出一個確認視窗「Create this channel?」→ 按 **OK**（或 **Create**）。

### Step 3-4：成功

建好之後會跳到 Channel 主頁面。這時你應該看到：
- 頂端：你剛才填的 Channel name `每日新聞漫畫`
- 幾個分頁：**Basic settings** / **Messaging API** / **Roles** / **Statistics** / ...

**恭喜，機器人已經存在了。** 現在要做兩件事：拿 Token、加好友。

---

## 🔑 Part 4：拿到 Channel Access Token（最重要）

### Step 4-1：切到 Messaging API 分頁

機器人主頁上方的分頁列，點 **Messaging API**。

### Step 4-2：往下滾到 Channel access token 區塊

頁面很長，往下滾。你會看到一個標題 **Channel access token**（中間偏下的位置）。

底下寫 "Channel access token (long-lived)"（長期 token），有一個 **Issue** 藍色按鈕，下面寫 "Token not issued yet"。

### Step 4-3：按 Issue

點 **Issue** 按鈕。

按完之後原本 "Token not issued yet" 的地方會變成一長串字串，長這樣：
```
eyJhbGciOiJIUzI1NiJ9...（後面還有一大串，超過 100 個字）
```

### Step 4-4：⚠️ 關鍵：馬上複製存起來

**這串 token 就是機器人的通行證。**

1. 點右邊的 **Copy**（複製）圖示，或用滑鼠選取全部複製
2. **貼到你桌面的一個文字檔**（可以存成 `line-token.txt` 放在 `C:\Jason\claude\每日新聞\` 裡）
3. 安全注意：
   - 這 token 不要貼到公開的地方（GitHub 公開 repo、聊天群組、社群文）
   - 之後你要貼到 GitHub Secrets（安全儲存），那個可以
   - 如果不小心外洩，回來這頁按 **Reissue** 重發一把（舊的會失效）

### Step 4-5：順手記下 Bot basic ID

往上滾到頁面頂端附近，會看到：
```
Bot basic ID: @123abcde
```
（`@` 開頭 + 一串字）

這是你機器人的「帳號」，加好友時用到。**也記下來**。

---

## 🎯 Part 5：加機器人為好友（關鍵步驟）

我們要用 **Broadcast API** 發訊息 = 發給「所有好友」。如果你不加好友，你永遠收不到訊息。

### Step 5-1：找 QR code

還在 **Messaging API** 分頁，往下滾（或往上）找 **QR code** 這個區塊。

會看到一張黑白的 QR code。

### Step 5-2：手機掃碼

1. 拿你手機 → 打開 **LINE App**
2. 點右上角 **加朋友**（人形＋的圖示）
3. 選 **QR code / 行動條碼**
4. 把鏡頭對準電腦螢幕那張 QR code
5. 掃到之後 → 出現機器人頭像 + 名字「每日新聞漫畫」
6. 按 **加入 / Add**

### Step 5-3：確認好友關係

LINE 聊天列表會看到「每日新聞漫畫」出現在你的好友/官方帳號清單裡。

**點進去聊天室，隨便傳一句話測試**（例如「你好」）——機器人不會回你（我們還沒設自動回覆），這正常。

### Step 5-4：（可選）聊天室置頂

聊天室右上角選單 → **置頂聊天室**，這樣每天 8:30 訊息一來你會在最上方看到。

---

## 🔇 Part 6：關閉自動回覆（避免鬧事）

LINE 預設機器人會對任何訊息自動回「感謝您的訊息...」制式回答，我們不要這個。

### Step 6-1：打開 Response settings

還在 **Messaging API** 分頁，找到 **LINE Official Account features** 區塊。

找到 **Auto-reply messages** 這一行，旁邊有 **Edit** 按鈕，按它。

### Step 6-2：跳到 Official Account Manager

會跳到另一個網站：`manager.line.biz`（LINE 官方帳號管理器）。

這網站介面跟 Developers Console 完全不同——別慌，你要找的是**回應設定**。

**左側選單**找：
- **回應設定 / Response settings**

點進去。

### Step 6-3：調整三個開關

頁面中央會看到幾個選項：

| 選項 | 建議設定 |
|---|---|
| **聊天 / Chat** | 開啟（這樣你可以看訊息，但機器人不會自動回）|
| **自動回應訊息 / Auto-reply** | **關閉** ← 重要 |
| **AI 自動回應訊息 / Smart Reply** | **關閉** |
| **加入好友的歡迎訊息 / Greeting Messages** | 可關可不關（關掉比較清爽）|
| **Webhook** | **關閉**（我們用 Broadcast，不用 Webhook）|

### Step 6-4：存檔

有些設定會自動儲存，有些要按 **儲存 / Save**。確認一下。

---

## ✅ 完成檢查清單

做完以上步驟你應該有：

- [ ] 一個 LINE Developers 帳號（用你 LINE 登入的）
- [ ] 一個 Provider（例：`Jason Personal`）
- [ ] 一個 Messaging API Channel（例：`每日新聞漫畫`）
- [ ] 一串很長的 **Channel Access Token** 存在桌面記事本
- [ ] 一個 **Bot basic ID**（`@xxxxxx`）記下來
- [ ] 你手機 LINE 已經加了這個機器人為好友
- [ ] 機器人的自動回覆關掉了

---

## 🐛 常見卡關點

### Q: 登入 LINE Developers 一直跳回首頁
A: 瀏覽器 cookie 問題。用無痕模式或換 Chrome 試試。

### Q: Create Channel 時「Category」下拉選單沒 News 選項
A: 選相近的（Lifestyle / Media 都可以），之後能改。

### Q: Issue Token 按下去沒反應
A: 確認你在正確的 Channel 下（URL 應該有 `/console/channel/xxxxx`）。換瀏覽器或清 cache。

### Q: 加好友後聊天室沒出現機器人
A: 關掉 LINE 再開。或在 LINE 搜尋列貼 `@xxxxx`（Bot basic ID）直接搜。

### Q: 要再建一個機器人測試
A: 回到 Provider 主頁，再按 **Create a new channel** → Messaging API。一個 Provider 可以裝多個 Channel。

### Q: 想刪除這個 Channel
A: Channel 的 **Basic settings** 分頁最下方有 **Delete channel** 紅色按鈕（謹慎用）。

---

## 🔐 Token 的安全小提醒

**LINE Channel Access Token 能做什麼：**
- 代表你這個機器人，發訊息給所有好友
- 可以發 500 則/月（免費）或更多（付費）
- 不能讀別人聊天、不能亂加好友

**風險**：如果 token 外流，有人可以冒名發訊息給你所有好友（假設好友只有你，風險低；但習慣要好）。

**處理**：
- 現在放桌面記事本（暫時 OK）
- 等下要貼到 **GitHub Secrets**（加密儲存，最安全）
- **絕對不要**直接貼進 `generate.py` 或 repo 任何檔案

---

## ➡️ 下一步

做完上面 6 個 Part，你手邊會有：
1. **Channel Access Token**（放在桌面記事本）
2. **Bot basic ID**（隨手記一下就好）

然後就可以進行「主指引」（`README 設定指引.md`）的第二階段——建 GitHub repo、貼 3 個檔案、設 Secrets、開 Pages、按 Run workflow 測試。

有任何一步卡住，截圖那個畫面貼給我，我看了就知道怎麼處理。
