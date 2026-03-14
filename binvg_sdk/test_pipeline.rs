use binvg_sdk::core::BinVGrGraph;
use binvg_sdk::adapter::NanoVLLMAdapter;
use binvg_sdk::pipeline::BinVGrPipeline;
use std::time::Instant;
use anyhow::Result;

fn safe_truncate(s: &str, max_bytes: usize) -> &str {
    if s.len() <= max_bytes { return s; }
    let mut idx = max_bytes;
    while idx > 0 && !s.is_char_boundary(idx) { idx -= 1; }
    &s[..idx]
}

fn main() -> Result<()> {
    println!("╔══════════════════════════════════════════╗");
    println!("║    ТЕСТ BINVGR SDK С NANO-VLLM         ║");
    println!("╚══════════════════════════════════════════╝");
    
    // 1. Создаём граф
    println!("\n📁 Создание бинарного графа...");
    let start = Instant::now();
    let graph = BinVGrGraph::create("test_pipeline.binvg", 10000, 50000, 384)?;
    println!("   ✅ Граф создан за {:?}", start.elapsed());
    
    // 2. Подключаем адаптер
    println!("\n🔌 Подключение к nano-vLLM...");
    let adapter = NanoVLLMAdapter::new("http://127.0.0.1:5000");
    let mut pipeline = BinVGrPipeline::new(graph, adapter);
    
    // 3. Добавляем знания
    println!("\n📚 Добавление знаний в граф...");
    let knowledge = vec![
        ("графовая память хранит узлы и связи", "concept"),
        ("эмбеддинги превращают текст в векторы", "concept"),
        ("нейросети работают на GPU", "fact"),
    ];
    
    for (text, intent) in knowledge {
        let start = Instant::now();
        let id = pipeline.add_knowledge(text, intent)?;
        let preview = safe_truncate(text, 30);
        println!("   ✅ Добавлен узел {}: {}... [{:?}]", id, preview, start.elapsed());
    }
    
    // 4. Статистика
    let (nodes, edges) = pipeline.stats();
    println!("\n📊 Статистика графа: {} узлов, {} связей", nodes, edges);
    
    // 5. Тестовый вопрос
    let question = "Что такое графовая память?";
    println!("\n🧪 ТЕСТОВЫЙ ЗАПРОС");
    println!("📝 Вопрос: {}", question);
    
    let start = Instant::now();
    match pipeline.ask(question) {
        Ok(answer) => {
            let duration = start.elapsed();
            println!("   ⏱️  Время: {:?}", duration);
            
            let preview = safe_truncate(&answer, 100);
            println!("   💬 Ответ: {}", preview);
            
            if duration.as_millis() < 500 {
                println!("   ✅ Цель <500ms достигнута!");
            }
        }
        Err(e) => println!("   ❌ Ошибка: {}", e),
    }

    // 6. Тест auto_connect
    println!("\n🔗 ТЕСТ AUTO_CONNECT");
    let id1 = pipeline.add_knowledge("тестовый узел 1", "test")?;
    let id2 = pipeline.add_knowledge("тестовый узел 2", "test")?;
    pipeline.auto_connect(id1, id2)?;
    println!("✅ auto_connect протестирован");

    // 7. Финальная статистика
    let (nodes, edges) = pipeline.stats();
    println!("\n📊 Финальная статистика: {} узлов, {} связей", nodes, edges);
    
    println!("\n✅ ТЕСТ ЗАВЕРШЁН");
    Ok(())
}
