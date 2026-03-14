# run_binvg.ps1 - Запуск BinVGr в твоём Jarvis

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║     BinVGr - Бинарный Векторный Граф    ║" -ForegroundColor Magenta
Write-Host "║         Интеграция с Jarvis             ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

# Загружаем модуль
. .\BinVGr.ps1

# Проверяем запущен ли Ollama
$ollama = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "⚠️ Ollama не запущен. Запускаю..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve"
    Start-Sleep -Seconds 3
}

# Создаём или загружаем BinVGr
$bvg = [BinVGr]::new("jarvis.binvg")

# Добавляем начальные данные из твоего лога
Write-Host "`n📥 Загрузка начальных данных..." -ForegroundColor Yellow

$initialData = @(
    @{Text="приветствие"; Intent="greeting"},
    @{Text="вопрос"; Intent="question"},
    @{Text="команда"; Intent="command"},
    @{Text="функция на python"; Intent="coding_task"},
    @{Text="история разговора"; Intent="context"}
)

$ids = @{}
foreach ($item in $initialData) {
    $id = $bvg.Add($item.Text, $item.Intent)
    $ids[$item.Text] = $id
}

# Добавляем связи
$bvg.Connect($ids["функция на python"], $ids["история разговора"], 0.8, "related")
$bvg.Connect($ids["приветствие"], $ids["вопрос"], 0.5, "related")

# Показываем статистику
$bvg.Stats()

# Интерактивный режим
Write-Host "`n💬 Интерактивный режим BinVGr" -ForegroundColor Green
Write-Host "Команды: search <текст>, add <текст> [интент], connect <id1> <id2> [вес], stats, viz, exit" -ForegroundColor Yellow

while ($true) {
    $input = Read-Host "`nBinVGr> "
    
    if ($input -eq "exit") { break }
    
    if ($input -match "^search (.+)$") {
        $query = $matches[1]
        $results = $bvg.Search($query, 10)
        Write-Host "`n🔍 Результаты поиска:" -ForegroundColor Cyan
        foreach ($r in $results) {
            $pct = [math]::Round($r.Similarity * 100, 1)
            Write-Host "  [$($r.Id)] $($r.Text) [$($r.Intent)] - $pct%" -ForegroundColor White
        }
    }
    elseif ($input -match "^add (.+?)(?: (.+))?$") {
        $text = $matches[1]
        $intent = if ($matches[2]) { $matches[2] } else { "memory" }
        $id = $bvg.Add($text, $intent)
        Write-Host "✅ Добавлен узел ID: $id" -ForegroundColor Green
    }
    elseif ($input -match "^connect (\d+) (\d+)(?: (\d+\.?\d*))?$") {
        $from = [int]$matches[1]
        $to = [int]$matches[2]
        $weight = if ($matches[3]) { [float]$matches[3] } else { 0.7 }
        $bvg.Connect($from, $to, $weight)
    }
    elseif ($input -eq "stats") {
        $bvg.Stats()
    }
    elseif ($input -eq "viz") {
        $bvg.Visualize()
    }
    elseif ($input -eq "") {
        # ничего
    }
    else {
        Write-Host "Неизвестная команда" -ForegroundColor Red
    }
}

# Закрываем
$bvg.Close()
Write-Host "`n👋 BinVGr завершил работу" -ForegroundColor Magenta