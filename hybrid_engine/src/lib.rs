//! SVDR + BinVGr гибридный поисковый движок + JVGR модули + MemoryGraph

mod core;
mod store;
mod persistence;
mod builder;
mod error;
pub mod nlp_minimal;
pub mod verb_engine;
pub mod object_detector;
pub mod param_extractor;
pub mod command_graph; // устаревший, но оставлен
pub mod jvgr;
pub mod executor;
pub mod memory_graph;

pub use core::*;
pub use store::*;
pub use persistence::*;
pub use builder::*;
pub use error::*;
pub use nlp_minimal::*;
pub use verb_engine::*;
pub use object_detector::*;
pub use param_extractor::*;
pub use jvgr::*;
pub use executor::*;
pub use memory_graph::*;

use fxhash::FxHashMap;

/// Метаданные документа
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Metadata {
    pub path: String,
    pub modified: u64,
    pub size: u64,
    pub source: String,
}

/// Документ
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Document {
    pub id: u64,
    pub text: String,
    pub metadata: Metadata,
}

/// Результат поиска
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub id: u64,
    pub score: f32,
    pub text: String,
    pub metadata: Metadata,
}

/// Тип результата
pub type Result<T> = std::result::Result<T, Error>;
