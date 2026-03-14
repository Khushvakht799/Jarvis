use binvg_sdk::core::BinVGrGraph;
use binvg_sdk::adapter::MockAdapter;
use binvg_sdk::pipeline::BinVGrPipeline;

fn main() -> anyhow::Result<()> {
    println!("🧪 Тест auto_connect");
    
    // Создаём граф
    let graph = BinVGrGraph::create("test_auto.binvg", 1000, 1000, 384)?;
    let adapter = MockAdapter::new();
    let mut pipeline = BinVGrPipeline::new(graph, adapter);
    
    // Добавляем два узла
    let id1 = pipeline.add_knowledge("первый узел", "test")?;
    let id2 = pipeline.add_knowledge("второй узел", "test")?;
    
    println!("📦 Узлы: {} и {}", id1, id2);
    
    // Связываем их
    pipeline.auto_connect(id1, id2)?;
    println!("🔗 Связь создана");
    
    // Проверяем статистику
    let (nodes, edges) = pipeline.stats();
    println!("📊 Статистика: {} узлов, {} связей", nodes, edges);
    
    Ok(())
}
