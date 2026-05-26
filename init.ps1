# init.ps1 - Sapir Tools

$ScriptDir = $PSScriptRoot

function run {
    if ($args.Count -eq 0) {
        Write-Host ""
        Write-Host " Sapir Tools - available commands:" -ForegroundColor Cyan
        Write-Host "   run help                 - show this list" -ForegroundColor Gray
        Write-Host "   cleanup [days] [--opts]  - clean old files from Downloads" -ForegroundColor Gray
        Write-Host "   backup  [--opts]         - backup important files" -ForegroundColor Gray
        Write-Host "   anagram [word]           - find all words from letters" -ForegroundColor Gray
        Write-Host "   install_deps             - install missing dependencies" -ForegroundColor Gray
        Write-Host ""
        Write-Host " Examples:" -ForegroundColor Yellow
        Write-Host "   run cleanup --dry       - preview what will be deleted" -ForegroundColor Gray
        Write-Host "   run cleanup 7           - delete files older than 7 days" -ForegroundColor Gray
        Write-Host "   run cleanup 30 --trash  - move to recycle bin" -ForegroundColor Gray
        Write-Host "   run backup --list       - show what will be backed up" -ForegroundColor Gray
        Write-Host "   run backup --dest D:\   - backup to drive D:" -ForegroundColor Gray
        Write-Host "   run anagram guitar      - words from letters of 'guitar'" -ForegroundColor Gray
        Write-Host ""
        return
    }

    $cmd = $args[0]
    $rest = $args[1..$args.Length]

    switch ($cmd) {
        'help' { run }
        'cleanup' { & python "$ScriptDir\cleanup\cleanup.py" $rest }
        'backup' { & python "$ScriptDir\backup\backup.py" $rest }
        'anagram' { & python "$ScriptDir\anagram\anagram.py" $rest }
        'install_deps' { & python "$ScriptDir\install_deps.py" $rest }
        default {
            Write-Host "Unknown command: $cmd" -ForegroundColor Red
            run
        }
    }
}

# ----- Health check -----------------------------------------------------------------
$py = Get-Command python -ErrorAction SilentlyContinue
Write-Host ""
Write-Host " Sapir Tools" -ForegroundColor Cyan

if (-not $py) {
    Write-Host "   Python not found! Install Python and try again." -ForegroundColor Red
} else {
    $check = & python -c @"
import json, sys, importlib, py_compile, os
from pathlib import Path

base = Path(r'$ScriptDir')
results = []

def check(name, script, *imports):
    entry = {'name': name, 'status': 'ok', 'detail': ''}
    path = base / script
    if not path.exists():
        entry['status'] = 'error'
        entry['detail'] = 'file not found'
        results.append(entry)
        return
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        entry['status'] = 'error'
        entry['detail'] = str(e)
        results.append(entry)
        return
    for mod in imports:
        try:
            importlib.import_module(mod)
        except ImportError:
            entry['status'] = 'warn'
            detail = f'missing: {mod}'
            if entry['detail']:
                detail = entry['detail'] + ', ' + detail
            entry['detail'] = detail
    results.append(entry)

check('cleanup', 'cleanup\\cleanup.py', 'send2trash')
check('backup', 'backup\\backup.py')
check('anagram', 'anagram\\anagram.py')
check('install_deps', 'install_deps.py')

print(json.dumps(results))
"@ 2>$null

    if ($check) {
        $items = $check | ConvertFrom-Json
        foreach ($item in $items) {
            $icon = '?'
            $color = 'Gray'
            $note = ''
            if ($item.status -eq 'ok')    { $icon = 'ok';    $color = 'Green' }
            if ($item.status -eq 'warn')  { $icon = 'warn';  $color = 'Yellow'; $note = " ($($item.detail))" }
            if ($item.status -eq 'error') { $icon = 'FAIL';  $color = 'Red';    $note = " ($($item.detail))" }
            Write-Host "   [$icon] $($item.name)$note" -ForegroundColor $color
        }
    } else {
        Write-Host "   Health check failed" -ForegroundColor Red
    }
}

Write-Host "   run - show available commands" -ForegroundColor Gray