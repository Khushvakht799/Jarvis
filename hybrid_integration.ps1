#!powershell
# hybrid_integration.ps1 - Интеграция гибридного движка с Jarvis

Write-Host "🔗 Интеграция SVDR+BinVGr Hybrid с Jarvis" -ForegroundColor Cyan

# Пути
 = "C:\Users\Usuario\Jarvis"
 = Join-Path  "hybrid_engine"
 = Join-Path  "data\hybrid_index"
 = Join-Path  "data\documents"

# Создаем папки если нет
New-Item -ItemType Directory -Path  -Force | Out-Null
New-Item -ItemType Directory -Path  -Force | Out-Null

Write-Host "
📁 Индекс будет保存在: " -ForegroundColor Yellow
Write-Host "📁 Документы: " -ForegroundColor Yellow

# Проверяем наличие гибридного движка
if (-not (Test-Path )) {
    Write-Host "❌ Гибридный движок не найден!" -ForegroundColor Red
    Write-Host "Сначала выполните создание hybrid_engine" -ForegroundColor Red
    exit 1
}

# Функция для индексации
function Build-Index {
    param([string])
    
    Write-Host "
🔨 Индексация документов из " -ForegroundColor Green
    Set-Location 
    cargo run --release -- build  
}

# Функция для поиска
function Search-Index {
    param([string], [int] = 10)
    
    Write-Host "
🔍 Поиск: " -ForegroundColor Green
    Set-Location 
    cargo run --release -- search  "" 
}

# Функция для добавления документов
function Add-Documents {
    param([string])
    
    Write-Host "
📂 Добавление документов из " -ForegroundColor Green
    Set-Location 
    cargo run --release -- load-dir  
}

# Меню
do {
    Write-Host "
" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "      ГИБРИДНЫЙ ДВИЖОК SVDR+BINVGR" -ForegroundColor White
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "1. Построить индекс из документов" -ForegroundColor Yellow
    Write-Host "2. Поиск" -ForegroundColor Yellow
    Write-Host "3. Добавить документы в существующий индекс" -ForegroundColor Yellow
    Write-Host "4. Показать статистику индекса" -ForegroundColor Yellow
    Write-Host "5. Выход" -ForegroundColor Red
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    
     = Read-Host "
Выберите действие"
    
    switch () {
        "1" {
             = Read-Host "Путь к документам (по умолчанию: )"
            if ([string]::IsNullOrWhiteSpace()) {  =  }
            Build-Index -SourceDir 
        }
        "2" {
             = Read-Host "Поисковый запрос"
             = Read-Host "Количество результатов (по умолчанию: 10)"
            if ([string]::IsNullOrWhiteSpace()) {  = 10 }
            Search-Index -Query  -K ([int])
        }
        "3" {
             = Read-Host "Путь к новым документам"
            Add-Documents -Dir 
        }
        "4" {
            Write-Host "
📊 Статистика индекса" -ForegroundColor Green
            Set-Location 
            cargo run --release -- stats 
        }
    }
} while ( -ne "5")

Write-Host "
👋 До свидания!" -ForegroundColor Cyan
