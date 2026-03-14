//! CLI интерфейс для гибридного движка

use hybrid_engine::*;
use std::env;
use tracing_subscriber;

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    
    let args: Vec<String> = env::args().collect();
    
    // Проверяем количество аргументов
    if args.len() < 2 {
        println!("Использование:");
        println!("  hybrid_cli build <input_dir> <output_path>   - построить индекс");
        println!("  hybrid_cli search <index_path> <query> [k]   - поиск");
        println!("  hybrid_cli stats <index_path>                - статистика");
        return Ok(());
    }
    
    match args[1].as_str() {
        "build" => {
            if args.len() < 4 {
                println!("Ошибка: нужно указать папку с документами и путь для индекса");
                println!("Пример: hybrid_cli build ./test_docs ./my_index");
                return Ok(());
            }
            let input_dir = &args[2];
            let output_path = &args[3];
            
            println!("🔨 Индексация документов из: {}", input_dir);
            let stats = IndexBuilder::build_index(input_dir, 1000, output_path)?;
            
            println!("✅ Индексация завершена:");
            println!("   Документов: {}", stats.total_docs);
            println!("   Время: {:.2} сек", stats.time_secs);
        }
        
        "search" => {
            if args.len() < 4 {
                println!("Ошибка: нужно указать путь к индексу и поисковый запрос");
                return Ok(());
            }
            let index_path = &args[2];
            let query = &args[3];
            let k = if args.len() > 4 { args[4].parse().unwrap_or(10) } else { 10 };
            
            let index = Index::load(index_path)?;
            let results = index.search(query, k);
            
            println!("🔍 Найдено {} результатов:", results.len());
            for (i, result) in results.iter().enumerate() {
                println!("\n{}. [{}] score: {:.3}", i+1, result.id, result.score);
                println!("   📁 {}", result.metadata.path);
                let preview = if result.text.len() > 100 {
                    let mut chars = result.text.chars();
                    let preview: String = chars.by_ref().take(100).collect();
                    preview + "..."
                } else {
                     result.text.clone()
                };
                println!("   📄 {}", preview);
            }
        }
        
        "stats" => {
            if args.len() < 3 {
                println!("Ошибка: нужно указать путь к индексу");
                return Ok(());
            }
            let index_path = &args[2];
            let index = Index::load(index_path)?;
            
            println!("📊 Статистика индекса:");
            println!("   Версия: {}", index.meta.version);
            println!("   Документов: {}", index.meta.num_docs);
        }
        
        _ => {
            println!("Неизвестная команда: {}", args[1]);
        }
    }
    
    Ok(())
}
