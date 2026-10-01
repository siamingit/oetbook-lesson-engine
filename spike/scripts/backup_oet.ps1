# Back up C:\OET (lesson content, not in git) and the repo's evidence folders
# to the external drive labelled OETBACKUP. Approved by the maintainer in chat,
# 2026-10-01.
#
#   powershell -File spike\scripts\backup_oet.ps1                 # dry run (robocopy /L): nothing written
#   powershell -File spike\scripts\backup_oet.ps1 -Copy           # the real copy
#   powershell -File spike\scripts\backup_oet.ps1 -Verify         # after a copy: 0 differences, SHA-256 match
#   ... -Drive E:                                                 # if the drive gets another letter
#
# Scope:
#   C:\OET -> <drive>:\Backups\OET\OET, a mirror (/MIR), except
#     the credential paths listed in spike\out\backup-exclude.txt (local and
#       gitignored, so this public script names none; one absolute path a line,
#       folder or file). Without that file the script refuses to run, so
#       credentials are never copied by accident,
#     every folder named term_probes (terms-check test clips, regenerable),
#     Grammar 1's legacy generated\<section>\audio folders (600 WAVs no player
#       references; excluded, not deleted).
#   spike\out\voice_samples, initialism-probe, lexicon-review ->
#     <drive>:\Backups\OET\repo-evidence\<name>, mirrors.
# Nothing is written outside <drive>:\Backups\OET: every destination is checked
# against it before robocopy runs, and the drive must carry the label OETBACKUP.
# A mirror deletes from its own destination what is gone from its source; the
# two parts have separate destinations, so neither can delete the other.

param(
    [string]$Drive = "D:",
    [switch]$Copy,
    [switch]$Verify
)
$ErrorActionPreference = "Stop"

$Label  = "OETBACKUP"
$Source = "C:\OET"
$Repo   = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Drive  = $Drive.TrimEnd("\").TrimEnd(":") + ":"
$Root   = "$Drive\Backups\OET"
$Mode   = if ($Copy) { "COPY" } elseif ($Verify) { "VERIFY" } else { "DRY RUN" }

$vol = Get-Volume -DriveLetter $Drive.TrimEnd(":") -ErrorAction SilentlyContinue
if (-not $vol) { throw "No drive $Drive. Connect the backup drive, or pass -Drive X:." }
if ($vol.FileSystemLabel -ne $Label) {
    throw "Drive $Drive is labelled '$($vol.FileSystemLabel)', not '$Label'. Refusing: wrong drive?"
}

# Grammar 1's legacy audio: generated\<section>\audio, never generated\<section>\boards\audio
$legacy = @(Get-ChildItem "$Source\lessons\grammar-01-verb-tenses\generated" -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName "audio" } | Where-Object { Test-Path $_ })

# Credentials: their paths come from a local, gitignored file, never from this script
$ExcludeFile = "$Repo\spike\out\backup-exclude.txt"
if (-not (Test-Path $ExcludeFile)) {
    throw "No $ExcludeFile. List the credential paths never to copy (one absolute path a line) first."
}
$private = @(Get-Content $ExcludeFile | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith("#") })
if (-not $private.Count) { throw "$ExcludeFile lists no path. Refusing." }
$privDirs  = @($private | Where-Object { Test-Path -LiteralPath $_ -PathType Container })
$privFiles = @($private | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Container) })

$jobs = @(
    @{ Name = "OET"; Src = $Source; Dst = "$Root\OET";
       XD = @("term_probes") + $privDirs + $legacy;
       XF = $privFiles }
)
foreach ($n in "voice_samples", "initialism-probe", "lexicon-review") {
    $jobs += @{ Name = "repo-evidence\$n"; Src = "$Repo\spike\out\$n"; Dst = "$Root\repo-evidence\$n"; XD = @(); XF = @() }
}

foreach ($j in $jobs) {
    if (-not $j.Dst.StartsWith("$Root\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "Destination $($j.Dst) is outside $Root. Refusing."
    }
    if (-not (Test-Path $j.Src)) { throw "Source $($j.Src) is missing." }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = if ($Copy) { "$Root\logs" } else { "$Repo\spike\out\backup-logs" }
New-Item -ItemType Directory -Force $logDir | Out-Null

function Summary([string]$log) {
    # robocopy's closing table: Dirs / Files / Bytes, columns total copied skipped mismatch failed extras
    $s = @{}
    foreach ($line in Get-Content $log) {
        if ($line -match '^\s*(Dirs|Files|Bytes)\s*:\s*(\d[\d\s]*)$') {     # not the header's "Files : *.*"
            $s[$Matches[1]] = @(($Matches[2].Trim() -split '\s+') | ForEach-Object { [double]$_ })
        }
    }
    return $s
}

function Run-Robocopy($j, [bool]$listOnly) {
    $log = Join-Path $logDir ("$stamp-" + ($j.Name -replace '[\\/]', '_') + ".log")
    $rcArgs = @($j.Src, $j.Dst, "/MIR", "/R:2", "/W:5", "/FFT", "/NP", "/BYTES", "/NFL", "/NDL", "/LOG:$log")
    if ($listOnly) { $rcArgs += "/L" }
    if ($j.XD.Count) { $rcArgs += "/XD"; $rcArgs += $j.XD }
    if ($j.XF.Count) { $rcArgs += "/XF"; $rcArgs += $j.XF }
    & robocopy @rcArgs | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) { throw "robocopy failed for $($j.Name) (exit $code); see $log" }
    return @{ Code = $code; Log = $log; S = (Summary $log) }
}

Write-Host "backup_oet: $Mode  ($Source and repo evidence -> $Root, drive $Drive '$Label', $($vol.FileSystem))"
Write-Host ("excluded: {0} credential path(s) from spike\out\backup-exclude.txt, every term_probes folder, {1} Grammar 1 legacy audio folders" -f $private.Count, $legacy.Count)
$bad = 0
foreach ($j in $jobs) {
    $r = Run-Robocopy $j (-not $Copy)
    $f = $r.S["Files"]; $b = $r.S["Bytes"]; $d = $r.S["Dirs"]
    Write-Host ("  {0,-30} files {1,6} total, {2,6} {3}, {4,4} extra (deleted from the copy)  |  {5,8:N1} MB {3}" -f `
        $j.Name, $f[0], $f[1], $(if ($Copy) { "copied" } else { "to copy" }), $f[5], ($b[1] / 1MB))
    if ($Verify -and ($f[1] -ne 0 -or $f[5] -ne 0 -or $d[5] -ne 0)) {
        Write-Host "    DIFFERENT: the copy does not match its source"; $bad++
    }
    Write-Host "    log: $($r.Log)"
}

if ($Verify) {
    Write-Host "SHA-256: every file in the copy against its source..."
    foreach ($j in $jobs) {
        $n = 0
        foreach ($file in Get-ChildItem $j.Dst -Recurse -File) {
            $rel = $file.FullName.Substring($j.Dst.Length)
            $src = $j.Src + $rel
            if (-not (Test-Path -LiteralPath $src) -or
                (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash) {
                Write-Host "    MISMATCH $rel"; $bad++
            }
            $n++
        }
        Write-Host ("  {0,-30} {1} files hashed" -f $j.Name, $n)
    }
    if ($bad) { Write-Host "VERIFY FAILED: $bad difference(s)" } else {
        Write-Host "VERIFY OK: the copy matches its source"
        # the runner reminds when this is more than 14 days old (docs/03-RUNBOOK.md step 19)
        Set-Content -Path "$Repo\spike\out\backup-logs\last-verified.txt" -Value (Get-Date -Format "yyyy-MM-ddTHH:mm:ss") -Encoding ASCII
    }
}

Write-Host ""
Write-Host "REMINDER: before unplugging $Drive, use 'Safely Remove Hardware and Eject Media' (or Eject in File Explorer)."
Write-Host "The drive is exFAT, which has no journal: unplugging it during or right after a copy can corrupt it."
if ($bad) { exit 1 }
