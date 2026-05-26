# completion.ps1 - tab completion

Add-Type -AssemblyName System.Management.Automation

function item($text, $tip) {
    [System.Management.Automation.CompletionResult]::new($text, $text, 'ParameterValue', $tip)
}

function items($list, $word) {
    $list | Where-Object { $_ -like "$word*" }
}

function numitems($from, $to, $word) {
    $from..$to | Where-Object { "$_" -like "$word*" }
}

$cmds = @(
    (item 'help' 'Show this help')
    (item 'cleanup' 'Clean old files from Downloads folder')
    (item 'backup' 'Backup important files (Documents, Desktop, Downloads)')
    (item 'anagram' 'Find all valid words from letters of a given word')
    (item 'install_deps' 'Install missing Python dependencies')
)

$cleanup_flags = @(
    (item '--dry' '-d     Dry run: only show what would be deleted')
    (item '-d'    '--dry  Dry run: only show what would be deleted')
    (item '--trash' '-t     Move to recycle bin (requires send2trash)')
    (item '-t'    '--trash Move to recycle bin (requires send2trash)')
    (item '--verbose' '-v     Verbose output: show all files being processed')
    (item '-v'    '--verbose Verbose output')
    (item '--yes' '-y     Skip confirmation prompt')
    (item '-y'    '--yes  Skip confirmation prompt')
    (item '--help' '-h     Show help and exit')
    (item '-h'    '--help  Show help and exit')
)

$backup_flags = @(
    (item '--dest' '-d DEST  Backup destination folder')
    (item '-d'    '--dest DEST Backup destination folder')
    (item '--list' '-l     List files that would be backed up')
    (item '-l'    '--list  List files that would be backed up')
    (item '--dry' 'Dry run: show what would be copied')
    (item '--help' '-h     Show help and exit')
    (item '-h'    '--help  Show help and exit')
)

$anagram_flags = @(
    (item '--min' '-m N    Minimum word length (default: 3)')
    (item '-m'   '--min N Minimum word length (default: 3)')
    (item '--max' '-M N    Maximum word length (default: same as input)')
    (item '-M'   '--max N Maximum word length (default: same as input)')
    (item '--lang' '-l LANG  Language: en or ru (auto-detected by default)')
    (item '-l'   '--lang LANG Language: en or ru')
    (item '--all' '-a     Show input word in results')
    (item '-a'   '--all  Show input word in results')
    (item '--sub' '-s     Words that CONTAIN all input letters (superset)')
    (item '-s'   '--sub  Words that CONTAIN all input letters (superset)')
    (item '--exact' '-e     Exact anagrams only (no repetitions)')
    (item '-e'   '--exact  Exact anagrams only (no repetitions)')
    (item '--help' '-h     Show help and exit')
    (item '-h'   '--help  Show help and exit')
)

$completer = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $name = $commandAst.CommandElements[0].Value
    $elements = $commandAst.CommandElements | Select-Object -Skip 1

    switch ($name) {
        'run' {
            if ($elements.Count -eq 0) {
                return items $cmds $wordToComplete
            }
            $sub = $elements[0].Extent.Text.Trim("'", '"')
            if (@('help','cleanup','backup','anagram','install_deps') -notcontains $sub) {
                return items $cmds $wordToComplete
            }
            switch ($sub) {
                'help'    { @() }
                'cleanup' { items $cleanup_flags $wordToComplete; numitems 1 90 $wordToComplete }
                'backup'  { items $backup_flags $wordToComplete }
                'anagram' { items $anagram_flags $wordToComplete }
            }
        }
        'cleanup' {
            items $cleanup_flags $wordToComplete; numitems 1 90 $wordToComplete
        }
        'backup' {
            items $backup_flags $wordToComplete
        }
        'anagram' {
            items $anagram_flags $wordToComplete
        }
    }
}

Register-ArgumentCompleter -CommandName 'run' -ScriptBlock $completer
Register-ArgumentCompleter -CommandName 'cleanup' -ScriptBlock $completer
Register-ArgumentCompleter -CommandName 'backup' -ScriptBlock $completer
Register-ArgumentCompleter -CommandName 'anagram' -ScriptBlock $completer

Write-Host "Tab completion loaded" -ForegroundColor Green