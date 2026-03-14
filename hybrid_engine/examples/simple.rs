//! Пример использования гибридного движка

use hybrid_engine::*;

fn main() -> Result<()> {
    println!("🚀 SVDR+BinVGr Hybrid Engine Example");
    
    // Создаем новый индекс
    let mut index = Index::new();
    
    // Добавляем несколько документов
    let docs = vec![
        Document {
            id: 1,
            text: "графовая память для искусственного интеллекта".to_string(),
            metadata: Metadata {
                path: "doc1.txt".to_string(),
                modified: 0,
                size: 0,
                source: "example".to_string(),
            },
        },
        Document {
            id: 2,
            text: "бинарные эмбеддинги и разреженные вектора".to_string(),
            metadata: Metadata {
                path: "doc2.txt".to_string(),
                modified: 0,
                size: 0,
                source: "example".to_string(),
            },
        },
        Document {
            id: 3,
            text: "поиск по документам с использованием гибридного подхода".to_string(),
            metadata: Metadata {
                path: "doc3.txt".to_string(),
                modified: 0,
                size: 0,
                source: "example".to_string(),
            },
        },
    ];
    
    for doc in docs {
        index.add_document(doc);
    }
    
    println!("✅ Добавлено {} документов", index.meta.num_docs);
    
    // Поиск
    let query = "графовый поиск";
    println!("\n🔍 Поиск: '{}'", query);
    
    let results = index.search(query, 5);
    
    for (i, result) in results.iter().enumerate() {
        println!("{}. {} (score: {:.3})", i + 1, result.text, result.score);
    }
    
    // Сохраняем индекс
    index.save("./test_index")?;
    println!("\n💾 Индекс сохранен в ./test_index");
    
    Ok(())
}
