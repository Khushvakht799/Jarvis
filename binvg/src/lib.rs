use memmap2::MmapMut;
use std::fs::{OpenOptions, File};
use std::path::Path;
use std::io::{Write, Read};
use byteorder::{LittleEndian, WriteBytesExt, ReadBytesExt};
use anyhow::{Result};

// Заголовок файла (64 байта)
#[repr(C, packed)]
struct Header {
    magic: [u8; 8],      // b"BINVGR10"
    version: u32,
    node_count: u32,
    edge_count: u32,
    node_capacity: u32,
    edge_capacity: u32,
    embedding_dim: u32,
    node_offset: u64,
    edge_offset: u64,
    _reserved: [u8; 16],
}

impl Header {
    const MAGIC: [u8; 8] = *b"BINVGR10";
    const NODE_SIZE: u64 = 4 + 4 + 64 + 4 + 512; // id + intent_len + intent + text_len + embedding
    const EDGE_SIZE: u64 = 4 + 4 + 4; // from + to + weight (f32)
}

// Узел в памяти
#[derive(Debug)]
pub struct Node {
    pub id: u32,
    pub intent: String,
    pub text: String,
    pub embedding: Vec<f32>,
}

// Связь
#[derive(Debug)]
pub struct Edge {
    pub from: u32,
    pub to: u32,
    pub weight: f32,
}

// BinVGr хранилище
pub struct BinVGr {
    mmap: MmapMut,
    file: File,
    header: Header,
    node_capacity: u32,
    edge_capacity: u32,
    embedding_dim: u32,
    node_offset: u64,
    edge_offset: u64,
}

impl BinVGr {
    // Создать новый файл
    pub fn create(path: &Path, node_capacity: u32, edge_capacity: u32, embedding_dim: u32) -> Result<Self> {
        let file_size = 64 + (node_capacity as u64 * Header::NODE_SIZE) + (edge_capacity as u64 * Header::EDGE_SIZE);
        
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)?;
        file.set_len(file_size)?;
        
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        
        let mut this = BinVGr {
            mmap,
            file,
            header: Header {
                magic: Header::MAGIC,
                version: 1,
                node_count: 0,
                edge_count: 0,
                node_capacity,
                edge_capacity,
                embedding_dim,
                node_offset: 64,
                edge_offset: 64 + (node_capacity as u64 * Header::NODE_SIZE),
                _reserved: [0; 16],
            },
            node_capacity,
            edge_capacity,
            embedding_dim,
            node_offset: 64,
            edge_offset: 64 + (node_capacity as u64 * Header::NODE_SIZE),
        };
        
        this.write_header()?;
        Ok(this)
    }
    
    // Открыть существующий
    pub fn open(path: &Path) -> Result<Self> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(path)?;
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        
        let mut this = BinVGr {
            mmap,
            file,
            header: unsafe { std::mem::zeroed() },
            node_capacity: 0,
            edge_capacity: 0,
            embedding_dim: 0,
            node_offset: 0,
            edge_offset: 0,
        };
        
        this.read_header()?;
        Ok(this)
    }
    
    fn write_header(&mut self) -> Result<()> {
        let mut cursor = std::io::Cursor::new(&mut self.mmap[..]);
        cursor.write_all(&Header::MAGIC)?;
        cursor.write_u32::<LittleEndian>(self.header.version)?;
        cursor.write_u32::<LittleEndian>(self.header.node_count)?;
        cursor.write_u32::<LittleEndian>(self.header.edge_count)?;
        cursor.write_u32::<LittleEndian>(self.header.node_capacity)?;
        cursor.write_u32::<LittleEndian>(self.header.edge_capacity)?;
        cursor.write_u32::<LittleEndian>(self.header.embedding_dim)?;
        cursor.write_u64::<LittleEndian>(self.header.node_offset)?;
        cursor.write_u64::<LittleEndian>(self.header.edge_offset)?;
        cursor.write_all(&[0; 16])?;
        Ok(())
    }
    
    fn read_header(&mut self) -> Result<()> {
        let mut cursor = std::io::Cursor::new(&self.mmap[..]);
        let mut magic = [0; 8];
        cursor.read_exact(&mut magic)?;
        if magic != Header::MAGIC {
            anyhow::bail!("Invalid magic");
        }
        self.header.version = cursor.read_u32::<LittleEndian>()?;
        self.header.node_count = cursor.read_u32::<LittleEndian>()?;
        self.header.edge_count = cursor.read_u32::<LittleEndian>()?;
        self.header.node_capacity = cursor.read_u32::<LittleEndian>()?;
        self.header.edge_capacity = cursor.read_u32::<LittleEndian>()?;
        self.header.embedding_dim = cursor.read_u32::<LittleEndian>()?;
        self.header.node_offset = cursor.read_u64::<LittleEndian>()?;
        self.header.edge_offset = cursor.read_u64::<LittleEndian>()?;
        
        self.node_capacity = self.header.node_capacity;
        self.edge_capacity = self.header.edge_capacity;
        self.embedding_dim = self.header.embedding_dim;
        self.node_offset = self.header.node_offset;
        self.edge_offset = self.header.edge_offset;
        Ok(())
    }
    
    // Добавить узел
    pub fn add_node(&mut self, text: &str, intent: &str) -> Result<u32> {
        if self.header.node_count >= self.node_capacity {
            anyhow::bail!("Node capacity exceeded");
        }

        let id = self.header.node_count;
        let pos = self.node_offset + (id as u64 * Header::NODE_SIZE);
        let mut cursor = std::io::Cursor::new(&mut self.mmap[pos as usize..]);

        cursor.write_u32::<LittleEndian>(id)?;

        // intent
        let intent_bytes = intent.as_bytes();
        cursor.write_u32::<LittleEndian>(intent_bytes.len() as u32)?;
        cursor.write_all(intent_bytes)?;
        cursor.write_all(&vec![0; 64 - 4 - intent_bytes.len()])?; // паддинг

        // text
        let text_bytes = text.as_bytes();
        cursor.write_u32::<LittleEndian>(text_bytes.len() as u32)?;
        cursor.write_all(text_bytes)?;

        // Временно пишем нулевой эмбеддинг (пока нет сервера)
        for _ in 0..self.embedding_dim as usize {
            cursor.write_f32::<LittleEndian>(0.0)?;
        }

        self.header.node_count += 1;
        self.write_header()?;

        Ok(id)
    }
    
    // Добавить связь
    pub fn add_edge(&mut self, from: u32, to: u32, weight: f32) -> Result<()> {
        if self.header.edge_count >= self.edge_capacity {
            anyhow::bail!("Edge capacity exceeded");
        }
        
        let id = self.header.edge_count;
        let pos = self.edge_offset + (id as u64 * Header::EDGE_SIZE);
        let mut cursor = std::io::Cursor::new(&mut self.mmap[pos as usize..]);
        
        cursor.write_u32::<LittleEndian>(from)?;
        cursor.write_u32::<LittleEndian>(to)?;
        cursor.write_f32::<LittleEndian>(weight)?;
        
        self.header.edge_count += 1;
        self.write_header()?;
        Ok(())
    }
    
    // Получить узел
    pub fn get_node(&self, id: u32) -> Result<Node> {
        if id >= self.header.node_count {
            anyhow::bail!("Node not found");
        }
        
        let pos = self.node_offset + (id as u64 * Header::NODE_SIZE);
        let mut cursor = std::io::Cursor::new(&self.mmap[pos as usize..]);
        
        let stored_id = cursor.read_u32::<LittleEndian>()?;
        assert_eq!(stored_id, id);
        
        // intent
        let intent_len = cursor.read_u32::<LittleEndian>()? as usize;
        let mut intent_buf = vec![0; intent_len];
        cursor.read_exact(&mut intent_buf)?;
        let intent = String::from_utf8(intent_buf)?;
        cursor.read_exact(&mut vec![0; 64 - 4 - intent_len])?; // пропустить паддинг
        
        // text
        let text_len = cursor.read_u32::<LittleEndian>()? as usize;
        let mut text_buf = vec![0; text_len];
        cursor.read_exact(&mut text_buf)?;
        let text = String::from_utf8(text_buf)?;
        
        // Читаем эмбеддинг (нули пока что)
        let mut embedding = Vec::with_capacity(self.embedding_dim as usize);
        for _ in 0..self.embedding_dim {
            embedding.push(cursor.read_f32::<LittleEndian>()?);
        }
        
        Ok(Node { id, intent, text, embedding })
    }
    
    // Поиск (косинус) - исправленная версия
    pub fn search(&self, query_emb: &[f32], top_k: usize) -> Vec<(u32, f32)> {
        let node_count = self.header.node_count;
        let mut scores = Vec::new();
    
        for id in 0..node_count {
            if let Ok(node) = self.get_node(id) {
                let norm_node: f32 = node.embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm_node == 0.0 {
                    continue;
                }
            
                let dot: f32 = node.embedding.iter()
                    .zip(query_emb.iter())
                    .map(|(a, b)| a * b)
                    .sum();
            
                let norm_query: f32 = query_emb.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm_query == 0.0 {
                    continue;
                }
            
                let sim = dot / (norm_node * norm_query);
                scores.push((id, sim));
            }
        }
    
        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.into_iter().take(top_k).collect()
    }
    
    // Публичные методы для доступа к статистике
    pub fn node_count(&self) -> u32 {
        self.header.node_count
    }
    
    pub fn edge_count(&self) -> u32 {
        self.header.edge_count
    }
}