# BinVGrSimple.ps1 - Простая версия для Jarvis

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
        $content = Get-Content $path -Raw
        if ($content) {
            $script:BinVGrMemory = $content | ConvertFrom-Json -AsHashtable
            Write-Host "📂 Загружена память из $path" -ForegroundColor Yellow
        }
    } else {
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
    $script:BinVGrMemory.nodes["$id"] = @{
        id = $id
        text = $text
        intent = $intent
        created = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
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
        [float]$weight = 0.7
    )
    
    $edge = @{
        from = $fromId
        to = $toId
        weight = $weight
    }
    $script:BinVGrMemory.edges += $edge
    
    Save-BinVGr
    Write-Host "🔗 Связь: $fromId → $toId (вес: $weight)" -ForegroundColor Cyan
}

# Поиск
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
        
        $matches = 0
        foreach ($word in $words) {
            if ($text.Contains($word)) { $matches++ }
        }
        
        if ($matches -gt 0) {
            $score = $matches / $words.Count
            $results += @{
                id = $id
                text = $node.text
                intent = $node.intent
                score = $score
            }
        }
    }
    
    return $results | Sort-Object -Property score -Descending | Select-Object -First $topK
}

# Получить все узлы
function Get-BinVGrNodes {
    return $script:BinVGrMemory.nodes
}

# Статистика
function Show-BinVGrStats {
    Write-Host "`n📊 Статистика:" -ForegroundColor Magenta
    Write-Host "  Узлов: $($script:BinVGrMemory.nodes.Count)" -ForegroundColor Yellow
    Write-Host "  Связей: $($script:BinVGrMemory.edges.Count)" -ForegroundColor Yellow
}

# Инициализация
Init-BinVGr

# Экспорт функций
Export-ModuleMember -Function Add-BinVGrNode, Add-BinVGrEdge, Search-BinVGr, Show-BinVGrStats, Get-BinVGrNodes
