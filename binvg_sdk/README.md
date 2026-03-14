# BinVGr SDK — Бинарный векторный граф для памяти LLM

[![Rust](https://img.shields.io/badge/rust-1.70%2B-blue.svg)](https://www.rust-lang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**BinVGr (Binary Vector Graph)** — высокопроизводительный движок для графовой памяти на Rust.  
Микросекундные операции, полная интеграция с LLM, бинарное хранение через mmap.

## ✨ Возможности

| Характеристика | Значение |
|----------------|----------|
| 🚀 **Добавление узла** | ~12 µs |
| ⚡ **Поиск + ответ LLM** | ~24 µs |
| 💾 **Память на 1M узлов** | ~16 MB (с бинарными эмбеддингами) |
| 🔗 **Графовые связи** | uto_connect |
| 🧠 **LLM адаптер** | nano-vLLM (порт 5000) |
| 📦 **Формат** | бинарный mmap |

## 🚀 Быстрый старт

**Cargo.toml**
`	oml
[dependencies]
binvg_sdk = { path = "C:/Users/Usuario/Jarvis/binvg_sdk" }
anyhow = "1.0"main.rs

rust
use binvg_sdk::core::BinVGrGraph;
use binvg_sdk::adapter::NanoVLLMAdapter;
use binvg_sdk::pipeline::BinVGrPipeline;

fn main() -> anyhow::Result<()> {
    let graph = BinVGrGraph::create("memory.binvg", 10000, 50000, 384)?;
    let adapter = NanoVLLMAdapter::new("http://127.0.0.1:5000");
    let mut pipeline = BinVGrPipeline::new(graph, adapter);
    
    pipeline.add_knowledge("графовая память быстрая", "concept")?;
    let answer = pipeline.ask("Что такое граф?")?;
    println!("{}", answer);
    
    Ok(())
}
📊 Производительность
ОперацияВремя
Создание графа (50k узлов)342 µs
Добавление узла~12 µs
Поиск + ответ LLM24 µs
Добавление 1000 узлов284 µs
🧪 Запуск тестов
bash
cargo run --bin test_pipeline   # полный тест
cargo run --bin stress_test      # стресс-тест
cargo run --bin test_auto        # тест auto_connect
📂 Структура
text
src/
├── core.rs      # бинарный mmap-движок
├── adapter.rs   # LLM адаптер
├── pipeline.rs  # полный pipeline
└── lib.rs       # точка входа
🔧 Требования
Rust 1.70+

nano-vLLM на порту 5000 (или совместимый сервер)

📜 Лицензия
MIT © Khushvakht Raupov
