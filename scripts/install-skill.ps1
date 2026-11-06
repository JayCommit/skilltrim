# Copy the skilltrim agent skill into host skill folders.
# Windows counterpart of scripts/install-skill.sh. $Host is reserved in
# PowerShell, so --host is parsed manually and stored in $SkillHost.
# This file does not claim it was executed on Windows.
$ErrorActionPreference = 'Stop'

$SkillHost = 'all'
$InstallScope = 'user'

function Show-Usage {
    Write-Output 'Usage: powershell -ExecutionPolicy Bypass -File .\scripts\install-skill.ps1 [--host HOST] [--scope SCOPE]'
    Write-Output ''
    Write-Output 'Copy SKILL.md and the files the skill uses into a host folder named skilltrim.'
    Write-Output 'SKILL.md sits directly in that folder (not skilltrim\skilltrim). Copies the'
    Write-Output 'bundled CLI (scripts\skilltrim.py, src\skilltrim), pyproject.toml, README.md,'
    Write-Output 'LICENSE, and the linked reference benchmarks\README.md. Does not copy .git,'
    Write-Output '.venv, or benchmark corpora.'
    Write-Output ''
    Write-Output '--host   grok | grok-bot | cursor | openai | antigravity | claude | all'
    Write-Output '         (default: all)'
    Write-Output '--scope  user | project'
    Write-Output '         (default: user)'
    Write-Output ''
    Write-Output 'User scope writes under the user profile. Project scope writes under the current directory.'
    Write-Output 'Grok Bot also prints a paste-in prompt. This script does not prove an agent'
    Write-Output 'discovered or followed the skill.'
}

$index = 0
while ($index -lt $args.Count) {
    $arg = [string]$args[$index]
    if ($arg -eq '--help' -or $arg -eq '-h') {
        Show-Usage
        exit 0
    } elseif ($arg -eq '--host' -or $arg -eq '-host') {
        if ($index + 1 -ge $args.Count) {
            [Console]::Error.WriteLine('skilltrim: --host requires a value')
            exit 2
        }
        $SkillHost = [string]$args[$index + 1]
        $index += 2
    } elseif ($arg.StartsWith('--host=')) {
        $SkillHost = $arg.Substring(7)
        $index += 1
    } elseif ($arg -eq '--scope' -or $arg -eq '-scope') {
        if ($index + 1 -ge $args.Count) {
            [Console]::Error.WriteLine('skilltrim: --scope requires a value')
            exit 2
        }
        $InstallScope = [string]$args[$index + 1]
        $index += 2
    } elseif ($arg.StartsWith('--scope=')) {
        $InstallScope = $arg.Substring(8)
        $index += 1
    } else {
        [Console]::Error.WriteLine("skilltrim: unknown argument: $arg")
        exit 2
    }
}

$knownHosts = @('grok', 'grok-bot', 'cursor', 'openai', 'antigravity', 'claude', 'all')
$knownScopes = @('user', 'project')
if ($knownHosts -notcontains $SkillHost) {
    [Console]::Error.WriteLine("skilltrim: unknown host '$SkillHost'")
    exit 2
}
if ($knownScopes -notcontains $InstallScope) {
    [Console]::Error.WriteLine("skilltrim: unknown scope '$InstallScope'")
    exit 2
}

$script:Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$SkillMd = Join-Path $script:Root 'SKILL.md'
$front = Get-Content -LiteralPath $SkillMd -TotalCount 80
$nameLine = $front | Where-Object { $_ -match '^name:\s*' } | Select-Object -First 1
$descLine = $front | Where-Object { $_ -match '^description:\s*' } | Select-Object -First 1
$name = ''
$desc = ''
if ($nameLine) { $name = ([string]$nameLine -replace '^name:\s*', '').Trim() }
if ($descLine) { $desc = ([string]$descLine -replace '^description:\s*', '').Trim() }
if ($name -ne 'skilltrim') {
    [Console]::Error.WriteLine("skilltrim: SKILL.md name must match folder skilltrim (found '$name')")
    exit 2
}
if (-not $desc) {
    [Console]::Error.WriteLine('skilltrim: description is required in SKILL.md frontmatter')
    exit 2
}

function Assert-Installed {
    param([string]$Destination)
    $skillFile = Join-Path $Destination 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        [Console]::Error.WriteLine("skilltrim: missing SKILL.md in $Destination")
        exit 1
    }
    if (Test-Path -LiteralPath (Join-Path $Destination 'skilltrim')) {
        [Console]::Error.WriteLine("skilltrim: double-nested skill folder: $Destination\skilltrim")
        exit 1
    }
    foreach ($forbidden in @('.git', '.venv')) {
        if (Test-Path -LiteralPath (Join-Path $Destination $forbidden)) {
            [Console]::Error.WriteLine("skilltrim: copied .git or .venv into $Destination")
            exit 1
        }
    }
    foreach ($corpus in @(
            'benchmarks\fixtures',
            'benchmarks\real-results.json',
            'benchmarks\real-example.json',
            'benchmarks\baseline.json'
        )) {
        if (Test-Path -LiteralPath (Join-Path $Destination $corpus)) {
            [Console]::Error.WriteLine("skilltrim: copied benchmark corpora into $Destination")
            exit 1
        }
    }
    foreach ($required in @(
            'benchmarks\README.md',
            'scripts\skilltrim.py',
            'src\skilltrim\cli.py',
            'src\skilltrim\__init__.py',
            'pyproject.toml'
        )) {
        if (-not (Test-Path -LiteralPath (Join-Path $Destination $required) -PathType Leaf)) {
            [Console]::Error.WriteLine("skilltrim: missing bundled skill file $required in $Destination")
            exit 1
        }
    }
}

function Copy-SkillTrim {
    param([string]$Destination)
    if (-not $Destination.EndsWith('\skilltrim') -and -not $Destination.EndsWith('/skilltrim')) {
        [Console]::Error.WriteLine("skilltrim: refusing destination that is not a skilltrim folder: $Destination")
        exit 2
    }
    if (Test-Path -LiteralPath $Destination) {
        $item = Get-Item -LiteralPath $Destination -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Remove-Item -LiteralPath $Destination -Force
        } elseif (-not $item.PSIsContainer) {
            [Console]::Error.WriteLine("skilltrim: destination exists and is not a directory: $Destination")
            exit 2
        } else {
            Remove-Item -LiteralPath $Destination -Recurse -Force
        }
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $Destination 'benchmarks') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Destination 'scripts') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Destination 'src\skilltrim') | Out-Null
    Copy-Item -LiteralPath (Join-Path $script:Root 'SKILL.md') -Destination (Join-Path $Destination 'SKILL.md') -Force
    Copy-Item -LiteralPath (Join-Path $script:Root 'README.md') -Destination (Join-Path $Destination 'README.md') -Force
    Copy-Item -LiteralPath (Join-Path $script:Root 'LICENSE') -Destination (Join-Path $Destination 'LICENSE') -Force
    Copy-Item -LiteralPath (Join-Path $script:Root 'pyproject.toml') -Destination (Join-Path $Destination 'pyproject.toml') -Force
    Copy-Item -LiteralPath (Join-Path $script:Root 'benchmarks\README.md') -Destination (Join-Path $Destination 'benchmarks\README.md') -Force
    Copy-Item -LiteralPath (Join-Path $script:Root 'scripts\skilltrim.py') -Destination (Join-Path $Destination 'scripts\skilltrim.py') -Force
    Get-ChildItem -LiteralPath (Join-Path $script:Root 'src\skilltrim') -Filter '*.py' -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Destination 'src\skilltrim') -Force
    }
    Assert-Installed -Destination $Destination
    Write-Output "Installed $Destination"
}

$script:dests = New-Object System.Collections.Generic.List[string]
function Add-Dest {
    param([string]$Candidate)
    if (-not $script:dests.Contains($Candidate)) {
        [void]$script:dests.Add($Candidate)
    }
}

if ($InstallScope -eq 'user') {
    $Base = $env:USERPROFILE
    if (-not $Base) { $Base = $env:HOME }
    if (-not $Base) {
        [Console]::Error.WriteLine('skilltrim: HOME is not set')
        exit 2
    }
    $Base = $Base.TrimEnd('\', '/')
} else {
    $Base = (Get-Location).ProviderPath
    if (-not $Base) { $Base = (Get-Location).Path }
}

switch ($SkillHost) {
    { $_ -in @('grok', 'grok-bot') } {
        Add-Dest (Join-Path $Base '.grok\skills\skilltrim')
        break
    }
    'cursor' {
        Add-Dest (Join-Path $Base '.cursor\skills\skilltrim')
        break
    }
    'openai' {
        Add-Dest (Join-Path $Base '.agents\skills\skilltrim')
        break
    }
    'antigravity' {
        if ($InstallScope -eq 'project') {
            Add-Dest (Join-Path $Base '.agents\skills\skilltrim')
        } else {
            Add-Dest (Join-Path $Base '.gemini\config\skills\skilltrim')
            Add-Dest (Join-Path $Base '.gemini\antigravity-cli\skills\skilltrim')
        }
        break
    }
    'claude' {
        Add-Dest (Join-Path $Base '.claude\skills\skilltrim')
        break
    }
    'all' {
        Add-Dest (Join-Path $Base '.grok\skills\skilltrim')
        Add-Dest (Join-Path $Base '.cursor\skills\skilltrim')
        Add-Dest (Join-Path $Base '.agents\skills\skilltrim')
        if ($InstallScope -eq 'user') {
            Add-Dest (Join-Path $Base '.gemini\config\skills\skilltrim')
            Add-Dest (Join-Path $Base '.gemini\antigravity-cli\skills\skilltrim')
        }
        Add-Dest (Join-Path $Base '.claude\skills\skilltrim')
        break
    }
}

foreach ($dest in $script:dests) {
    Copy-SkillTrim -Destination $dest
}

if ($InstallScope -eq 'user') {
    Write-Output 'Scope: user. Project paths were not changed. Re-run with --scope project to install .grok, .cursor, .agents, and .claude under the current directory.'
} else {
    Write-Output "Scope: project. Home skill directories were not changed. Antigravity's user paths are ~/.gemini/config/skills/skilltrim and ~/.gemini/antigravity-cli/skills/skilltrim."
}

if ($SkillHost -eq 'grok' -or $SkillHost -eq 'all') {
    Write-Output 'Grok: invoke /skilltrim'
}
if ($SkillHost -eq 'grok-bot' -or $SkillHost -eq 'all') {
    Write-Output 'Grok Bot paste-in prompt:'
    Write-Output 'Clone https://github.com/JayCommit/skilltrim and copy its agent skill into ~/.grok/skills/skilltrim/ on the bot computer. Copy SKILL.md plus the files that skill uses (bundled scripts/skilltrim.py, src/skilltrim, and linked references such as benchmarks/README.md). Do not copy .git, .venv, or benchmark corpora. Do not nest another skilltrim directory inside the destination; SKILL.md must sit directly at ~/.grok/skills/skilltrim/SKILL.md. Use the same SKILL.md from that repository. Invoke /skilltrim.'
}
if ($SkillHost -eq 'cursor' -or $SkillHost -eq 'all') {
    Write-Output 'Cursor: folder name matches skill name skilltrim. Invoke /skilltrim'
}
if ($SkillHost -eq 'openai' -or $SkillHost -eq 'all') {
    Write-Output 'OpenAI / ChatGPT app: zip the skilltrim folder (SKILL.md directly inside it). Plugins -> Skills -> Add -> Upload. Codex: $skilltrim'
}
if ($SkillHost -eq 'antigravity' -or $SkillHost -eq 'all') {
    Write-Output 'Antigravity: description is required in SKILL.md. Project path is one level at .agents/skills/skilltrim. Invoke /skilltrim'
}
if ($SkillHost -eq 'claude' -or $SkillHost -eq 'all') {
    Write-Output 'Claude: invoke /skilltrim'
}
