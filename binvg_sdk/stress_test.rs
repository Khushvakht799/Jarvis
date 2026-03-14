use binvg_sdk::core::BinVGrGraph;
use binvg_sdk::adapter::NanoVLLMAdapter;
use binvg_sdk::pipeline::BinVGrPipeline;
use std::time::Instant;
use anyhow::Result;
use rayon::prelude::*;

fn safe_truncate(s: &str, max_bytes: usize) -> &str {
    if s.len() <= max_bytes { return s; }
    let mut idx = max_bytes;
    while idx > 0 && !s.is_char_boundary(idx) { idx -= 1; }
    &s[..idx]
}

fn main() -> Result<()> {
    println!("╔══════════════════════════════════════════╗");
    println!("║    СТРЕСС-ТЕСТ BINVGR SDK              ║");
    println!("╚══════════════════════════════════════════╝");
    
    // 1. Создаём граф
    println!("\n📁 Создание графа на 50,000 узлов...");
    let start = Instant::now();
    let graph = BinVGrGraph::create("stress.binvg", 50000, 100000, 384)?;
    println!("   ✅ Граф создан за {:?}", start.elapsed());
    
    // 2. Подключаем адаптер
    let adapter = NanoVLLMAdapter::new("http://127.0.0.1:5000");
    let mut pipeline = BinVGrPipeline::new(graph, adapter);
    
    // 3. Массовое добавление знаний
    println!("\n📚 Массовое добавление 1000 узлов...");
    let start = Instant::now();
    for i in 0..1000 {
        let text = format!("Знание номер {} - это тестовый узел для проверки производительности", i);
        pipeline.add_knowledge(&text, "test")?;
        if (i+1) % 100 == 0 {
            print!("\r   Прогресс: {}%", ((i+1)*100/1000));
        }
    }
    println!("\n   ✅ Добавлено 1000 узлов за {:?}", start.elapsed());
    
    // 4. Статистика
    let (nodes, edges) = pipeline.stats();
    println!("\n📊 Статистика графа: {} узлов, {} связей", nodes, edges);
    
    // 5. Пакетные запросы
    println!("\n🧪 ТЕСТ ПАКЕТНЫХ ЗАПРОСОВ");
    let questions = vec![
        "Что такое графовая память?",
        "Как работают эмбеддинги?",
        "Где выполняются нейросети?",
        "Что такое Rust?",
        "Как работает память?",
    ];
    
    // Последовательные запросы
    println!("\n📊 Последовательные запросы:");
    let start = Instant::now();
    for (i, q) in questions.iter().enumerate() {
        let q_start = Instant::now();
        match pipeline.ask(q) {
            Ok(answer) => {
                println!("   {}. {:?} - {}", i+1, q_start.elapsed(), safe_truncate(&answer, 50));
            }
            Err(e) => println!("   ❌ Ошибка: {}", e),
        }
    }
    println!("   Всего: {:?}", start.elapsed());
    
    // 6. Информация о файле
    println!("\n💾 Информация о бинарном файле:");
    let file_size = std::fs::metadata("stress.binvg")?.len();
    println!("   Размер: {} bytes ({:.2} MB)", file_size, file_size as f64 / (1024.0 * 1024.0));
    
    println!("\n✅ СТРЕСС-ТЕСТ ЗАВЕРШЁН");
    Ok(())
}
