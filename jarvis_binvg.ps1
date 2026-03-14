# jarvis_binvg.ps1 - Запуск Jarvis с BinVGr-памятью

# Загружаем BinVGr
. .\BinVGr.ps1

# Глобальная переменная для доступа из команд
$script:binvg = $null

# Функция инициализации
function Init-BinVGr {
    if (-not $script:binvg) {
        $script:binvg = [BinVGr]::new("jarvis.binvg")
        
        # Загружаем историю из логов, если есть
        $logFile = "logs\chat_history.json"
        if (Test-Path $logFile) {
            Write-Host "📚 Загружаю историю в BinVGr..." -ForegroundColor Yellow
            $history = Get-Content $logFile | ConvertFrom-Json
            foreach ($msg in $history) {
                $script:binvg.Add($msg.text, "history")
            }
        }
    }
    return $script:binvg
}

# Переопределяем команду chat для использования BinVGr
function Invoke-BinVGrChat {
    param([string]$Text)
    
    $bvg = Init-BinVGr
    
    # Поиск релевантной памяти
    $memories = $bvg.Search($Text, 3)
    
    # Формируем контекст
    $context = "🧠 BinVGr Memory:\n"
    foreach ($mem in $memories) {
        $context += "  • $($mem.Text) [релевантность: $([math]::Round($mem.Similarity*100,0))%]\n"
    }
    
    # Здесь должен быть вызов твоей LLM
    Write-Host "`n🤔 Запрос к модели с контекстом..." -ForegroundColor Yellow
    Write-Host $context -ForegroundColor Cyan
    
    # Эмулируем ответ модели (замени на реальный вызов Ollama)
    $response = "Ответ модели с учётом памяти..."
    
    # Запоминаем диалог
    $bvg.Add("User: $Text", "user_query")
    $bvg.Add("Assistant: $response", "assistant_response")
    
    return $response
}

# Добавляем новые команды в Jarvis
$commands = @{
    'bvg-stats' = { 
        $bvg = Init-BinVGr
        $bvg.Stats()
    }
    'bvg-search' = {
        param($query)
        $bvg = Init-BinVGr
        $results = $bvg.Search($query)
        $results | Format-Table Id, Text, Intent, @{Name="Similarity"; Expression={[math]::Round($_.Similarity*100,1)}} -AutoSize
    }
    'bvg-add' = {
        param($text, $intent="memory")
        $bvg = Init-BinVGr
        $id = $bvg.Add($text, $intent)
        Write-Host "✅ Добавлен ID: $id" -ForegroundColor Green
    }
    'bvg-viz' = {
        $bvg = Init-BinVGr
        $bvg.Visualize()
    }
    'chat-bvg' = {
        param($text)
        Invoke-BinVGrChat $text
    }
}

# Вывод справки
Write-Host "`n📌 BinVGr команды загружены:" -ForegroundColor Magenta
Write-Host "  bvg-stats     - Статистика бинарной памяти" -ForegroundColor Cyan
Write-Host "  bvg-search    - Поиск в памяти" -ForegroundColor Cyan
Write-Host "  bvg-add       - Добавить в память" -ForegroundColor Cyan
Write-Host "  bvg-viz       - Визуализация графа" -ForegroundColor Cyan
Write-Host "  chat-bvg      - Чат с использованием памяти" -ForegroundColor Cyan

# Экспортируем функции
Export-ModuleMember -Function Init-BinVGr, Invoke-BinVGrChat -Variable commands