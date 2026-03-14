//! memory_graph.rs — эпизодическая память
use std::collections::{HashMap, VecDeque};
use chrono::Utc;
use serde::{Serialize, Deserialize};
use std::fs;
use bincode;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExecutionStatus {
    Success,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub status: ExecutionStatus,
    pub output: String,
    pub duration_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryNode {
    pub memory_id: u64,
    pub jvgr_node_id: u64,
    pub verb_id: u32,
    pub object: String,
    pub parameters: Vec<String>,
    pub timestamp: u64,
    pub result: ExecutionResult,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryGraph {
    nodes: HashMap<u64, MemoryNode>,
    order: VecDeque<u64>,
    object_index: HashMap<String, Vec<u64>>,
    max_nodes: usize,
    next_id: u64,
    version: u32,
}

const CURRENT_VERSION: u32 = 1;

impl MemoryGraph {
    pub fn new(max_nodes: usize) -> Self {
        MemoryGraph {
            nodes: HashMap::with_capacity(max_nodes),
            order: VecDeque::with_capacity(max_nodes),
            object_index: HashMap::new(),
            max_nodes,
            next_id: 0,
            version: CURRENT_VERSION,
        }
    }

    pub fn max_nodes(&self) -> usize {
        self.max_nodes
    }

    pub fn add_memory(&mut self, jvgr_node_id: u64, verb_id: u32, object: String, parameters: Vec<String>, result: ExecutionResult) -> u64 {
        let memory_id = self.next_id;
        self.next_id += 1;
        let timestamp = Utc::now().timestamp_millis() as u64;
        let node = MemoryNode {
            memory_id,
            jvgr_node_id,
            verb_id,
            object: object.clone(),
            parameters,
            timestamp,
            result,
        };
        self.nodes.insert(memory_id, node);
        self.order.push_back(memory_id);
        self.object_index.entry(object).or_insert_with(Vec::new).push(memory_id);
        if self.nodes.len() > self.max_nodes {
            self.prune_oldest();
        }
        memory_id
    }

    fn prune_oldest(&mut self) {
        if let Some(oldest_id) = self.order.pop_front() {
            if let Some(node) = self.nodes.remove(&oldest_id) {
                if let Some(vec) = self.object_index.get_mut(&node.object) {
                    vec.retain(|&id| id != oldest_id);
                    if vec.is_empty() {
                        self.object_index.remove(&node.object);
                    }
                }
            }
        }
    }

    pub fn add_edge(&mut self, _from: u64, _to: u64) {}

    pub fn last_memory(&self) -> Option<&MemoryNode> {
        self.order.back().and_then(|id| self.nodes.get(id))
    }

    pub fn find_by_verb(&self, verb_id: u32) -> Vec<&MemoryNode> {
        self.nodes.values().filter(|n| n.verb_id == verb_id).collect()
    }

    pub fn find_by_object(&self, object: &str) -> Vec<&MemoryNode> {
        if let Some(ids) = self.object_index.get(object) {
            ids.iter().filter_map(|id| self.nodes.get(id)).collect()
        } else {
            Vec::new()
        }
    }

    pub fn recent(&self, limit: usize) -> Vec<&MemoryNode> {
        self.order.iter().rev().take(limit).filter_map(|id| self.nodes.get(id)).collect()
    }

    pub fn save_to_file(&self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        let data = bincode::serialize(self)?;
        fs::write(path, data)?;
        Ok(())
    }

    pub fn load_from_file(path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let data = fs::read(path)?;
        let graph: MemoryGraph = bincode::deserialize(&data)?;
        if graph.version != CURRENT_VERSION {
            return Err(format!("Version mismatch: expected {}, got {}", CURRENT_VERSION, graph.version).into());
        }
        Ok(graph)
    }

    pub fn size(&self) -> usize {
        self.nodes.len()
    }

    pub fn all_nodes(&self) -> Vec<&MemoryNode> {
        self.nodes.values().collect()
    }
}
