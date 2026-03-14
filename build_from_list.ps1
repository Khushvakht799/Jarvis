param(
    [Parameter(Mandatory=$true)]
    [string]$SourceDir,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetDir,
    
    [Parameter(Mandatory=$true)]
    [string[]]$FileList,
    
    [string]$ProjectName = "binvg_sdk"
)

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  СБОРЩИК ФАЙЛОВОЙ СИСТЕМЫ ИЗ СПИСКА    ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

Write-Host "`n📂 Источник: $SourceDir" -ForegroundColor Cyan
Write-Host "🎯 Цель: $TargetDir" -ForegroundColor Cyan
Write-Host "📋 Файлов для обработки: $($FileList.Count)" -ForegroundColor Cyan

# Создаём целевую папку
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
Set-Location $TargetDir

# Создаём структуру проекта
Write-Host "`n📁 Создаю структуру проекта $ProjectName..." -ForegroundColor Yellow

$folders = @(
    "src",
    "tests",
    "benches",
    "examples",
    "target"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path "$TargetDir\$folder" -Force | Out-Null
    Write-Host "  ✅ Создана папка: $folder" -ForegroundColor Green
}

# Функция для извлечения содержимого между маркерами
function Extract-CodeBlock {
    param([string]$Content, [string]$Filename)
    
    # Ищем блоки кода в markdown или json
    if ($Content -match '```rust\n(.*?)```' -or 
        $Content -match '```powershell\n(.*?)```' -or
        $Content -match '```\n(.*?)```') {
        return $matches[1].Trim()
    }
    
    # Если нет блоков кода, возвращаем весь контент
    return $Content.Trim()
}

# Обрабатываем каждый файл из списка
Write-Host "`n📄 Обработка файлов:" -ForegroundColor Yellow

$processedFiles = @()

foreach ($fileName in $FileList) {
    $sourcePath = Join-Path $SourceDir $fileName
    
    if (Test-Path $sourcePath) {
        Write-Host "  📖 Читаю: $fileName" -ForegroundColor Gray
        
        # Читаем содержимое
        $content = Get-Content $sourcePath -Raw
        
        # Извлекаем имя целевого файла из содержимого (если есть маркер)
        $targetFile = $null
        
        if ($content -match 'FILE:\s*([^\n]+)') {
            $targetFile = $matches[1].Trim()
        } elseif ($content -match '"file":\s*"([^"]+)"') {
            $targetFile = $matches[1].Trim()
        } else {
            # Если нет маркера, используем имя исходного файла с .rs
            $targetFile = "$fileName.rs"
        }
        
        # Очищаем путь от лишних символов
        $targetFile = $targetFile -replace '["`''"']', ''
        
        # Формируем полный путь к целевому файлу
        $targetPath = Join-Path $TargetDir $targetFile
        
        # Создаём папки если нужно
        $targetDir_path = Split-Path $targetPath -Parent
        if ($targetDir_path -and $targetDir_path -ne $TargetDir) {
            New-Item -ItemType Directory -Path $targetDir_path -Force | Out-Null
        }
        
        # Извлекаем код
        $code = Extract-CodeBlock -Content $content -Filename $fileName
        
        # Сохраняем
        $code | Out-File -FilePath $targetPath -Encoding utf8 -Force
        
        Write-Host "    ✅ Записан: $targetFile" -ForegroundColor Green
        $processedFiles += [PSCustomObject]@{
            Source = $fileName
            Target = $targetFile
            Size = ($code.Length)
        }
    } else {
        Write-Host "  ❌ Файл не найден: $fileName" -ForegroundColor Red
    }
}

# Создаём Cargo.toml если его нет в списке
if ($processedFiles.Target -notcontains "Cargo.toml") {
    Write-Host "`n📝 Создаю Cargo.toml..." -ForegroundColor Yellow
    
    $cargoToml = @"
[package]
name = "$ProjectName"
version = "1.0.0"
edition = "2021"
authors = ["Khushvakht Raupov"]
license = "MIT"

[dependencies]
memmap2 = "0.9"
byteorder = "1.5"
anyhow = "1.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
reqwest = { version = "0.12", features = ["blocking", "json"] }
bytemuck = "1.14"
crossbeam-channel = "0.5"
rayon = "1.10"
tokio = { version = "1.0", features = ["full"], optional = true }

[dev-dependencies]
criterion = "0.5"
tempfile = "3.8"

[features]
default = ["sync"]
sync = []
async = ["tokio", "futures"]

[[bench]]
name = "pipeline_bench"
harness = false
"@
    
    $cargoToml | Out-File -FilePath "$TargetDir\Cargo.toml" -Encoding utf8
    Write-Host "  ✅ Cargo.toml создан" -ForegroundColor Green
}

# Создаём lib.rs если его нет
if ($processedFiles.Target -notcontains "src\lib.rs") {
    Write-Host "`n📝 Создаю src\lib.rs..." -ForegroundColor Yellow
    
    $libRs = @"
//! $ProjectName v1.0 SDK

pub mod core;
pub mod adapter;
pub mod pipeline;
pub mod error;

pub use anyhow::Result;
"@
    
    New-Item -ItemType Directory -Path "$TargetDir\src" -Force | Out-Null
    $libRs | Out-File -FilePath "$TargetDir\src\lib.rs" -Encoding utf8
    Write-Host "  ✅ src\lib.rs создан" -ForegroundColor Green
}

# Выводим статистику
Write-Host "`n📊 СТАТИСТИКА СБОРКИ:" -ForegroundColor Magenta
Write-Host "  Всего обработано: $($processedFiles.Count) файлов" -ForegroundColor Cyan
$totalSize = ($processedFiles | Measure-Object -Property Size -Sum).Sum
Write-Host "  Общий размер кода: $([math]::Round($totalSize/1KB, 2)) KB" -ForegroundColor Cyan
Write-Host "  Целевая папка: $TargetDir" -ForegroundColor Cyan

Write-Host "`n📋 СПИСОК СОЗДАННЫХ ФАЙЛОВ:" -ForegroundColor Yellow
$processedFiles | Format-Table Source, Target, @{Name="Size(KB)";Expression={[math]::Round($_.Size/1KB, 2)}} -AutoSize

Write-Host "`n✅ СБОРКА ЗАВЕРШЕНА" -ForegroundColor Green
Write-Host "🚀 Для компиляции выполните:" -ForegroundColor Yellow
Write-Host "  cd $TargetDir" -ForegroundColor Cyan
Write-Host "  cargo build --release" -ForegroundColor Cyan