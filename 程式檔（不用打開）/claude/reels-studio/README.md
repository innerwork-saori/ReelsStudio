# Reels Studio 工具包

從錄音、影片或一個想法做出 9:16 短影音（IG Reels／TikTok／YouTube Shorts）的共用工具。Agents 定義在 `{{HOME}}\.claude\agents\studio-*.md`，流程手冊在 `{{HOME}}\.claude\skills\reels-studio\SKILL.md`。

| 檔案 | 用途 |
|---|---|
| `STYLE.md` | 共通製作規則：版面、固定要求、剪接／字幕／品管／文案底線、實拍素材（Pexels／Unsplash）、露臉模式、自由創作模式。**所有 agent 必讀。** |
| `my-brand\brand.json` | 這個頻道的程式設定：名稱、配色、字型（名稱＋粗細）、結尾卡、版面風格 `style`（整體風格 `preset`＋逐項調整，選項在 `reels_lib.py` 的 `STYLE_OPTIONS`／`STYLE_PRESETS`；沒寫就是原本的手作便條；`free` 是自由創作，見 STYLE.md 第 12 節）、版面規則 `layout`（標題卡、結尾卡、上方標籤開關，字幕位置大小、節奏；選項在 `LAYOUT_OPTIONS`，沒寫就是預設）。第一次使用時由問答或控制台產生，重裝不會被覆蓋 |
| `my-brand\BRAND.md` | 這個頻道給 agent 的說明：講者、受眾、文案語氣、hashtag、自由創作方向與參考帳號、長期偏好 |
| `brand_template\` | 上面兩個檔的空白範本 |
| `studio_ui.py` | 本機控制台（網頁）：用點選的方式改 brand.json／BRAND.md 並出樣張；看素材資料夾做到哪一步、播放成品、複製文案。只聽 127.0.0.1；桌面捷徑「Reels Studio」用 pythonw 開它。改 BRAND.md 時只動使用者改過的 `- 欄位：值` 那一行，其他內容保留 |
| `ui\` | 控制台的頁面（`index.html`）與圖示 |
| `brand_preview.py` | 依目前的品牌設定出一張樣張（標題卡、字幕、結尾卡、色票），並檢查品牌文字有沒有缺字 |
| `fonts.py` | 列出這台電腦上有台灣繁體字形的字型並出樣本（`list`）、檢查缺字（`check`）、推薦免費字型（`free`） |
| `transcribe.py` | 整段逐字稿（Whisper large-v3-turbo，本機 CPU，台灣繁體；音檔或影片都可以） |
| `words.py` | 切出片段音訊＋字級時間碼＋安靜區地圖（選剪接點用；`0 end` = 整支） |
| `pexels.py` | Pexels 照片／影片搜尋、預覽、下載，自動記錄攝影師標註（key 讀環境變數 `PEXELS_API_KEY`） |
| `unsplash.py` | Unsplash 照片搜尋、預覽、下載，通知 Unsplash 下載並記錄必要標註（key 讀環境變數 `UNSPLASH_ACCESS_KEY`） |
| `reels_lib.py` | 繪圖與輸出引擎：品牌載入、色票、圖形、字幕、標題卡、結尾卡、轉場、實拍素材、露臉 `Reel.face()`、音訊組裝、H.264 輸出、驗證 |
| `props.py` | 60 個現成物件（天氣、情緒、醫療、居家、工作目標），全部不畫人 |
| `TEMPLATE_clip.py` | 插圖模式的片段腳本範本（素材只有聲音） |
| `TEMPLATE_face_clip.py` | 露臉模式的片段腳本範本（主講人自己拍的影片，可混插圖） |

## 素材資料夾結構
```
<素材資料夾>\
  _reels_studio.json              ← 控制台（這個資料夾用的頻道、素材、支數、露臉、要求、確定要剪的片段）
  <錄音或影片>                    （或 <主題>_口播稿.md ← studio-script-writer，錄好後放進來）
  <檔名>_逐字稿.txt               ← studio-transcriber
  <檔名>_Reels精華片段.md          ← studio-clip-picker（長素材才有）
  _reels_work\clipN\              ← studio-reels-editor 的工作檔（seg.wav、clip.py、sheet 圖，可刪）
  <檔名>_Reels_片段N.mp4           ← studio-reels-editor
  <檔名>_Reels_文案.md             ← studio-caption-writer
  發文包\                          ← studio-publish-prep
```

## 環境需求（安裝程式會處理）
Python 3.10 以上：faster-whisper、opencc、av（含 libx264/aac）、skia-python、numpy、soundfile、Pillow。
字體：預設 `jf-openhuninn-1.1.ttf`（jf open 粉圓），裝在使用者字型資料夾。brand.json 可改成其他已安裝、有繁體中文的字型（`python fonts.py list` 查詢）；片段腳本與樣張在輸出前會自動檢查缺字。
Pexels（選用）：Windows 使用者環境變數 `PEXELS_API_KEY`。Unsplash（選用）：`UNSPLASH_ACCESS_KEY`。

## 多個頻道
每個頻道一個資料夾：預設 `my-brand\`，其他是 `my-brand-<名稱>\`（控制台「頻道設定」→「＋ 新增頻道」會建立，可以沿用現有頻道的 brand.json）。
一個素材資料夾用哪個頻道，寫在它的 `_reels_studio.json` 的 `"brand"`（資料夾名稱，或完整路徑）。`reels_lib` 依序決定頻道：環境變數 `REELS_BRAND` → 從執行中的腳本所在資料夾和工作資料夾往上找 `_reels_studio.json`（最多 4 層）→ `my-brand\`。不是預設頻道時會印出 `[reels_lib] channel: …`。
