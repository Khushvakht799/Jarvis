# run_binvg_simple.ps1

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║     BinVGr Simple - Для Jarvis         ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

# Загружаем модуль
. .\BinVGrSimple.ps1

# Добавляем начальные данные
if ((Get-BinVGrNodes).Count -eq 0) {
    Write-Host "`n📥 Загрузка начальных данных..." -ForegroundColor Yellow
    
    $id1 = Add-BinVGrNode -text "приветствие" -intent "greeting"
    $id2 = Add-BinVGrNode -text "вопрос" -intent "question"
    $id3 = Add-BinVGrNode -text "команда" -intent "command"
    $id4 = Add-BinVGrNode -text "функция на python" -intent "coding"
    $id5 = Add-BinVGrNode -text "история разговора" -intent "context"
    
    Add-BinVGrEdge -fromId $id4 -toId $id5 -weight 0.8
    Add-BinVGrEdge -fromId $id1 -toId $id2 -weight 0.5
}

Show-BinVGrStats

# Интерактивный режим
Write-Host "`n💬 Команды:" -ForegroundColor Green
Write-Host "  add <текст> [интент]" -ForegroundColor Cyan
Write-Host "  search <текст>" -ForegroundColor Cyan
Write-Host "  connect <id1> <id2> [вес]" -ForegroundColor Cyan
Write-Host "  list" -ForegroundColor Cyan
Write-Host "  stats" -ForegroundColor Cyan
Write-Host "  exit" -ForegroundColor Cyan

while ($true) {
    $input = Read-Host "`nBinVGr> "
    
    if ($input -eq "exit") { break }
    
    if ($input -match "^add (.+?)(?: (.+))?$") {
        $text = $matches[1]
        $intent = if ($matches[2]) { $matches[2] } else { "memory" }
        Add-BinVGrNode -text $text -intent $intent
    }
    elseif ($input -match "^search (.+)$") {
        $query = $matches[1]
        $results = Search-BinVGr -query $query
        Write-Host "`n🔍 Результаты:" -ForegroundColor Cyan
        if ($results.Count -eq 0) {
            Write-Host "  Ничего не найдено" -ForegroundColor Gray
        } else {
            $results | ForEach-Object {
                $pct = [math]::Round($_.score * 100, 1)
                Write-Host "  [$($_.id)] $($_.text) [$($_.intent)] - $pct%" -ForegroundColor White
            }
        }
    }
    elseif ($input -match "^connect (\d+) (\d+)(?: (\d+\.?\d*))?$") {
        $from = [int]$matches[1]
        $to = [int]$matches[2]
        $weight = if ($matches[3]) { [float]$matches[3] } else { 0.7 }
        Add-BinVGrEdge -fromId $from -toId $to -weight $weight
    }
    elseif ($input -eq "list") {
        $nodes = Get-BinVGrNodes
        Write-Host "`n📝 Узлы:" -ForegroundColor Green
        foreach ($id in $nodes.Keys) {
            $node = $nodes[$id]
            Write-Host "  [$($node.id)] $($node.text) [$($node.intent)]" -ForegroundColor Cyan
        }
    }
    elseif ($input -eq "stats") {
        Show-BinVGrStats
    }
}

Write-Host "`n👋 Пока!" -ForegroundColor Magenta
