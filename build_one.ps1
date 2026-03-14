# build_one.ps1 - Сборка одного файла

param(
    [Parameter(Mandatory=$true)]
    [string]$SourceDir,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetDir,
    
    [Parameter(Mandatory=$true)]
    [string]$FileName
)

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║        СБОРКА ОДНОГО ФАЙЛА             ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

Write-Host "`n📂 Источник: $SourceDir" -ForegroundColor Cyan
Write-Host "🎯 Цель: $TargetDir" -ForegroundColor Cyan
Write-Host "📄 Файл: $FileName" -ForegroundColor Cyan

# Создаём целевую папку если её нет
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

# Полный путь к исходному файлу
$sourcePath = Join-Path $SourceDir $FileName

if (-not (Test-Path $sourcePath)) {
    Write-Host "❌ Файл не найден: $sourcePath" -ForegroundColor Red
    exit 1
}

# Читаем содержимое
$content = Get-Content $sourcePath -Raw
Write-Host "✅ Файл прочитан: $($content.Length) символов" -ForegroundColor Green

# Функция извлечения кода
function Extract-CodeBlock {
    param([string]$Content)
    
    # Разные варианты блоков кода
    if ($Content -match '```rust\n(.*?)```') {
        return $matches[1].Trim()
    }
    if ($Content -match '```powershell\n(.*?)```') {
        return $matches[1].Trim()
    }
    if ($Content -match '```\n(.*?)```') {
        return $matches[1].Trim()
    }
    if ($Content -match '"(code|content)":\s*"([^"]+)"') {
        return $matches[2].Trim()
    }
    
    return $Content.Trim()
}

# Извлекаем имя целевого файла
$targetFile = $null

if ($content -match 'FILE:\s*([^\n]+)') {
    $targetFile = $matches[1].Trim()
} elseif ($content -match '"file":\s*"([^"]+)"') {
    $targetFile = $matches[1].Trim()
} elseif ($content -match 'path:\s*([^\n]+)') {
    $targetFile = $matches[1].Trim()
} else {
    # Спрашиваем пользователя
    Write-Host "`n❓ Не удалось определить целевой файл." -ForegroundColor Yellow
    Write-Host "   Содержимое начинается с:" -ForegroundColor Gray
    $content.Substring(0, [Math]::Min(200, $content.Length)) -split "`n" | Select-Object -First 5 | ForEach-Object {
        Write-Host "   $_" -ForegroundColor Gray
    }
    
    $targetFile = Read-Host "`n📝 Введите имя целевого файла (например: src/core.rs)"
}

# Очищаем путь от кавычек
$targetFile = $targetFile -replace '"', ''
$targetFile = $targetFile -replace "'", ''

# Полный путь к целевому файлу
$targetPath = Join-Path $TargetDir $targetFile

# Создаём папки если нужно
$targetDirPath = Split-Path $targetPath -Parent
if ($targetDirPath -and $targetDirPath -ne $TargetDir) {
    New-Item -ItemType Directory -Path $targetDirPath -Force | Out-Null
    Write-Host "📁 Создана папка: $targetDirPath" -ForegroundColor Cyan
}

# Извлекаем код
$code = Extract-CodeBlock -Content $content

# Сохраняем
$code | Out-File -FilePath $targetPath -Encoding utf8 -Force

Write-Host "`n✅ Файл сохранён: $targetPath" -ForegroundColor Green
Write-Host "   Размер: $($code.Length) байт" -ForegroundColor Gray

# Если это Rust файл, показываем структуру
if ($targetFile -like "*.rs") {
    $lines = $code -split "`n"
    $structs = $lines | Select-String "struct" | Measure-Object | Select-Object -ExpandProperty Count
    $fns = $lines | Select-String "fn" | Measure-Object | Select-Object -ExpandProperty Count
    
    Write-Host "   Строк кода: $($lines.Count)" -ForegroundColor Gray
    Write-Host "   Структур: $structs" -ForegroundColor Gray
    Write-Host "   Функций: $fns" -ForegroundColor Gray
}