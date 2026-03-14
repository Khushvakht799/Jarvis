<#
╔══════════════════════════════════════════════════════════════╗
║               JARVIS BRAIN v2.0 - ЕДИНЫЙ МОЗГ               ║
║           1000 команд + 2 формата + Когнитика               ║
╚══════════════════════════════════════════════════════════════╝
#>

param(
    [string]$Command = "menu"
)

# ------------------------------------------------------------
# 1. КОНФИГУРАЦИЯ
# ------------------------------------------------------------
$ROOT = "C:\Users\Usuario\Jarvis"
$ENGINE = "$ROOT\hybrid_engine"
$INDEX = "$ENGINE\my_index"
$COMMANDS_FILE = "$ROOT\jarvis_commands.json"
$FORMATS_FILE = "$ROOT\jarvis_hybrid_format.json"
$LLAMA_SERVER = "http://localhost:8080/completion"

# ------------------------------------------------------------
# 2. ЗАГРУЗКА КОМАНД И ФОРМАТОВ
# ------------------------------------------------------------
$COMMANDS = Get-Content $COMMANDS_FILE | ConvertFrom-Json
$FORMATS = Get-Content $FORMATS_FILE | ConvertFrom-Json

# ------------------------------------------------------------
# 3. КОГНИТИВНЫЙ ДИСПЕТЧЕР
# ------------------------------------------------------------
function Invoke-Cognitive {
    param(
        [string]$BaseCommand,
        [string]$Modifier,
        [string]$Arguments
    )

    Write-Host "🧠 Применяю когнитивный модификатор: $Modifier" -ForegroundColor Magenta

    # 1. Сначала выполняем базовую команду
    $result = Invoke-BaseCommand $BaseCommand $Arguments

    # 2. Применяем модификатор
    switch ($Modifier) {
        "визуализировать" {
            # Конвертируем результат в граф
            $result | ConvertTo-Json | Out-File "$ROOT\graph.json"
            Write-Host "📊 Граф сохранен в graph.json" -ForegroundColor Green
            
            # Вызываем локальный LLM для интерпретации
            $prompt = "Визуализируй этот граф связей: $result"
            $visual = Invoke-LocalLLM $prompt
            return $visual
        }
        
        "прогнозировать" {
            # Анализируем тренды
            $prompt = "На основе этих данных, спрогнозируй тенденции: $result"
            return Invoke-LocalLLM $prompt
        }
        
        "классифицировать" {
            # Группируем результаты
            return $result | Group-Object -Property Type
        }
        
        "ассоциировать" {
            # Ищем связи в графе памяти
            $prompt = "Найди неочевидные связи в этом контексте: $Arguments"
            return Invoke-LocalLLM $prompt
        }
        
        "критиковать" {
            # Код-ревью
            if (Test-Path $Arguments) {
                $code = Get-Content $Arguments -Raw
                $prompt = "Сделай код-ревью этого файла. Найди проблемы и предложи улучшения: $code"
                return Invoke-LocalLLM $prompt
            }
        }
        
        "генерировать" {
            # Генерация кода
            $prompt = "Напиши код для: $Arguments"
            $code = Invoke-LocalLLM $prompt
            $filename = "generated_$(Get-Date -Format 'yyyyMMdd_HHmmss').rs"
            $code | Out-File $filename
            return "✅ Код сохранен в $filename"
        }
        
        default {
            Write-Host "⚠️ Неизвестный модификатор: $Modifier" -ForegroundColor Yellow
            return $result
        }
    }
}

# ------------------------------------------------------------
# 4. БАЗОВЫЕ КОМАНДЫ
# ------------------------------------------------------------
function Invoke-BaseCommand {
    param([string]$Command, [string]$Args)
    
    switch -Wildcard ($Command) {
        "build" {
            Set-Location $ENGINE
            $result = cargo run --release --no-default-features --bin hybrid_cli -- build $Args $INDEX 2>&1
            return $result
        }
                        "search" {
            Set-Location $ENGINE
            $result = cargo run --release --no-default-features --bin hybrid_cli -- search $INDEX "$Args" 10 2>&1
            return $result
        }
        "stats" {
            Set-Location $ENGINE
            $result = cargo run --release --no-default-features --bin hybrid_cli -- stats $INDEX 2>&1
            return $result
        }
        "ask" {
            return Invoke-LocalLLM $Args
        }
        "ask:with-context" {
            Set-Location $ENGINE
            $searchResult = cargo run --release --no-default-features --bin hybrid_cli -- search $INDEX "$Args" 3 2>&1
            $prompt = "Контекст из базы знаний: $searchResult`n`nВопрос: $Args`n`nОтветь на вопрос, используя контекст."
            return Invoke-LocalLLM $prompt
        }
        default {
            return "❌ Неизвестная команда: $Command"
        }
    }
}

# ------------------------------------------------------------
# 5. ВЫЗОВ ЛОКАЛЬНОГО LLM
# ------------------------------------------------------------
function Invoke-LocalLLM {
    param([string]$Prompt)
    
    $body = @{
        prompt = $Prompt
        n_predict = 500
        temperature = 0.7
        stop = @("</s>", "User:", "Jarvis:")
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $LLAMA_SERVER `
                                     -Method Post `
                                     -Body $body `
                                     -ContentType "application/json" `
                                     -ErrorAction Stop
        return $response.content
    }
    catch {
        Write-Host @"
❌ Локальный LLM не отвечает!
   
   Запусти в другом окне:
   cd C:\Users\Usuario\Jarvis\llama
   .\llama-server.exe -m ..\models\qwen2.5-coder.gguf -ngl 99
   
"@ -ForegroundColor Red
        return "⚠️ Используется режим без LLM"
    }
}

# ------------------------------------------------------------
# 6. ПАРСЕР КОМАНД
# ------------------------------------------------------------
function Invoke-Jarvis {
    param([string]$InputLine)
    
    # Формат 1: команда:модификатор аргументы
    if ($InputLine -match "^(?<cmd>[^:]+):(?<mod>[^\s]+)\s+(?<args>.+)$") {
        $base = $matches['cmd']
        $mod = $matches['mod']
        $args = $matches['args']
        Invoke-Cognitive $base $mod $args
    }
    # Формат 2: обычная команда
    elseif ($InputLine -match "^(?<cmd>[^\s]+)\s+(?<args>.+)$") {
        $base = $matches['cmd']
        $args = $matches['args']
        Invoke-BaseCommand $base $args
    }
    # Команда без аргументов
    elseif ($InputLine -match "^(?<cmd>[^\s]+)$") {
        $base = $matches['cmd']
        switch ($base) {
            "menu" { Show-Menu }
            "stats" { Invoke-BaseCommand "stats" "" }
            default { Write-Host "❌ Неизвестная команда: $base" }
        }
    }
    else {
        Write-Host "❌ Неверный формат. Используй: команда аргументы" -ForegroundColor Red
    }
}

# ------------------------------------------------------------
# 7. МЕНЮ
# ------------------------------------------------------------
function Show-Menu {
    Clear-Host
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                    JARVIS v2.0 - BRAIN                       ║
║          1000 команд · 2 формата · Когнитика                ║
╠══════════════════════════════════════════════════════════════╣
"@ -ForegroundColor Cyan

    # Группируем команды по категориям
    $COMMANDS.commands | Group-Object category | ForEach-Object {
        Write-Host "`n📁 $($_.Name):" -ForegroundColor Yellow
        $_.Group | Select-Object -First 5 | ForEach-Object {
            Write-Host "   $($_.name) → $($_.description)" -ForegroundColor White
        }
    }

    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║  КОГНИТИВНЫЕ МОДИФИКАТОРЫ:                                   ║
║  $(($COMMANDS.cognitive_modifiers | Select-Object -First 5) -join " · ")
║
║  ФОРМАТЫ:                                                     ║
║  • команда:модификатор аргументы                              ║
║  • svdr|binvg:действие параметры                              ║
╠══════════════════════════════════════════════════════════════╣
║  ПРИМЕРЫ:                                                     ║
║  > search:визуализировать графы                              ║
║  > analyze:прогнозировать ./logs                             ║
║  > review:критиковать ./src/main.rs                          ║
║  > generate веб-сервер на Rust                               ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan
}

# ------------------------------------------------------------
# 8. ЗАПУСК
# ------------------------------------------------------------
Clear-Host
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                ║
║     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                ║
║     ██║███████║██████╔╝██║   ██║██║███████╗                ║
║     ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                ║
║     ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║                ║
║     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                ║
║                                                              ║
║           1000 КОМАНД · 2 ФОРМАТА · КОГНИТИКА               ║
║                      ГОТОВ К РАБОТЕ                          ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

if ($Command -ne "menu") {
    Invoke-Jarvis $Command
} else {
    Show-Menu
    Write-Host "`n👉 " -NoNewline
    while ($true) {
        $cmd = Read-Host "Jarvis"
        if ($cmd -eq "exit") { break }
        Invoke-Jarvis $cmd
        Write-Host "`n👉 " -NoNewline
    }
}

