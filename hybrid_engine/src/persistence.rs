//! Персистентность индекса

use crate::*;
use std::fs;
use std::path::Path;

/// Состояние индекса
#[derive(serde::Serialize, serde::Deserialize)]
pub struct IndexMeta {
    pub version: String,
    pub created: u64,
    pub num_docs: usize,
    pub last_modified: u64,
}

/// Основной индекс
pub struct Index {
    pub sparse: SparseIndex,
    pub graph: BinaryGraph,
    pub store: DocumentStore,
    pub meta: IndexMeta,
}

impl Index {
    pub fn new() -> Self {
        Self {
            sparse: SparseIndex::new(),
            graph: BinaryGraph::new(),
            store: DocumentStore::new(),
            meta: IndexMeta {
                version: env!("CARGO_PKG_VERSION").to_string(),
                created: chrono::Utc::now().timestamp() as u64,
                num_docs: 0,
                last_modified: chrono::Utc::now().timestamp() as u64,
            },
        }
    }
    
    pub fn add_document(&mut self, doc: Document) {
        let id = doc.id;
        let sparse = SparseVector::from_text(&doc.text);
        let binary = BinaryVector::from_text(&doc.text);
        
        let node = Node {
            id,
            sparse: sparse.clone(),
            binary,
            edges: Vec::new(),
        };
        
        self.sparse.insert(id, sparse);
        self.graph.insert(node);
        self.store.insert(doc);
        self.meta.num_docs += 1;
        self.meta.last_modified = chrono::Utc::now().timestamp() as u64;
    }
    
    pub fn search(&self, query: &str, k: usize) -> Vec<SearchResult> {
        let sparse_query = SparseVector::from_text(query);
        let binary_query = BinaryVector::from_text(query);
        
        let candidates = self.sparse.search(&sparse_query, k * 10);
        
        let mut results = Vec::new();
        for (id, sparse_score) in candidates {
            if let Some(node) = self.graph.get(id) {
                let binary_score = node.binary.similarity(&binary_query);
                let final_score = 0.7 * sparse_score + 0.3 * binary_score;
                
                if let Some(doc) = self.store.get(id) {
                    results.push(SearchResult {
                        id,
                        score: final_score,
                        text: doc.text.clone(),
                        metadata: doc.metadata.clone(),
                    });
                }
            }
        }
        
        results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
        results.truncate(k);
        results
    }
    
    pub fn save(&self, path: &str) -> Result<()> {
        fs::create_dir_all(path)?;
        
        let meta_path = Path::new(path).join("meta.json");
        fs::write(meta_path, serde_json::to_string_pretty(&self.meta)?)?;
        
        let sparse_path = Path::new(path).join("sparse.idx");
        let sparse_data = bincode::serialize(&self.sparse.vectors)?;
        fs::write(sparse_path, sparse_data)?;
        
        let graph_path = Path::new(path).join("graph.idx");
        let graph_data = bincode::serialize(&self.graph.nodes)?;
        fs::write(graph_path, graph_data)?;
        
        let docs_path = Path::new(path).join("docs.bin");
        let docs_data = bincode::serialize(&self.store.docs)?;
        fs::write(docs_path, docs_data)?;
        
        Ok(())
    }
    
    pub fn load(path: &str) -> Result<Self> {
        let meta_path = Path::new(path).join("meta.json");
        let meta: IndexMeta = serde_json::from_str(&fs::read_to_string(meta_path)?)?;
        
        let sparse_path = Path::new(path).join("sparse.idx");
        let sparse_data = fs::read(sparse_path)?;
        let sparse_vectors: FxHashMap<u64, SparseVector> = bincode::deserialize(&sparse_data)?;
        
        let mut sparse = SparseIndex::new();
        for (id, vec) in sparse_vectors {
            sparse.insert(id, vec);
        }
        
        let graph_path = Path::new(path).join("graph.idx");
        let graph_data = fs::read(graph_path)?;
        let nodes: FxHashMap<u64, Node> = bincode::deserialize(&graph_data)?;
        
        let mut graph = BinaryGraph::new();
        for (_, node) in nodes {
            graph.insert(node);
        }
        
        let docs_path = Path::new(path).join("docs.bin");
        let docs_data = fs::read(docs_path)?;
        let docs: FxHashMap<u64, Document> = bincode::deserialize(&docs_data)?;
        
        let mut store = DocumentStore::new();
        for (_, doc) in docs {
            store.insert(doc);
        }
        
        Ok(Self {
            sparse,
            graph,
            store,
            meta,
        })
    }
}
