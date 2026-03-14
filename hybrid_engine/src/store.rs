//! Хранилище текстов документов

use crate::*;
use fxhash::FxHashMap;

/// Хранилище документов
#[derive(serde::Serialize, serde::Deserialize)]
pub struct DocumentStore {
    pub docs: FxHashMap<u64, Document>,
}

impl DocumentStore {
    pub fn new() -> Self {
        Self {
            docs: FxHashMap::default(),
        }
    }
    
    pub fn insert(&mut self, doc: Document) {
        self.docs.insert(doc.id, doc);
    }
    
    pub fn get(&self, id: u64) -> Option<&Document> {
        self.docs.get(&id)
    }
    
    pub fn len(&self) -> usize {
        self.docs.len()
    }
    
    /// Загрузка документов из директории
    pub fn load_from_dir(&mut self, path: &str) -> Result<usize> {
        use std::fs;
        use walkdir::WalkDir;
        
        let mut count = 0;
        
        for entry in WalkDir::new(path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter(|e| {
                let ext = e.path().extension().unwrap_or_default();
                ext == "txt" || ext == "md" || ext == "rs" || ext == "json"
            })
        {
            let path = entry.path();
            if let Ok(content) = fs::read_to_string(path) {
                let metadata = fs::metadata(path)?;
                let modified = metadata.modified()?
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs();
                
                let doc = Document {
                    id: fxhash::hash64(path.to_string_lossy().as_bytes()),
                    text: content,
                    metadata: Metadata {
                        path: path.to_string_lossy().to_string(),
                        modified,
                        size: metadata.len(),
                        source: "filesystem".to_string(),
                    },
                };
                
                self.insert(doc);
                count += 1;
            }
        }
        
        Ok(count)
    }
}
