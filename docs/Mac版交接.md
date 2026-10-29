# Mac 版交接文件

> 評估日期：2026-10-29（評估當時版本：v1.5.0）
> 狀態：**只做了評估，程式都還沒改。** 等有 Mac 可以實際測試時再開始做。
> 這份文件只放在 GitHub repo 的 `docs/`，不會被 `tools/build_release.py` 打包進使用者下載的 zip。

## 結論

做得到，工程量中等：一個 Mac 安裝程式，加上十幾處修改，不用重寫。
最大的難處不是寫程式，而是**一定要在真的 Mac 上測過**才能公開。

開工前，先用 `grep` 對照下面列的位置，確認程式碼沒有因為後來的改版而移動或改寫。行號是 v1.5.0 時的位置。

## 不用改的部分（已確認能在 Mac 上跑）

- **剪片引擎**：`reels_lib.py`、`props.py` 都是純 Python。
- **Python 套件**：`requirements.txt` 裡的 skia-python、av（PyAV）、faster-whisper、numpy、pillow、soundfile、opencc 都有 macOS 的 wheel，Apple Silicon（arm64）也有。
- **逐字稿**：`whisper_model.py` 已經固定用 `device="cpu", compute_type="int8"`，Mac 上可以直接跑。
- **影片輸出**：PyAV 內建 libx264（`reels_lib.py` 約第 997 行 `add_stream("libx264")`），不需要另外安裝 ffmpeg。
- **控制台主體**：`studio_ui.py` 是只聽 127.0.0.1 的 `ThreadingHTTPServer`，Mac 上一樣能開。
- **`win_error_of()`**（磁碟錯誤偵測，`studio_ui.py` 約第 113 行）：已經有 `if os.name != "nt"` 的判斷，Mac 會自動略過。
- **`NO_WINDOW`**：是用 `getattr(subprocess, "CREATE_NO_WINDOW", 0)` 取得的，Mac 上會是 0，不會出錯。
- **6 個 agent 和製作流程**：大致不用動（只有下面第 5 點的寫法要調整）。

## 要改的部分

原則：**共用同一套程式碼**，用 `sys.platform == "darwin"`／`os.name == "nt"` 分支處理，不要分成兩份程式碼。每一項改完都要先在 Windows 上確認沒有壞掉。

### 1. 安裝程式（最大的一塊）

現在的 `② 雙擊安裝.bat` 和 `程式檔（不用打開）/install.ps1` 只能在 Windows 上跑。Mac 要另外寫一份 `② 雙擊安裝（Mac）.command`（zsh 腳本，雙擊就會用「終端機」執行），做的事要和 `install.ps1` 一樣：

| install.ps1 的步驟 | Mac 的做法 |
|---|---|
| 1. 複製 agents、skill、工具包到 `%USERPROFILE%\.claude\`，舊檔先備份，不動 `my-brand\` | 複製到 `~/.claude/`，用同樣的備份規則 |
| 填入 `{{STUDIO}}`、`{{HOME}}` 這些路徑 | 改用 `/` 分隔的路徑（見第 5 點） |
| 2. 粉圓字型裝到 `%LOCALAPPDATA%\Microsoft\Windows\Fonts` 並寫進登錄檔 | 複製 `jf-openhuninn-1.1.ttf` 到 `~/Library/Fonts/` 就好，不用登錄 |
| 3. 檢查 Python 3.10 以上，沒有就從 python.org 下載安裝 | 檢查 `python3`。沒有的話，引導使用者下載 python.org 的 macOS universal2 安裝檔（它有附 tkinter，Homebrew 版的 Python 通常沒有） |
| 4. `pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` |
| 5. 詢問 Pexels／Unsplash 金鑰並用 `setx` 存起來 | 把 `export PEXELS_API_KEY=...` 寫進 `~/.zshrc`。注意：從桌面捷徑開的控制台不會讀到 `.zshrc`，要確認讀得到金鑰（見第 4 點） |
| 6. 複製使用說明，在桌面建立 `Reels Studio.lnk`（用 pythonw 開控制台） | 在桌面放一個 `Reels Studio.command`，內容是背景執行 `python3 studio_ui.py`；或者做成 `.app`，看起來比較正式 |
| 最後檢查 `import reels_lib, props, fonts` | 一樣 |

另外 `tools/build_release.py` 要把 `.command` 檔放進 zip，並**保留執行權限**。用 Python 的 zipfile 打包時要設定 `ZipInfo.external_attr = 0o755 << 16`，不然 Mac 解壓縮後會沒辦法執行。

### 2. 控制台裡只有 Windows 才有的功能（`studio_ui.py`）

| 函式（約略行號） | 現在的做法 | Mac 要改成 |
|---|---|---|
| `to_recycle_bin()`（約 593） | Windows Shell `SHFileOperationW` | 搬到 `~/.Trash/`（檔名重複時加後綴），或用 `osascript -e 'tell application "Finder" to delete POSIX file "..."'`，這樣才能從 Finder 復原 |
| `open_path()`：打開資料夾（約 740） | `os.startfile(p)` | `subprocess.Popen(["open", p])` |
| `open_path()`：在資料夾中顯示（約 738） | `explorer /select,` | `open -R <檔案>` |
| `open_path()`：編輯 BRAND.md／brand.json（約 742） | `notepad` | `open -e`（文字編輯）。注意「文字編輯」可能把 .json 存成 RTF，要確認它會存成純文字 |
| `_top_windows()`／`_launch_in_front()`（約 693–728） | Windows 視窗 API，把新開的視窗拉到最前面 | Mac 的 `open` 本來就會把視窗帶到前面，非 Windows 時直接呼叫 `launch()` 就好 |
| `pick_folder()`（約 684） | 在子程序裡開 tkinter 的 `askdirectory` | python.org 版通常可以直接用；不行的話改用 `osascript -e 'POSIX path of (choose folder)'` |
| 第 4 行的說明、`if sys.stdout is None` 的處理 | pythonw 沒有主控台 | Mac 沒有 pythonw，從捷徑啟動時要把輸出導到 `studio_ui.log` |

`ui/index.html` 裡的文字也要依系統調整：常見問題的 `setx` 指令、「點桌面上的 Reels Studio」、「資源回收筒」這些說法。最簡單的做法是由伺服器告訴前端目前是哪個系統，前端再切換要顯示的文字。

### 3. 字型

- `reels_lib.py` 的 `_find_font()`（約 147 行）只會找 Windows 的字型資料夾，要加上 `~/Library/Fonts`、`/Library/Fonts`、`/System/Library/Fonts`。
- `fonts.py` 約 98 行，樣本標籤寫死用 `"Microsoft JhengHei"`（微軟正黑體）。Mac 上要改用 `"PingFang TC"`（蘋方-繁）。現在找不到字型時會改用預設字型，可能會變成方框字。
- `fonts.py` 的推薦字型說明（約 34 行，「Windows 11 多半已內建」）和 `load_typeface()` 的註解要調整。
- `fonts.py list` 在 Mac 上會列出哪些字型名稱（中文名還是英文名）需要實際測試，因為 SKILL.md 的設定流程會直接把這個名稱寫進 brand.json。

### 4. Pexels／Unsplash 金鑰

- `pexels.py` 約 23 行，找不到環境變數時會去讀 Windows 登錄檔（已經有 `sys.platform == "win32"` 的判斷，Mac 不會出錯，只是讀不到）。
- 問題是：從桌面捷徑開的控制台、Claude 桌面 App 開的 agent，**不一定讀得到 `~/.zshrc` 裡的環境變數**。比較可靠的做法是在 Mac 上另外存一個設定檔，例如 `~/.claude/reels-studio/keys.env`，權限設成 600，由 `pexels.py`／`unsplash.py` 讀取。不管用哪種方式，都要守住 STYLE.md 的規定：不能印出金鑰、不能寫進對話。
- 找不到金鑰時的錯誤訊息（`pexels.py` 約 36 行、`unsplash.py` 約 28 行）會教使用者用 `setx`，Mac 上要換成對應的說明。
- STYLE.md 約 125 行也寫了 `setx`，要一起改。

### 5. agent 指示和說明文件

- 安裝時會把 `{{STUDIO}}`、`{{HOME}}` 換成實際路徑。SKILL.md 和各個 agent 檔案裡的路徑寫的是 `"{{STUDIO}}\fonts.py"`、`my-brand\fonts_sheet.png` 這種反斜線。Mac 的安裝程式可以在替換時順便把 `\` 換成 `/`，或者乾脆把原始檔全部改成 `/`（Windows 也看得懂 `/`）。
- `agents/studio-reels-editor.md` 約 19 行寫的是 `$env:REELS_BRAND='<頻道資料夾>';`（PowerShell 寫法），Mac 要寫成 `REELS_BRAND='<頻道資料夾>' python3 clip.py ...`。
- 各個檔案都寫 `python ...`，Mac 上通常要用 `python3`。可以讓 agent 自己判斷，或在安裝時替換掉。
- `agents/` 的 tools 欄位列了 `PowerShell`。Mac 上沒有 PowerShell，但還有 Bash，應該不影響，要實際確認。
- `① 先看我.html`、`說明圖片/`、`README.md`：現在的系統需求只寫 Windows，截圖也都是 Windows 畫面。要加一份 Mac 的安裝說明（至少要有：怎麼對 `.command` 按右鍵 →「打開」、終端機的畫面截圖）。

## 風險和要先決定的事

1. **一定要在真的 Mac 上測試**，至少要跑過：
   - 全新安裝（電腦上沒有 Python 的情況）
   - 打開控制台、選資料夾、新增和刪除風格、打開資料夾、在資料夾中顯示、編輯 BRAND.md
   - `fonts.py list`，以及樣張的中文字有沒有變成方框
   - 聽打一段錄音（同時記下 Apple Silicon 上的速度）
   - 剪出並輸出一支插圖模式的片段，還有一支露臉模式的片段
   - Pexels／Unsplash 搜尋（確認讀得到金鑰）
   - 再跑一次安裝，確認是更新而不是覆蓋掉 `my-brand/`
2. **Mac 的安全警告（Gatekeeper）**：從網路下載、沒有簽章的 `.command` 檔會被擋下來，跳出「無法打開，因為無法驗證開發者」。
   - 免費的做法：在說明裡教使用者「按右鍵 → 打開」，就像現在 Windows 版教大家按「仍要執行」一樣。
   - 付費的做法：加入 Apple 開發者計畫（每年 99 美元），做簽章和公證。建議先用免費的做法。
3. **Intel 還是 Apple Silicon**：建議先只支援 Apple Silicon（M1 以後的 Mac），Intel Mac 列為「應該可以，但沒測過」。
4. **兩個版本要一起維護**：之後每次改版，兩個安裝程式都要更新。CHANGELOG 要註明每項改動有沒有影響 Mac。

## 建議的進行順序

1. **先改程式本身**（第 2～5 點），每項都用系統分支處理，在 Windows 上確認完全沒有影響。這一步在 Windows 上就能做。
2. **寫 Mac 安裝程式**、更新 `build_release.py`、寫 Mac 版說明頁。
3. **在 Mac 上照「風險」第 1 點的清單完整測一次**，最好再找一位用 Mac、不是工程師的朋友，從下載開始自己裝一次。
4. 修正後發布，README 和下載頁分別放 Windows、Mac 的說明。

## 在 Mac 版做好之前

在分享頁（https://lab.heysaori.com/reelsstudio.html）和索取表單上註明「目前只支援 Windows」，免得用 Mac 的人填了表單卻裝不起來。
