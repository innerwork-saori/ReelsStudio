# Reels Studio：Mac 安裝說明（試用版）

> Reels Studio 是為 Windows 做的，**還沒有在 Mac 上正式測試過**。這份說明是讓你 Mac 上的 Claude 照著步驟幫你安裝。聽打、挑片段、剪片、寫文案這些主要功能應該可以用，但控制台有幾個按鈕在 Mac 上不能用（見下面的清單）。遇到問題請截圖回報給 Saori。

---

## 第一部分：給你看的

### 需要什麼

- Mac 電腦，macOS 11（Big Sur）以上。M 系列晶片（M1–M4）比較沒問題；Intel 晶片的 Mac 沒試過。
- [Claude 桌面 App](https://claude.ai/download)，而且你的方案可以使用 Claude Code。
- 網路連線。
- 至少空出 **3 GB** 空間。
- 你的 Mac 登入密碼（安裝 Python 時會用到）。

### 安裝步驟

1. 下載 [ReelsStudio.zip](https://github.com/innerwork-saori/ReelsStudio/releases/latest/download/ReelsStudio.zip)，在「下載項目」裡雙擊它，會解壓縮出一個 `ReelsStudio` 資料夾。
   - 資料夾裡的 `② 雙擊安裝.bat` 是 Windows 用的，**不用理它**。
2. 打開 Claude 桌面 App，切到 **Code**，選擇剛剛解壓縮出來的 `ReelsStudio` 資料夾。
3. 把下面這段話貼給 Claude：

   > 請照著這個資料夾裡的 `INSTALL_MAC.md`「第二部分：給 Claude 的安裝步驟」，幫我在這台 Mac 上安裝 Reels Studio。每一步做之前先用簡單的話告訴我要做什麼。

4. 照 Claude 的指示操作。過程中**需要你自己動手**的地方有：
   - **允許 Claude 執行指令**：Claude 每次要執行指令都會先問你，看得懂就按允許。
   - **安裝 Python**：會跳出 Python 的安裝視窗，一直按「繼續」→「同意」→「安裝」，輸入你的 Mac 登入密碼。裝完會打開一個 Finder 視窗，關掉就好。
   - **允許存取「桌面」**：如果 Mac 問「Claude 想要取用『桌面』資料夾中的檔案」，按「好」。Claude 要在桌面放控制台的捷徑。
   - **素材庫金鑰（可略過）**：如果要用 Pexels／Unsplash 的免費實拍素材，Claude 會打開一個「終端機」視窗，你把金鑰貼進去按 Enter 就好（貼上時畫面不會顯示，這是正常的）。**不要把金鑰貼在對話裡。**
5. 裝好後，把 Claude 桌面 App **完全關掉**（選單列的 Claude → 結束 Claude，或按 ⌘Q），再重新打開。
6. 雙擊桌面上的 **`Reels Studio.command`** 就會打開控制台。會先跳出一個「終端機」黑色視窗，控制台用的時候不要把它關掉。

接下來的用法跟 Windows 一樣，看 `① 先看我.html` 從「建立頻道設定」開始做就好。

### Mac 上不能用的地方

| 功能 | Mac 上會怎樣 | 怎麼辦 |
|---|---|---|
| 控制台裡「打開資料夾」「在資料夾中顯示」「打開 BRAND.md」 | 按了沒反應或出現錯誤 | 請 Claude 幫你打開，或自己到 Finder 找 |
| 控制台裡「刪除頻道」 | 會失敗 | 到 Finder 自己把那個頻道資料夾丟到垃圾桶（位置請 Claude 告訴你） |
| 建立頻道時的字型樣本圖 | 每個字型上面的「字型名稱」標籤可能變成方框（□□□），因為標籤用的是 Windows 的微軟正黑體。字型本身的示範字是正常的 | 請 Claude 用文字告訴你每一列是哪個字型 |
| `① 先看我.html` 和控制台的說明 | 寫的是 Windows 的操作（例如「解壓縮全部」「C 槽」） | 照意思換成 Mac 的做法 |
| 更新版本 | 控制台的「下載新版」只給 Windows 用 | 下載新的 zip，再跟 Claude 說一次第 3 步那段話（頻道設定不會被蓋掉） |

### 遇到問題

- 先跟 Claude 說哪裡怪怪的，它通常能找出原因。
- 請 Claude **不要修改 Reels Studio 的程式檔**（`.py` 檔）。改了之後下次更新會被蓋掉，Saori 也很難幫你看問題。真的不能用時，請截圖回報給 Saori。

---

## 第二部分：給 Claude 的安裝步驟

你正在幫使用者把 Reels Studio（原本只支援 Windows）安裝到 macOS 上。Windows 版的安裝程式是 `程式檔（不用打開）/install.ps1`，下面每一步都對應到它的其中一段，有疑問時以它為準。

**規則**

- 使用者多半不懂程式。每一步執行前，用一兩句白話說明要做什麼、為什麼要做。
- **不要修改 `~/.claude/reels-studio/` 裡的 `.py` 程式檔**，也不要改安裝包裡的檔案。遇到 Windows 專用的程式碼出錯，告訴使用者是哪個功能不能用，不要自己改。
- 需要 `sudo` 或管理員密碼的步驟，交給使用者在圖形介面或終端機自己操作。你沒辦法替使用者輸入密碼。
- 不要讓使用者把 API 金鑰貼在對話裡。
- 每一步做完都要確認有成功，才繼續下一步。失敗就停下來告訴使用者，不要跳過。
- 下面的 `$SRC` 指的是安裝包裡的 `程式檔（不用打開）` 資料夾，請換成實際的絕對路徑，也就是這份檔案旁邊那個資料夾。因為路徑有中文和括號，一律加上引號。

### 0. 檢查環境

```bash
sw_vers; uname -m; df -h ~
cat "$SRC/VERSION"
```

- 系統是 macOS 11 以上才繼續。`uname -m` 是 `x86_64`（Intel）時，告訴使用者這種機型沒測試過，可能會失敗。
- 家目錄所在的磁碟可用空間少於 3 GB 時，提醒使用者先清出空間。

### 1. Python 3.13（對應 install.ps1 第 3 步）

先檢查：`command -v python3.13 && python3.13 --version`。

- **已經有 3.13**：確認是 python.org 版（路徑在 `/Library/Frameworks/Python.framework/` 或 `/usr/local/bin/`）就繼續。如果是 Homebrew 版，pip 會因為 PEP 668 拒絕安裝，tkinter 也要另外裝；這種情況還是改裝 python.org 版，比較單純。
- **沒有 3.13**：不要用 macOS 內建或 Xcode 附的 `python3`（通常是 3.9，太舊）。
  1. 到 <https://www.python.org/ftp/python/> 找最新的 `3.13.x`，下載 `python-3.13.x-macos11.pkg`（universal2，Intel 和 M 系列都能用），存到 `~/Downloads`。
  2. 確認簽章：`pkgutil --check-signature <pkg 檔>` 的結果要出現 `Python Software Foundation`，而且狀態是 `signed by a developer certificate issued by Apple`。不符合就刪掉檔案，停止安裝。
  3. 執行 `open <pkg 檔>`，請使用者在跳出的安裝視窗一路按下去，最後輸入登入密碼。等使用者說裝好了再繼續。
  4. 確認 `/usr/local/bin/python3.13 --version` 可以執行。
- **安裝 SSL 憑證（一定要做）**：python.org 版的 Python 預設沒有根憑證，不裝的話 Pexels、Unsplash 和版本檢查都會出現 SSL 錯誤。執行：

  ```bash
  "/Applications/Python 3.13/Install Certificates.command"
  ```

  如果這個檔案不存在，改成執行 `python3.13 -m pip install --upgrade certifi`。

### 2. 讓 `python` 指令指向 3.13

工具包的說明檔都寫 `python …`，但 Mac 上預設沒有 `python` 這個指令。在家目錄建一個捷徑，再加進 PATH：

```bash
mkdir -p ~/.local/bin
ln -sf "$(command -v python3.13)" ~/.local/bin/python
grep -q 'Reels Studio' ~/.zshenv 2>/dev/null || printf '\n# Reels Studio\nexport PATH="$HOME/.local/bin:$PATH"\n' >> ~/.zshenv
```

用 `~/.zshenv`，是因為不管是終端機、Claude Code 的指令，還是桌面捷徑啟動的 zsh 都會讀這個檔。

接著開一個新的 shell 確認：`zsh -c 'python --version'` 要印出 `Python 3.13.x`。如果使用者的預設 shell 不是 zsh（`echo $SHELL`），就把同一行 PATH 加到那個 shell 的設定檔。

### 3. Python 套件（對應第 4 步）

```bash
python3.13 -m pip install -r "$SRC/requirements.txt"
```

- 出現權限錯誤時，改用 `python3.13 -m pip install --user -r …`。
- `skia-python` 或 `ctranslate2`（faster-whisper 會用到）找不到這台機器能用的版本時，把錯誤訊息完整告訴使用者，請他回報給 Saori。不要自己改用其他套件取代。

### 4. 複製 agents、skill、工具包（對應第 1 步）

```bash
python3.13 "$SRC/mac_copy.py" "$SRC"
```

`mac_copy.py` 做的事情：

- 把 `$SRC/claude/` 裡的檔案複製到 `~/.claude/agents/`、`~/.claude/skills/reels-studio/`、`~/.claude/reels-studio/`。
- 把 `{{STUDIO}}`、`{{HOME}}` 換成這台 Mac 的路徑，路徑裡的 `\` 一起換成 `/`。
- 會被覆蓋的舊檔先備份；頻道設定 `my-brand*` 不會被動到。
- 複製使用說明頁，並在工具包資料夾放一份 `jf-openhuninn-1.1.ttf`。剪片引擎只會在 Windows 的字型資料夾和工具包資料夾找字型檔。

最後一行要印出「路徑沒換好的檔案：沒有」才算成功。

### 5. 字型 jf open 粉圓（對應第 2 步）

```bash
mkdir -p ~/Library/Fonts
cp -n "$SRC/font/jf-openhuninn-1.1.ttf" ~/Library/Fonts/
```

這是給其他 App 和 `fonts.py list` 用的。剪片引擎用的是第 4 步放在工具包資料夾的那一份。

### 6. 素材庫金鑰（選用，對應第 5 步）

先問使用者要不要用 Pexels（免費實拍照片和影片，<https://www.pexels.com/api/>）或 Unsplash（只有照片，發文時必須標註攝影師，<https://unsplash.com/developers>）。兩個都不用也可以，影片會全部改用插圖。

要用的話，讓使用者在終端機裡輸入金鑰。你沒辦法替他輸入，也不能讓金鑰經過對話；不要用「文字編輯」（`open -e`）開設定檔，它可能把引號自動換成彎引號，或存成 RTF，金鑰就會讀不到。

1. 執行下面的指令，建立金鑰輸入程式：

   ```bash
   cat > ~/.claude/reels-studio/mac_set_keys.command <<'EOF'
   #!/bin/zsh
   # Reels Studio：把 Pexels／Unsplash 金鑰存進 ~/.zshenv（輸入時不會顯示，也不會經過 Claude）
   f="$HOME/.zshenv"; touch "$f"; chmod 600 "$f"
   save() {   # $1 環境變數名稱  $2 給使用者看的名稱
     local k
     read -rs "k?請貼上 $2，再按 Enter（畫面不會顯示；不用的話直接按 Enter 跳過）：" ; echo
     k="${k//[[:space:]]/}"
     if [[ -z "$k" ]]; then echo "  跳過 $2"; return; fi
     grep -v "^export $1=" "$f" > "$f.tmp"; cat "$f.tmp" > "$f"; rm -f "$f.tmp"
     printf 'export %s=%q\n' "$1" "$k" >> "$f"
     echo "  OK  $2 已存好"
   }
   save PEXELS_API_KEY "Pexels API 金鑰"
   save UNSPLASH_ACCESS_KEY "Unsplash Access Key"
   echo; echo "完成！可以關掉這個視窗，回到 Claude 跟它說「好了」。"
   EOF
   chmod +x ~/.claude/reels-studio/mac_set_keys.command
   ```

2. 執行 `open ~/.claude/reels-studio/mac_set_keys.command`，會打開一個終端機視窗。請使用者在網站上複製金鑰，貼進那個視窗再按 Enter。不用的那一個直接按 Enter 跳過。等使用者說好了再繼續。
3. 用下面的指令確認有存好，只會印出「已設定／沒有設定」，**不會把金鑰印出來**：

   ```bash
   zsh -c 'for v in PEXELS_API_KEY UNSPLASH_ACCESS_KEY; do [ -n "${(P)v}" ] && echo "$v 已設定" || echo "$v 沒有設定"; done'
   ```

以後要新增或換金鑰，再執行一次 `open ~/.claude/reels-studio/mac_set_keys.command` 就好，舊的會被取代。工具包的說明檔寫的是「用 `setx` 設定金鑰」，那是 Windows 的做法。在 Mac 上一律改成執行這個程式。

### 7. 寫下 Mac 注意事項

Reels Studio 的 agents 和 skill 說明是照 Windows 寫的。在 `~/.claude/CLAUDE.md` 加上下面這段（檔案不存在就建立）。先告訴使用者你要在這個檔案加一段說明，讓以後的 Claude 知道這台是 Mac。如果檔案裡已經有 `<!-- Reels Studio Mac -->` 開頭的區塊，就整段換掉，不要重複加：

```markdown
<!-- Reels Studio Mac -->
## Reels Studio 在這台 Mac 上的注意事項
Reels Studio 的 agents、skill 和工具包說明是照 Windows 寫的，在這台 Mac 上要這樣換：
- 路徑一律用 `/`。說明裡的 `_reels_work\clipN\`、`assets\_previews\` 這類寫法，換成 `_reels_work/clipN/`、`assets/_previews/`。
- 說明寫 `$env:REELS_BRAND='<頻道資料夾>'; python clip.py …`（PowerShell）時，改成 `REELS_BRAND='<頻道資料夾>' python clip.py …`。
- 說明寫用 `setx` 設定金鑰時，改成執行 `open ~/.claude/reels-studio/mac_set_keys.command`，請使用者在跳出的終端機視窗貼上金鑰。金鑰存在 `~/.zshenv`，不要貼在對話裡，也不要用「文字編輯」開這個檔。
- `fonts.py list` 產生的字型樣本圖，每列上方的字型名稱標籤可能變成方框（標籤寫死用 Windows 的微軟正黑體）。字型名稱以 `fonts.py list` 印出的文字為準，用文字告訴使用者每一列是哪個字型。
- 要讓使用者看到資料夾或檔案時，用 `open <資料夾>` 或 `open -R <檔案>`，不要用 explorer、notepad。
- 控制台的「打開資料夾／在資料夾中顯示／打開 BRAND.md」和「刪除頻道」在 Mac 上不能用。使用者需要時改用 `open` 幫他打開；刪除頻道就告訴他資料夾位置，請他自己在 Finder 丟到垃圾桶。
- 不要修改 `~/.claude/reels-studio/` 裡的 `.py` 程式檔來配合 Mac。不能用的功能如實告訴使用者。
<!-- /Reels Studio Mac -->
```

### 8. 桌面捷徑（對應第 6 步）

建立 `~/Desktop/Reels Studio.command`：

```bash
cat > ~/Desktop/"Reels Studio.command" <<EOF
#!/bin/zsh
# Reels Studio 控制台：這個視窗開著時控制台才會運作，閒置 15 分鐘會自動結束
cd "\$HOME/.claude/reels-studio" && exec "$(command -v python3.13)" "\$HOME/.claude/reels-studio/studio_ui.py"
EOF
chmod +x ~/Desktop/"Reels Studio.command"
```

如果寫入失敗，原因通常是 macOS 還沒允許 Claude 存取桌面。請使用者在跳出的視窗按「好」，或到「系統設定 > 隱私權與安全性 > 檔案與資料夾」打開 Claude 的「桌面資料夾」權限，然後再試一次。

### 9. 檢查（對應 install.ps1 最後的檢查）

```bash
cd ~/.claude/reels-studio && python3.13 - <<'EOF'
import sys, os
sys.path.insert(0, os.getcwd())
import faster_whisper, opencc, av, skia, numpy, soundfile, PIL, tkinter
for c in ('libx264', 'aac'): av.codec.Codec(c, 'w')
import reels_lib, props, fonts
print('OK', reels_lib.FONT_PATH)
EOF
```

要印出 `OK` 和 `jf-openhuninn-1.1.ttf` 的路徑才算成功。如果 `import tkinter` 失敗，控制台的「選擇資料夾」就不能用。這通常表示用到的不是 python.org 版的 Python，回到第 1 步檢查。

接著執行 `python3.13 ~/.claude/reels-studio/studio_ui.py`，確認瀏覽器會打開控制台頁面，再請使用者看一眼頁面有沒有正常顯示。確認完把它停掉（`kill` 那個程序就好，不要用 `pkill python`）。

### 10. 完成

用條列告訴使用者：

1. 把 Claude 桌面 App 完全結束（⌘Q）再打開，它才會認得剛裝好的小幫手。
2. 之後雙擊桌面上的 `Reels Studio.command` 打開控制台，跳出的終端機視窗不要關。
3. 接著照 `① 先看我.html` 從「建立頻道設定」開始。第一次聽打會下載約 1.6 GB 的語音辨識模型，需要等一下。
4. 第一部分「Mac 上不能用的地方」那張表的內容。
5. 這次安裝哪幾步沒成功（如果有的話）。
