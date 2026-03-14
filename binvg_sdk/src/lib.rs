//! BinVGr SDK v1.0
//! Бинарный векторный граф для памяти LLM

pub mod core;
pub mod adapter;
pub mod pipeline;

pub use core::BinVGrGraph;
pub use adapter::{LLMAdapter, NanoVLLMAdapter, MockAdapter};
pub use pipeline::BinVGrPipeline;
pub use anyhow::Result;
