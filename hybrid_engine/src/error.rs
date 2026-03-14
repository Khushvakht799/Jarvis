//! Обработка ошибок

use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] bincode::Error),
    
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("Document not found: {0}")]
    DocumentNotFound(u64),
    
    #[error("Index corrupted: {0}")]
    IndexCorrupted(String),
    
    #[error("Invalid path: {0}")]
    InvalidPath(String),
}
