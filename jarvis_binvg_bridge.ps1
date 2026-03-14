# jarvis_binvg_bridge.ps1 - Мост для Python

param(
    [string]$Command,
    [string]$Arg1,
    [string]$Arg2,
    [string]$Arg3
)

# Загружаем модуль
. .\BinVGrSimple.ps1

# Выполняем команду
switch ($Command) {
    "add" {
        $id = Add-BinVGrNode -text $Arg1 -intent $Arg2
        Write-Output "{\"id\": $id, \"status\": \"ok\"}"
    }
    "search" {
        $results = Search-BinVGr -query $Arg1 -topK 5
        $results | ConvertTo-Json -Compress
    }
    "connect" {
        Add-BinVGrEdge -fromId ([int]$Arg1) -toId ([int]$Arg2) -weight ([float]$Arg3)
        Write-Output "{\"status\": \"ok\"}"
    }
    "stats" {
        $nodes = (Get-BinVGrNodes).Count
        Write-Output "{\"nodes\": $nodes}"
    }
    default {
        Write-Output "{\"error\": \"unknown command\"}"
    }
}
