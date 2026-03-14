#!powershell
Write-Host "🔨 Сборка гибридного движка SVDR+BinVGr" -ForegroundColor Cyan

Set-Location hybrid_engine

# Сборка
Write-Host "
📦 Компиляция..." -ForegroundColor Yellow
cargo build --release

if (0 -ne 0) {
    Write-Host "❌ Ошибка компиляции" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Компиляция успешна" -ForegroundColor Green

# Запуск примера
Write-Host "
🚀 Запуск примера..." -ForegroundColor Cyan
cargo run --example simple

# Индексация тестовых документов
Write-Host "
📚 Индексация тестовых документов..." -ForegroundColor Cyan
cargo run -- build ./test_docs ./my_index

# Поиск
Write-Host "
🔍 Поиск 'бинарные вектора'..." -ForegroundColor Cyan
cargo run -- search ./my_index "бинарные вектора" 3

Write-Host "
✨ Готово!" -ForegroundColor Green
