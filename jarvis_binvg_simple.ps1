# jarvis_binvg_simple.ps1 - Интеграция с Jarvis

. .\BinVGrSimple.ps1

function Invoke-BinVGrCommand {
    param([string]$command, [string]$arg1, [string]$arg2)
    
    switch ($command) {
        "add" {
            $id = Add-BinVGrNode -text $arg1 -intent $arg2
            return "✅ Добавлен ID: $id"
        }
        "search" {
            $results = Search-BinVGr -query $arg1 -topK 5
            return $results | ConvertTo-Json -Compress
        }
        "stats" {
            Show-BinVGrStats
            return "OK"
        }
        "connect" {
            Add-BinVGrEdge -fromId [int]$arg1 -toId [int]$arg2
            return "✅ Связь добавлена"
        }
        default {
            return "❌ Неизвестная команда"
        }
    }
}

Export-ModuleMember -Function Invoke-BinVGrCommand