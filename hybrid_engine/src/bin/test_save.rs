use hybrid_engine::*;

fn main() -> Result<()> {
    println!("🧪 Тест сохранения...");
    
    let mut index = Index::new();
    
    let doc = Document {
        id: 999,
        text: "тестовый документ".to_string(),
        metadata: Metadata {
            path: "test.txt".to_string(),
            modified: 0,
            size: 0,
            source: "test".to_string(),
        },
    };
    
    index.add_document(doc);
    println!("📝 Документ добавлен");
    
    match index.save("./test_save") {
        Ok(_) => println!("✅ Сохранение успешно!"),
        Err(e) => println!("❌ Ошибка: {}", e),
    }
    
    Ok(())
}