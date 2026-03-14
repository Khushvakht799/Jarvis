//! Ядро гибридного поиска SVDR + BinVGr
// В начало файла добавь:
use crate::nlp_minimal::process_text;
use fxhash::FxHashMap;

/// SVDR: разреженный вектор
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SparseVector {
    pub indices: Vec<u32>,
    pub weights: Vec<f32>,
    norm: f32,
}

impl SparseVector {
    pub fn from_text(text: &str) -> Self {
        let words = process_text(text);
    
        let mut freq = FxHashMap::default();
        for word in words {
            let hash = fxhash::hash32(&word) as u32;
            *freq.entry(hash).or_insert(0) += 1;
        }
    
        let mut indices = Vec::with_capacity(freq.len());
        let mut weights = Vec::with_capacity(freq.len());
    
        for (token, count) in freq {
            indices.push(token);
            weights.push((count as f32).sqrt());
        }
    
        let norm = weights.iter().map(|w| w * w).sum::<f32>().sqrt();
        if norm > 0.0 {
            for w in &mut weights {
                *w /= norm;
            }
        }
    
        Self { indices, weights, norm: 0.0 }
    }
    
    pub fn dot(&self, other: &Self) -> f32 {
        let mut i = 0;
        let mut j = 0;
        let mut result = 0.0;
        
        while i < self.indices.len() && j < other.indices.len() {
            match self.indices[i].cmp(&other.indices[j]) {
                std::cmp::Ordering::Equal => {
                    result += self.weights[i] * other.weights[j];
                    i += 1;
                    j += 1;
                }
                std::cmp::Ordering::Less => i += 1,
                std::cmp::Ordering::Greater => j += 1,
            }
        }
        result
    }
}

/// BinVGr: бинарный вектор (64 бита)
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BinaryVector {
    bits: u64,
}

impl BinaryVector {
    pub fn from_text(text: &str) -> Self {
        let mut bits = 0u64;
        let words: Vec<&str> = text.split_whitespace().collect();
        
        for (i, word) in words.iter().enumerate().take(64) {
            let hash = fxhash::hash32(word) as u64;
            if hash & 1 == 1 {
                bits |= 1u64 << (i % 64);
            }
        }
        
        Self { bits }
    }
    
    pub fn hamming_distance(&self, other: &Self) -> u32 {
        (self.bits ^ other.bits).count_ones()
    }
    
    pub fn similarity(&self, other: &Self) -> f32 {
        1.0 - (self.hamming_distance(other) as f32 / 64.0)
    }
}

/// Узел графа
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Node {
    pub id: u64,
    pub sparse: SparseVector,
    pub binary: BinaryVector,
    pub edges: Vec<u64>,
}

/// SVDR индекс
#[derive(serde::Serialize, serde::Deserialize)]
pub struct SparseIndex {
    inverted: FxHashMap<u32, Vec<u64>>,
    pub vectors: FxHashMap<u64, SparseVector>,
}

impl SparseIndex {
    pub fn new() -> Self {
        Self {
            inverted: FxHashMap::default(),
            vectors: FxHashMap::default(),
        }
    }
    
    pub fn insert(&mut self, id: u64, vec: SparseVector) {
        for &idx in &vec.indices {
            self.inverted.entry(idx)
                .or_insert_with(Vec::new)
                .push(id);
        }
        self.vectors.insert(id, vec);
    }
    
    pub fn search(&self, query: &SparseVector, k: usize) -> Vec<(u64, f32)> {
        let mut scores = FxHashMap::default();
        
        for &token in &query.indices {
            if let Some(docs) = self.inverted.get(&token) {
                for &doc_id in docs {
                    *scores.entry(doc_id).or_insert(0.0) += 1.0;
                }
            }
        }
        
        let mut candidates: Vec<_> = scores.into_iter().collect();
        candidates.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        candidates.truncate(k);
        
        let mut results = Vec::new();
        for (id, _) in candidates {
            if let Some(vec) = self.vectors.get(&id) {
                let score = query.dot(vec);
                results.push((id, score));
            }
        }
        
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        results
    }
}

/// BinVGr граф
#[derive(serde::Serialize, serde::Deserialize)]
pub struct BinaryGraph {
    pub nodes: FxHashMap<u64, Node>,
}

impl BinaryGraph {
    pub fn new() -> Self {
        Self {
            nodes: FxHashMap::default(),
        }
    }
    
    pub fn insert(&mut self, node: Node) {
        self.nodes.insert(node.id, node);
    }
    
    pub fn search(&self, query: &BinaryVector, k: usize) -> Vec<(u64, f32)> {
        let mut results: Vec<_> = self.nodes
            .iter()
            .map(|(&id, node)| (id, node.binary.similarity(query)))
            .collect();
        
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        results.truncate(k);
        results
    }
    
    pub fn get(&self, id: u64) -> Option<&Node> {
        self.nodes.get(&id)
    }
}

