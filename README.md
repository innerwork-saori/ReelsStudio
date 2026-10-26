# Reels Studio 短影音小幫手

**目前版本：第一版（v1.1.0，2026-10-26）**｜[版本記錄](CHANGELOG.md)

讓 Claude 幫你把錄音、影片，或一個還沒錄的想法，做成直式短影音（IG Reels／TikTok／YouTube Shorts）：聽打逐字稿、挑出精華片段、剪成有字幕和插圖的 9:16 影片，再寫好貼文文案。

## 👉 [下載 Reels Studio（Windows）](https://github.com/innerwork-saori/ReelsStudio/releases/latest/download/ReelsStudio.zip)

點上面的連結就會下載 `ReelsStudio.zip`。不要按這個頁面上方綠色的「Code」按鈕，那是給寫程式的人用的。
想看每一版改了什麼，到 [Releases](https://github.com/innerwork-saori/ReelsStudio/releases)。

## 需要什麼

- Windows 電腦
- [Claude 桌面 App](https://claude.ai/download)，而且你的方案可以使用 Claude Code
- 網路連線（安裝時會下載 Python 和需要的套件）
- C 槽至少空出 **3 GB**：Python 和套件約 0.4 GB、語音辨識模型約 1.6 GB（第一次聽打時下載），其餘留給安裝暫存和前幾支影片。之後每支影片約 50–80 MB（成品＋可刪的工作檔）。

## 安裝：三步驟

1. 在下載的 `ReelsStudio.zip` 上按右鍵 → **「解壓縮全部」**。
2. 打開解壓縮出來的資料夾，先看 **`① 先看我`**，再雙擊 **`② 雙擊安裝`**，照畫面回答。
3. 把 Claude 桌面 App 完全關掉再打開。

`① 先看我` 是一份可以打勾的檢查表，從安裝、建立頻道設定，一路帶你做完第一支影片。

## 它能做什麼

| 你手上有 | 跟 Claude 說 |
|---|---|
| 一段很長的錄音或影片（Podcast、訪談、講座、直播） | 幫我把這個檔案做成 3 支 reels |
| 一支自己拍的口播或 vlog | 幫我剪這支 |
| 一篇文章或一個想法 | 幫我把這篇寫成 reels 口播稿 |
| 已經剪好的影片 | 幫我寫文案、幫我整理發文包 |

安裝後桌面會有一個 **Reels Studio** 控制台：用點選的方式設定頻道的配色、字型、版面風格和結尾卡，選要剪的片段，播放成品、一鍵複製文案。

### 五種版面風格

每個頻道可以選不同的風格，也可以逐項調整字幕、標題卡、背景、線條、動畫和結尾卡。

![五種版面風格：手作便條、俐落簡約、雜誌感、筆記本、街頭活力](docs/styles.png)

## 使用須知與免責聲明

- **成品請自己檢查**：逐字稿、字幕、精華片段和貼文文案都是 AI 產生的，可能有錯字、聽錯或斷句不對。發布前請完整看過影片、讀過文案。
- **哪些資料會交給 Claude**：語音辨識（聽打）在你自己的電腦上執行；但逐字稿、文案，以及剪片時用來檢查畫面的截圖，會在對話中交給 Claude（Anthropic）處理，適用 Anthropic 的使用條款與隱私政策。含有不公開內容的素材請自行斟酌。
- **素材的權利由你負責**：請確認你有權使用錄音、影片、照片與音樂，來賓或入鏡的人同意公開，並遵守 Pexels 素材授權和各社群平台的規範。
- **安裝會改動這台電腦**：安裝程式會下載安裝 Python 與套件、安裝字型、寫入 `%USERPROFILE%\.claude\`，選填的 Pexels 金鑰會存成使用者環境變數。
- **非官方工具**：Reels Studio 是個人作品，與 Anthropic、Meta（Instagram）、TikTok、Google（YouTube）沒有關係。
- **不提供任何保證**：本工具依「現狀」提供，作者不保證它沒有錯誤或適合特定用途；因使用本工具或其成品造成的任何損失，作者不負責任（詳見 [LICENSE](LICENSE)）。

## 授權

- Reels Studio（程式、說明文件、控制台）採用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.zh-hant)：可以分享、修改，但要註明出處（Saori），而且**這套工具本身不能用於商業用途**：不能拿去賣、收費散布，或包裝成付費的產品、課程、平台。全文見 [LICENSE](LICENSE)。
- **用它做出來的影片不受這個限制，可以商業使用**：例如店家宣傳、業配、幫客戶做影片收費都可以，影片、圖片和文案怎麼用由你決定。
- 隨附的字型 jf open 粉圓由 justfont 製作，採用 SIL Open Font License 1.1（見 `程式檔（不用打開）/font/OFL.txt`），不受上面的 CC BY-NC 限制。

## 製作

**Saori**｜軟體工程師・系統分析師・生涯諮詢師
[更多 Saori 的作品與聯絡方式 →](https://lab.heysaori.com/links.html)

---

<details>
<summary>給開發者</summary>

- `程式檔（不用打開）/claude/`：安裝到 `%USERPROFILE%\.claude\` 的 agents、skill 與工具包（`reels-studio/`，說明見裡面的 `README.md`）。檔案裡的 `{{STUDIO}}`、`{{HOME}}` 會在安裝時換成實際路徑。
- `程式檔（不用打開）/install.ps1`：安裝程式本體；`② 雙擊安裝.bat` 只負責找到它並執行（.bat 必須維持純 ASCII、CRLF）。
- 打包 Release：`python tools/build_release.py` → `dist/ReelsStudio.zip`（檔案直接放在 zip 最上層，解壓縮後只有一層資料夾）。上傳時檔名維持 `ReelsStudio.zip`，首頁的下載連結才會一直指向最新版；版本號寫在 `程式檔（不用打開）/VERSION`。

</details>
