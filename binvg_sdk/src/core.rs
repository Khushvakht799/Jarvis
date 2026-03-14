use memmap2::MmapMut;
use std::fs::{File, OpenOptions};
use std::path::Path;
use anyhow::{Result, anyhow};

const MAGIC: [u8; 8] = *b"BINVGR10";
const HEADER_SIZE: u64 = 64;
const NODE_SIZE: u64 = 256;
const EDGE_SIZE: u64 = 32;

#[repr(C, packed)]
#[derive(Debug, Clone, Copy)]
struct Header {
    magic: [u8; 8],
    version: u32,
    node_count: u32,
    edge_count: u32,
    node_capacity: u32,
    edge_capacity: u32,
    embedding_dim: u32,
    node_offset: u64,
    edge_offset: u64,
    embeddings_offset: u64,
    _reserved: [u8; 16],
}

#[repr(C, packed)]
#[derive(Debug, Clone, Copy)]
struct Node {
    id: u32,
    text_len: u32,
    text: [u8; 128],
    intent_len: u32,
    intent: [u8; 32],
    embedding_id: u32,
    edge_start: u32,
    edge_count: u32,
    created: u64,
    _reserved: [u8; 24],
}

#[repr(C, packed)]
#[derive(Debug, Clone, Copy)]
struct Edge {
    source: u32,
    target: u32,
    weight: f32,
    edge_type: u32,
    _reserved: [u8; 16],
}

pub struct BinVGrGraph {
    mmap: MmapMut,
    file: File,
    header: Header,
}

impl BinVGrGraph {
    pub fn create(path: impl AsRef<Path>, node_cap: u32, edge_cap: u32, emb_dim: u32) -> Result<Self> {
        let node_block = node_cap as u64 * NODE_SIZE;
        let edge_block = edge_cap as u64 * EDGE_SIZE;
        let emb_block = node_cap as u64 * emb_dim as u64 * 4;
        let total_size = HEADER_SIZE + node_block + edge_block + emb_block;

        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)?;
        file.set_len(total_size)?;
        
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        
        let header = Header {
            magic: MAGIC,
            version: 1,
            node_count: 0,
            edge_count: 0,
            node_capacity: node_cap,
            edge_capacity: edge_cap,
            embedding_dim: emb_dim,
            node_offset: HEADER_SIZE,
            edge_offset: HEADER_SIZE + node_block,
            embeddings_offset: HEADER_SIZE + node_block + edge_block,
            _reserved: [0; 16],
        };
        
        let mut graph = Self { mmap, file, header };
        graph.write_header()?;
        Ok(graph)
    }

    fn write_header(&mut self) -> Result<()> {
        let header_bytes = unsafe {
            std::slice::from_raw_parts(
                &self.header as *const Header as *const u8,
                std::mem::size_of::<Header>(),
            )
        };
        self.mmap[0..header_bytes.len()].copy_from_slice(header_bytes);
        Ok(())
    }

        pub fn add_node(&mut self, text: &str, intent: &str) -> Result<u32> {
        if self.header.node_count >= self.header.node_capacity {
            anyhow::bail!("Node capacity exceeded");
        }
        
        let id = self.header.node_count;
        let pos = self.header.node_offset + (id as u64 * NODE_SIZE);
        
        let mut node = Node {
            id,
            text_len: 0,
            text: [0; 128],
            intent_len: 0,
            intent: [0; 32],
            embedding_id: id,
            edge_start: self.header.edge_count,
            edge_count: 0,
            created: std::time::UNIX_EPOCH.elapsed()?.as_secs(),
            _reserved: [0; 24],
        };
        
        // Безопасное копирование UTF-8 текста
        let mut text_bytes = 0;
        for (i, c) in text.char_indices() {
            if i + c.len_utf8() > 128 { break; }
            c.encode_utf8(&mut node.text[i..i + c.len_utf8()]);
            text_bytes = i + c.len_utf8();
        }
        node.text_len = text_bytes as u32;
        
        // Безопасное копирование intent
        let mut intent_bytes = 0;
        for (i, c) in intent.char_indices() {
            if i + c.len_utf8() > 32 { break; }
            c.encode_utf8(&mut node.intent[i..i + c.len_utf8()]);
            intent_bytes = i + c.len_utf8();
        }
        node.intent_len = intent_bytes as u32;
        
        let node_ptr = self.mmap[pos as usize..].as_mut_ptr() as *mut Node;
        unsafe { *node_ptr = node };
        
        self.header.node_count += 1;
        self.write_header()?;
        
        Ok(id)
    }

    pub fn add_edge(&mut self, source: u32, target: u32, weight: f32, edge_type: u32) -> Result<()> {
        if self.header.edge_count >= self.header.edge_capacity {
            anyhow::bail!("Edge capacity exceeded");
        }
        
        let id = self.header.edge_count;
        let pos = self.header.edge_offset + (id as u64 * EDGE_SIZE);
        
        let edge = Edge {
            source,
            target,
            weight,
            edge_type,
            _reserved: [0; 16],
        };
        
        let edge_ptr = self.mmap[pos as usize..].as_mut_ptr() as *mut Edge;
        unsafe { *edge_ptr = edge };
        
        self.header.edge_count += 1;
        self.write_header()?;
        
        Ok(())
    }

    pub fn node_count(&self) -> u32 {
        self.header.node_count
    }

    pub fn edge_count(&self) -> u32 {
        self.header.edge_count
    }

    pub fn embedding_dim(&self) -> u32 {
        self.header.embedding_dim
    }

    pub fn get_node_text(&self, id: u32) -> Result<Option<String>> {
        if id >= self.node_count() {
            return Ok(None);
        }
        // TODO: реальное чтение из бинарного файла
        Ok(Some(format!("Узел {}", id)))
    }

    pub fn search(&self, _query_emb: &[f32], _top_k: usize) -> Vec<u32> {
        // Заглушка для поиска
        vec![]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_graph() {
        let path = "test_graph.binvg";
        let result = BinVGrGraph::create(path, 100, 100, 384);
        assert!(result.is_ok());
        let _ = std::fs::remove_file(path);
    }
}

