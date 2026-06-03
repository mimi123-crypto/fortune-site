<#
  publish.ps1  —  占いサイトを毎日更新してGitHubへ反映するローカル用スクリプト
  =================================================================
  1. build_site.py で docs/index.html を生成
  2. 変更があれば git add / commit / push
  3. すべて logs/update.log に記録（成功も失敗も）

  Windowsタスクスケジューラからは publish.bat 経由で呼ぶのが簡単です。
  GitHub Actions を使う場合はこのスクリプトは不要（クラウドで同じことをやる）。

  使い方:
    powershell -ExecutionPolicy Bypass -File publish.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# ログ準備
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir "update.log"

function Write-Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Host $line
}

Write-Log "=== publish 開始 ==="

try {
    # 1) サイト生成（公開フォルダ docs/ に出力）
    $py = python build_site.py --out docs 2>&1 | Out-String
    Write-Log "build_site.py 実行完了"
    foreach ($l in ($py -split "`n")) {
        $t = $l.Trim()
        if ($t) { Add-Content -Path $log -Value ("    " + $t) -Encoding UTF8 }
    }

    # 2) 変更があるか確認（docs/ 配下のみ）
    $changes = git status --porcelain -- docs
    if (-not $changes) {
        Write-Log "docs/ に変更なし。コミットをスキップしました。"
        Write-Log "=== publish 正常終了（更新なし） ==="
        exit 0
    }

    # 3) コミット & プッシュ
    git add docs
    if ($LASTEXITCODE -ne 0) { throw "git add 失敗" }

    $today = Get-Date -Format "yyyy-MM-dd"
    git commit -m ("daily fortune update {0}" -f $today)
    if ($LASTEXITCODE -ne 0) { throw "git commit 失敗" }

    git push
    if ($LASTEXITCODE -ne 0) { throw "git push 失敗（認証/リモート設定を確認）" }

    Write-Log ("GitHubへ反映しました（{0}）" -f $today)
    Write-Log "=== publish 正常終了 ==="
    exit 0
}
catch {
    Write-Log ("!! エラー: " + $_.Exception.Message)
    Write-Log "=== publish 異常終了 ==="
    exit 1
}
