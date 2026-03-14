//! command_graph.rs — устаревший модуль, оставлен для совместимости
#![allow(dead_code)]
use crate::jvgr::JVGRNode;

#[deprecated(note = "используйте jvgr::JVGRNode")]
pub type Command = JVGRNode;

pub fn new_command(id: u64, verb_id: u32, object_id: u32, params: Vec<String>) -> JVGRNode {
    JVGRNode {
        id,
        verb_id,
        object_id,
        parameters: params,
        timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        context_vector: Vec::new(),
    }
}
