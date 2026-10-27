# Reels Studio 短影音製作流程安裝程式
# 用法：雙擊安裝包最外層的「② 雙擊安裝.bat」。可重複執行；已存在的舊檔會先備份，頻道設定（reels-studio\my-brand\）不會被動到。
# 測試用參數：-TargetHome <資料夾>（預設 %USERPROFILE%）、-SkipPip、-SkipFont、-SkipKey、-SkipShortcut（不建桌面捷徑、不自動打開說明頁）
param(
    [string]$TargetHome = $env:USERPROFILE,
    [switch]$SkipPip,
    [switch]$SkipFont,
    [switch]$SkipKey,
    [switch]$SkipShortcut
)
$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot
$Guide = Join-Path (Split-Path $Src) '① 先看我.html'   # 說明頁在安裝包最外層
$Rerun = '再雙擊一次「② 雙擊安裝」'
$Claude = Join-Path $TargetHome '.claude'
$Studio = Join-Path $Claude 'reels-studio'
$Utf8 = New-Object System.Text.UTF8Encoding($false)   # 不加 BOM，agent 檔開頭的 --- 才讀得到
$Problems = @()

function Say($msg, $color = 'White') { Write-Host $msg -ForegroundColor $color }

$Version = if (Test-Path (Join-Path $Src 'VERSION')) { (Get-Content (Join-Path $Src 'VERSION') -TotalCount 1).Trim() } else { '' }
Say "`n=== Reels Studio 安裝程式 $(if ($Version) { "v$Version" }) ===" Cyan
Say "安裝到：$Claude"
try {                                                 # Python, packages and the speech model need about 3 GB on this drive
    $drive = Get-PSDrive -Name ($TargetHome.Substring(0, 1)) -ErrorAction Stop
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    if ($freeGB -lt 3) {
        Say "  ⚠ $($drive.Name): 槽只剩 $freeGB GB。安裝和第一次聽打總共需要約 3 GB，空間不夠可能會失敗。" Yellow
        Say "    建議先清出空間（例如清空資源回收筒、刪掉不用的大檔案）再安裝。" Yellow
    } else { Say "  $($drive.Name): 槽可用空間 $freeGB GB（需要約 3 GB）" }
} catch {}

# ---------- 1. 複製 agents / skill / 工具包 ----------
Say "`n[1/6] 複製 agents、skill、工具包" Cyan
$Parts = @(
    @{ From = 'claude\agents';                To = 'agents' },
    @{ From = 'claude\skills\reels-studio';   To = 'skills\reels-studio' },
    @{ From = 'claude\reels-studio';          To = 'reels-studio' }
)
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $Claude "backup-reels-studio-$Stamp"
foreach ($p in $Parts) {
    $srcDir = Join-Path $Src $p.From
    Get-ChildItem $srcDir -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($srcDir.Length).TrimStart('\')
        $dst = Join-Path (Join-Path $Claude $p.To) $rel
        if (Test-Path $dst) {                       # 備份會被覆蓋的舊檔
            $bk = Join-Path (Join-Path $Backup $p.To) $rel
            New-Item -ItemType Directory -Force (Split-Path $bk) | Out-Null
            Copy-Item $dst $bk -Force
        }
        New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
        if ($_.Extension -in '.md', '.py', '.txt') {
            $text = [System.IO.File]::ReadAllText($_.FullName, $Utf8)
            $text = $text.Replace('{{STUDIO}}', $Studio).Replace('{{HOME}}', $TargetHome)   # 換成這台電腦的路徑
            [System.IO.File]::WriteAllText($dst, $text, $Utf8)
        } else {
            Copy-Item $_.FullName $dst -Force
        }
    }
    Say "  OK  $($p.To)" Green
}
if (Test-Path $Backup) { Say "  舊檔已備份到 $Backup" Yellow }
# the release number goes in with the program files, so a panel started mid-install already sees the new one
if ($Version) { [System.IO.File]::WriteAllText((Join-Path $Studio 'VERSION'), "$Version`n", $Utf8) }

# ---------- 2. 字型 jf open 粉圓 ----------
Say "`n[2/6] 字型 jf open 粉圓" Cyan
$FontFile = 'jf-openhuninn-1.1.ttf'
$UserFonts = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$Installed = (Test-Path (Join-Path $UserFonts $FontFile)) -or (Test-Path (Join-Path "$env:WINDIR\Fonts" $FontFile))
if ($Installed) { Say "  已安裝，略過" Green }
elseif ($SkipFont) { Say "  略過（-SkipFont）" Yellow }
else {
    New-Item -ItemType Directory -Force $UserFonts | Out-Null
    $dst = Join-Path $UserFonts $FontFile
    Copy-Item (Join-Path $Src "font\$FontFile") $dst -Force
    New-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts' `
        -Name 'jf open 粉圓 1.1 (TrueType)' -Value $dst -PropertyType String -Force | Out-Null
    Say "  OK  已安裝到 $UserFonts（只裝給目前使用者）" Green
}

# ---------- 3. Python ----------
Say "`n[3/6] Python" Cyan
$Py313 = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'   # python.org 個人安裝的位置

function PyVersion($exe) {           # 回傳 [int] 次版本號（3.13 → 13），不能執行就回傳 0
    try { $o = (& $exe -c "import sys; print(sys.version_info[1])" 2>$null); if ($LASTEXITCODE -eq 0) { return [int]"$o".Trim() } } catch {}
    return 0
}

function Get-Python313Url {          # python.org 上最新、且有 Windows 安裝檔的 3.13.x
    try {
        $html = (Invoke-WebRequest 'https://www.python.org/ftp/python/' -UseBasicParsing).Content
        $ns = [regex]::Matches($html, 'href="3\.13\.(\d+)/"') | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Descending
        foreach ($n in ($ns | Select-Object -First 8)) {
            $url = "https://www.python.org/ftp/python/3.13.$n/python-3.13.$n-amd64.exe"
            try { Invoke-WebRequest $url -Method Head -UseBasicParsing | Out-Null; return $url } catch {}
        }
    } catch {}
    return 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe'
}

function Install-Python313 {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = 'SilentlyContinue'      # 不關掉的話 PowerShell 5.1 下載會非常慢
    Say "  查詢 python.org 上最新的 Python 3.13 ..."
    $url = Get-Python313Url
    $file = Join-Path $env:TEMP (Split-Path $url -Leaf)
    Say "  下載 $url"
    Invoke-WebRequest $url -OutFile $file -UseBasicParsing
    $sig = Get-AuthenticodeSignature $file          # 確認是 Python 官方簽章的安裝檔
    if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        Remove-Item $file -ErrorAction SilentlyContinue
        throw "下載的檔案沒有 Python 官方的有效簽章，已刪除，沒有安裝。"
    }
    Say "  安裝中（只裝給目前使用者，不需要系統管理員權限，約 1–3 分鐘）..."
    $p = Start-Process $file -Wait -PassThru -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
        'Include_launcher=1', 'InstallLauncherAllUsers=0', 'Include_test=0'
    Remove-Item $file -ErrorAction SilentlyContinue
    if ($p.ExitCode -ne 0) { throw "Python 安裝程式結束代碼 $($p.ExitCode)" }
    # 讓這個視窗馬上看得到新的 PATH
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

$Py = $null
$minor = PyVersion 'python'
if ($minor -ge 10) {
    $Py = 'python'
    Say "  OK  $(& python --version 2>$null)" Green
} else {
    if ($minor -gt 0) { Say "  目前的 Python 是 3.$minor，版本太舊（需要 3.10 以上）" Yellow }
    else { Say "  這台電腦還沒有 Python" Yellow }
    $ans = Read-Host "  要自動從 python.org 下載並安裝 Python 3.13 嗎？(Y/n)"
    if ($ans -match '^\s*(n|no)\s*$') {
        Say "  沒有安裝。請到 https://www.python.org/downloads/ 自行安裝 Python 3.13，" Red
        Say "  安裝畫面第一頁要勾選「Add python.exe to PATH」，裝好後$Rerun。" Red
        $Problems += 'Python 未安裝'
    } else {
        try {
            Install-Python313
            if ((PyVersion 'python') -ge 10) { $Py = 'python'; Say "  OK  已安裝 $(& python --version 2>$null)" Green }
            elseif ((PyVersion $Py313) -ge 10) {
                $Py = $Py313
                Say "  已安裝，但命令列輸入 python 仍會叫到舊版。" Yellow
                $Problems += "命令列的 python 不是 3.13：請在「設定 > 應用程式 > 進階應用程式設定 > 應用程式執行別名」關掉 python.exe，或移除舊版 Python"
            } else { throw "安裝完成後仍找不到 python.exe" }
        } catch {
            Say "  自動安裝失敗：$($_.Exception.Message)" Red
            Say "  請到 https://www.python.org/downloads/ 自行安裝（勾選「Add python.exe to PATH」），裝好後$Rerun。" Red
            $Problems += 'Python 自動安裝失敗'
        }
    }
}

# ---------- 4. Python 套件 ----------
Say "`n[4/6] Python 套件" Cyan
if (-not $Py) { Say "  略過（沒有 Python）" Yellow }
elseif ($SkipPip) { Say "  略過（-SkipPip）" Yellow }
else {
    & $Py -m pip install -r (Join-Path $Src 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { Say "  pip 安裝失敗，請看上面的錯誤訊息" Red; $Problems += 'Python 套件安裝失敗' }
}

# ---------- 5. 素材庫金鑰（Pexels、Unsplash，都可略過） ----------
Say "`n[5/6] 素材庫金鑰（選用：剪片時找免費實拍素材，兩個都沒有也可以用，影片會全部用插圖）" Cyan
function Ask-Key($label, $var, $note) {
    $HasKey = [Environment]::GetEnvironmentVariable($var, 'User')
    if ($HasKey) { Say "  $label：已設定，略過" Green; return }
    if ($SkipKey) { Say "  $label：略過（-SkipKey）" Yellow; return }
    Say "  $note"
    Say "  請貼上 $label 金鑰（輸入時不會顯示；直接按 Enter 跳過）："
    $sec = Read-Host -AsSecureString
    $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
    if ($key.Trim()) {
        [Environment]::SetEnvironmentVariable($var, $key.Trim(), 'User')
        Say "  OK  已存成使用者環境變數 $var" Green
    } else {
        Say "  跳過。之後想用時在 PowerShell 執行：setx $var ""你的金鑰""" Yellow
    }
}
Ask-Key 'Pexels API' 'PEXELS_API_KEY' 'Pexels：免費實拍照片和影片，不強制標註。到 https://www.pexels.com/api/ 免費申請。'
Ask-Key 'Unsplash Access Key' 'UNSPLASH_ACCESS_KEY' 'Unsplash：只有照片，發文時必須標註攝影師。到 https://unsplash.com/developers 建立 App 後複製「Access Key」。'

# ---------- 6. 使用說明＋控制台捷徑 ----------
Say "`n[6/6] 控制台與桌面捷徑" Cyan
$GuideCopy = Join-Path $Studio '使用說明.html'      # 複製一份，安裝包刪掉後捷徑也還能用
if (Test-Path $Guide) {
    Copy-Item $Guide $GuideCopy -Force
    $html = [System.IO.File]::ReadAllText($GuideCopy, $Utf8).Replace('程式檔（不用打開）\font\OFL.txt', 'font\OFL.txt').Replace('程式檔（不用打開）/說明圖片/', '說明圖片/')
    [System.IO.File]::WriteAllText($GuideCopy, $html, $Utf8)
    $Shots = Join-Path $Src '說明圖片'                 # screenshots the guide shows next to each step
    if (Test-Path $Shots) {
        New-Item -ItemType Directory -Force (Join-Path $Studio '說明圖片') | Out-Null
        Copy-Item (Join-Path $Shots '*') (Join-Path $Studio '說明圖片') -Force
    }
    New-Item -ItemType Directory -Force (Join-Path $Studio 'font') | Out-Null
    Copy-Item (Join-Path $Src 'font\OFL.txt') (Join-Path $Studio 'font\OFL.txt') -Force
}
$Pyw = $null                                       # 控制台用 pythonw 跑，不會跳出黑色視窗
if ($Py) {
    $Pyw = (& $Py -c "import os, sys; d = os.path.dirname(sys.executable); w = os.path.join(d, 'pythonw.exe'); print(w if os.path.exists(w) else sys.executable)" 2>$null)
    if ($Pyw) { $Pyw = "$Pyw".Trim() }
}
$Panel = Join-Path $Studio 'studio_ui.py'
if ($SkipShortcut) { Say "  略過（-SkipShortcut）" Yellow }
elseif (-not $Pyw) { Say "  沒有 Python，略過控制台捷徑" Yellow }
else {
    try {
        $Desktop = [Environment]::GetFolderPath('Desktop')
        $old = Join-Path $Desktop 'Reels Studio 使用說明.lnk'      # 舊版安裝程式建的，改成控制台捷徑
        if (Test-Path $old) { Remove-Item $old -Force }
        $sc = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $Desktop 'Reels Studio.lnk'))
        $sc.TargetPath = $Pyw
        $sc.Arguments = """$Panel"""
        $sc.WorkingDirectory = $Studio
        $sc.IconLocation = (Join-Path $Studio 'ui\icon.ico')
        $sc.Description = 'Reels Studio 控制台：頻道設定、看做好的影片和文案'
        $sc.Save()
        Say "  OK  桌面多了「Reels Studio」，點它就會打開控制台（頻道設定、我的作品、使用說明）" Green
    } catch { Say "  桌面捷徑建立失敗（不影響使用）：$($_.Exception.Message)" Yellow }
}

# ---------- 檢查 ----------
Say "`n=== 檢查 ===" Cyan
if ($Py) {
    $check = @"
import sys
sys.path.insert(0, r'$Studio')
import faster_whisper, opencc, av, skia, numpy, soundfile, PIL
for c in ('libx264', 'aac'): av.codec.Codec(c, 'w')
import reels_lib, props, fonts
print('OK', reels_lib.FONT_PATH)
"@
    $tmp = Join-Path $env:TEMP 'reels_studio_check.py'
    [System.IO.File]::WriteAllText($tmp, $check, $Utf8)
    $ErrorActionPreference = 'Continue'          # python 的 stderr 不要被當成 PowerShell 錯誤而中斷
    $out = (& $Py $tmp 2>&1 | ForEach-Object { "$_" }) -join "`n"
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Remove-Item $tmp -ErrorAction SilentlyContinue
    if ($code -eq 0) { Say "  工具包可以正常載入：$out" Green }
    else { Say "  工具包載入失敗：`n$out" Red; $Problems += '工具包載入失敗（見上方訊息）' }
}
$left = Get-ChildItem "$Claude\agents\studio-*.md", "$Claude\skills\reels-studio", $Studio -Recurse -File -Include *.md, *.py |
    Where-Object { [System.IO.File]::ReadAllText($_.FullName, $Utf8) -match '\{\{(STUDIO|HOME)\}\}' }
if ($left) { Say "  還有檔案沒換到路徑：$($left.FullName -join ', ')" Red; $Problems += '路徑替換不完整' }
else { Say "  路徑都已換成 $Studio" Green }
if (Test-Path (Join-Path $Studio 'my-brand\brand.json')) { Say "  找到既有的頻道設定（my-brand），保留不動" Green }

if ($Problems.Count -eq 0) {
    Say "`n全部完成！" Green
    Say "1. 把 Claude 桌面 App 完全關掉再打開，它才會認得剛裝好的小幫手。"
    Say "2. 在控制台的「頻道設定」選配色、字型和結尾卡（也可以之後直接跟 Claude 說「幫我做 reels」，它會一題一題問你）。"
    Say "3. 在控制台的「我的作品」選素材所在的資料夾，照「下一步」把句子複製貼給 Claude。"
    Say "第一次聽打時會自動下載約 1.6 GB 的語音辨識模型，需要一點時間。"
    if (-not $SkipShortcut -and $Pyw) {
        Say "`n正在打開 Reels Studio 控制台⋯⋯之後點桌面上的「Reels Studio」就能再打開。" Cyan
        Start-Process $Pyw -ArgumentList """$Panel""" -WorkingDirectory $Studio
    }
} else {
    Say "`n完成，但有以下問題要處理：" Yellow
    $Problems | ForEach-Object { Say "  - $_" Yellow }
    Say "處理好之後，$Rerun 就可以。重複執行不會弄壞東西。" Yellow
}
