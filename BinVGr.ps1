# BinVGrSimple.ps1 - Упрощенная версия для Jarvis

# Глобальная переменная для хранения графа
$script:BinVGrMemory = @{
    nodes = @{}
    edges = @()
    nextId = 0
}

# Функция инициализации
function Init-BinVGr {
    $path = "jarvis_binvg.json"
    if (Test-Path $path) {
        $script:BinVGrMemory = Get-Content $path | ConvertFrom-Json -AsHashtable
        Write-Host "📂 Загружена память из $path" -ForegroundColor Yellow
    } else {
        # Начальные данные
        $script:BinVGrMemory = @{
            nodes = @{}
            edges = @()
            nextId = 0
        }
        Write-Host "📁 Создана новая память" -ForegroundColor Green
    }
}

# Сохранение
function Save-BinVGr {
    $script:BinVGrMemory | ConvertTo-Json -Depth 10 | Set-Content "jarvis_binvg.json"
}

# Добавление узла
function Add-BinVGrNode {
    param(
        [string]$text,
        [string]$intent = "memory"
    )
    
    $id = $script:BinVGrMemory.nextId
    $script:BinVGrMemory.nodes[$id] = @{
        id = $id
        text = $text
        intent = $intent
        created = (Get-Date).ToString()
        weight = 1.0
    }
    $script:BinVGrMemory.nextId++
    
    Save-BinVGr
    Write-Host "✅ Добавлен узел [$id]: $text" -ForegroundColor Green
    return $id
}

# Добавление связи
function Add-BinVGrEdge {
    param(
        [int]$fromId,
        [int]$toId,
        [float]$weight = 0.7,
        [string]$type = "related"
    )
    
    $edge = @{
        from = $fromId
        to = $toId
        weight = $weight
        type = $type
    }
    $script:BinVGrMemory.edges += $edge
    
    Save-BinVGr
    Write-Host "🔗 Связь: $fromId → $toId (вес: $weight)" -ForegroundColor Cyan
}

# Поиск (простой, по словам)
function Search-BinVGr {
    param(
        [string]$query,
        [int]$topK = 5
    )
    
    $words = $query.ToLower().Split(' ',[StringSplitOptions]::RemoveEmptyEntries)
    $results = @()
    
    foreach ($id in $script:BinVGrMemory.nodes.Keys) {
        $node = $script:BinVGrMemory.nodes[$id]
        $text = $node.text.ToLower()
        
        # Считаем совпадения
        $matches = 0
        foreach ($word in $words) {
            if ($text.Contains($word)) {
                $matches++
            }
        }
        
        if ($matches -gt 0) {
            $score = $matches / $words.Count
            
            # Учитываем вес узла и связи
            $edgeWeight = 0
            foreach ($edge in $script:BinVGrMemory.edges) {
                if ($edge.from -eq $id -or $edge.to -eq $id) {
                    $edgeWeight += $edge.weight
                }
            }
            
            $finalScore = $score * (1 + $edgeWeight * 0.1)
            
            $results += @{
                id = $id
                text = $node.text
                intent = $node.intent
                score = $finalScore
            }
        }
    }
    
    $results = $results | Sort-Object -Property score -Descending | Select-Object -First $topK
    return $results
}

# Статистика
function Show-BinVGrStats {
    Write-Host "`n📊 BinVGr Statistics:" -ForegroundColor Magenta
    Write-Host "  Узлов: $($script:BinVGrMemory.nodes.Count)" -ForegroundColor Yellow
    Write-Host "  Связей: $($script:BinVGrMemory.edges.Count)" -ForegroundColor Yellow
    
    if ($script:BinVGrMemory.nodes.Count -gt 0) {
        Write-Host "`n📝 Узлы:" -ForegroundColor Green
        $script:BinVGrMemory.nodes.Keys | ForEach-Object {
            $node = $script:BinVGrMemory.nodes[$_]
            Write-Host "  [$($node.id)] $($node.text) [$($node.intent)]" -ForegroundColor Cyan
        }
    }
    
    if ($script:BinVGrMemory.edges.Count -gt 0) {
        Write-Host "`n🔗 Связи:" -ForegroundColor Yellow
        $script:BinVGrMemory.edges | ForEach-Object {
            Write-Host "  $($_.from) → $($_.to) [вес:$($_.weight)]" -ForegroundColor Cyan
        }
    }
}

# Инициализация при загрузке
Init-BinVGr

# Добавляем начальные данные, если память пуста
if ($script:BinVGrMemory.nodes.Count -eq 0) {
    Write-Host "📥 Загрузка начальных данных..." -ForegroundColor Yellow
    
    $id1 = Add-BinVGrNode -text "приветствие" -intent "greeting"
    $id2 = Add-BinVGrNode -text "вопрос" -intent "question"
    $id3 = Add-BinVGrNode -text "команда" -intent "command"
    $id4 = Add-BinVGrNode -text "функция на python" -intent "coding_task"
    $id5 = Add-BinVGrNode -text "история разговора" -intent "context"
    
    Add-BinVGrEdge -fromId $id4 -toId $id5 -weight 0.8
    Add-BinVGrEdge -fromId $id1 -toId $id2 -weight 0.5
    
    Show-BinVGrStats
}

# Экспорт функций
Export-ModuleMember -Function Add-BinVGrNode, Add-BinVGrEdge, Search-BinVGr, Show-BinVGrStats, Init-BinVGr, Save-BinVGr