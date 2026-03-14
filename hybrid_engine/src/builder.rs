//! Пакетная индексация миллионов документов

use crate::*;
// use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use tracing::info;
use std::time::Instant;
use std::fs;

/// Статистика индексации
#[derive(Debug)]
pub struct BuildStats {
    pub total_docs: usize,
    pub time_secs: f64,
    pub docs_per_sec: f64,
}

/// Построитель индекса
pub struct IndexBuilder;

impl IndexBuilder {
    pub fn build_index(
        input_dir: &str,
        _batch_size: usize,
        output_path: &str,
    ) -> Result<BuildStats> {
        let start = Instant::now();
        
        info!("Начало индексации директории: {}", input_dir);
        
        let index = Arc::new(Mutex::new(Index::new()));
        
        // Получаем список файлов
        let files: Vec<_> = walkdir::WalkDir::new(input_dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .map(|e| e.path().to_string_lossy().to_string())
            .collect();
        
        info!("Найдено {} файлов для индексации", files.len());
        
        if files.is_empty() {
            return Ok(BuildStats {
                total_docs: 0,
                time_secs: 0.0,
                docs_per_sec: 0.0,
            });
        }
        
        // Последовательная обработка для надежности
        for (i, path) in files.iter().enumerate() {
            info!("Обработка файла {}/{}: {}", i+1, files.len(), path);
            
            match fs::read_to_string(path) {
                Ok(content) => {
                    let metadata = fs::metadata(path).ok();
                    
                    let modified = metadata
                        .as_ref()
                        .and_then(|m| m.modified().ok())
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0);
                    
                    let size = metadata
                        .as_ref()
                        .map(|m| m.len())
                        .unwrap_or(0);
                    
                    let doc = Document {
                        id: fxhash::hash64(path.as_bytes()),
                        text: content,
                        metadata: Metadata {
                            path: path.clone(),
                            modified,
                            size,
                            source: "filesystem".to_string(),
                        },
                    };
                    
                    let mut global = index.lock().unwrap();
                    global.add_document(doc);
                    info!("  ✅ Добавлен документ ID: {}", fxhash::hash64(path.as_bytes()));
                }
                Err(e) => {
                    info!("  ❌ Ошибка чтения {}: {}", path, e);
                }
            }
        }
        
        info!(">>> ПЕРЕД СОХРАНЕНИЕМ: получаем доступ к индексу...");
        
        // Получаем статистику в отдельном блоке, чтобы сразу отпустить Mutex
        let total_docs = {
            let locked = index.lock().unwrap();
            locked.meta.num_docs
        };
        
        info!(">>> Статистика получена: {} документов", total_docs);
        
        let elapsed = start.elapsed();
        let stats = BuildStats {
            total_docs,
            time_secs: elapsed.as_secs_f64(),
            docs_per_sec: total_docs as f64 / elapsed.as_secs_f64(),
        };
        
        info!("Индексация завершена за {:.2?}", elapsed);
        info!("Документов: {}, скорость: {:.0} docs/sec", 
              stats.total_docs, stats.docs_per_sec);
        
        info!(">>> ШАГ 1: Начинаем сохранение...");
        info!("Сохраняем индекс в {}", output_path);
        
        info!(">>> ШАГ 2: Вызываем save()...");
        
        // Сохраняем в отдельном блоке
        let save_result = {
            let locked = index.lock().unwrap();
            locked.save(output_path)
        };
        
        info!(">>> ШАГ 3: save() вернул результат");
        match save_result {
            Ok(_) => info!("✅ Индекс сохранён в {}", output_path),
            Err(e) => info!("❌ Ошибка сохранения: {}", e),
        }
        
        info!(">>> ШАГ 4: Сохранение завершено, возвращаем результат");
        
        Ok(stats)
    }
}

