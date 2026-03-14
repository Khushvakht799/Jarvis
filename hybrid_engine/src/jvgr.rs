//! jvgr.rs — Jarvis VectorGraph Representation
//! Добавлено поле id для связи с памятью

#[derive(Debug, Clone)]
pub struct JVGRNode {
    pub id: u64,
    pub verb_id: u32,
    pub object_id: u32,
    pub parameters: Vec<String>,
    pub timestamp: u64,
    pub context_vector: Vec<u64>,
}

#[derive(Debug)]
pub struct JVGRGraph {
    pub nodes: Vec<JVGRNode>,
    pub edges: Vec<(usize, usize)>,
    pub execution_pointer: usize,
    next_id: u64,
}

impl JVGRGraph {
    pub fn new() -> Self {
        JVGRGraph {
            nodes: Vec::new(),
            edges: Vec::new(),
            execution_pointer: 0,
            next_id: 0,
        }
    }

    pub fn add_node(&mut self, verb_id: u32, object_id: u32, parameters: Vec<String>) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        let node = JVGRNode {
            id,
            verb_id,
            object_id,
            parameters,
            timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
            context_vector: Vec::new(),
        };
        self.nodes.push(node);
        id
    }

    pub fn add_edge(&mut self, from: usize, to: usize) {
        self.edges.push((from, to));
    }

    pub fn current_node(&self) -> Option<&JVGRNode> {
        self.nodes.get(self.execution_pointer)
    }

    pub fn advance(&mut self) {
        if self.execution_pointer + 1 < self.nodes.len() {
            self.execution_pointer += 1;
        }
    }

    pub fn reset(&mut self) {
        self.execution_pointer = 0;
    }
}