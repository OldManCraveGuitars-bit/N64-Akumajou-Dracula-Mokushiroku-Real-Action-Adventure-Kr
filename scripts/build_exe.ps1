$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $bundleDir = Join-Path (Get-Location).Path 'data'
    $versionFile = Join-Path (Get-Location).Path 'version_info.txt'
    $patchVersion = python -c "from patcher_core import VERSION; print(VERSION)"
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name "N64-Akumajou-Dracula-Mokushiroku-Kr-v$patchVersion-Patcher" --add-data "$bundleDir;data" --version-file $versionFile --distpath dist --workpath build/pyinstaller --specpath build patcher_app.py
    if ($LASTEXITCODE -ne 0) { throw 'EXE build failed.' }
} finally {
    Pop-Location
}
