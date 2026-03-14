# Jarvis CLI с BinVGr SDK
$sdkPath = "C:\Users\Usuario\Jarvis\binvg_sdk\target\release\binvg_sdk.dll"

function Ask-Jarvis {
    param([string]$Question)
    
    # TODO: вызвать SDK через FFI или отдельный Rust бинарник
    Write-Host "🤔 Думаю..." -ForegroundColor Yellow
    Write-Host "💬 Ответ: " -ForegroundColor Green
}

function Add-Knowledge {
    param([string]$Text)
    Write-Host "📚 Добавляю: $Text" -ForegroundColor Cyan
}

function Show-Stats {
    Write-Host "📊 Статистика графа" -ForegroundColor Magenta
}

$menu = @"
╔══════════════════════════════════════════╗
║     JARVIS CLI с BinVGr SDK             ║
╠══════════════════════════════════════════╣
║  ask <вопрос>   - задать вопрос         ║
║  add <текст>    - добавить знание       ║
║  stats          - статистика графа      ║
║  exit           - выход                  ║
╚══════════════════════════════════════════╝
"@

while ($true) {
    Write-Host $menu -ForegroundColor Cyan
    $input = Read-Host "`njarvis"
    
    switch -Regex ($input) {
        '^ask (.+)$' { Ask-Jarvis $matches[1] }
        '^add (.+)$' { Add-Knowledge $matches[1] }
        '^stats$' { Show-Stats }
        '^exit$' { break }
        default { Write-Host "❌ Неизвестная команда" -ForegroundColor Red }
    }
}
