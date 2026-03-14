mod lib;
use lib::BinVGr;
use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "binvg")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Добавить узел
    Add {
        text: String,
        #[arg(default_value = "memory")]
        intent: String,
    },
    /// Поиск по тексту
    Search {
        query: String,
        #[arg(short, long, default_value_t = 5)]
        top_k: usize,
    },
    /// Связать узлы
    Connect {
        from: u32,
        to: u32,
        #[arg(default_value_t = 0.7)]
        weight: f32,
    },
    /// Статистика
    Stats,
}

fn get_embedding(text: &str) -> Result<Vec<f32>> {
    let client = reqwest::blocking::Client::new();
    
    // Используем правильный формат для nano-vLLM
    let body = serde_json::json!({
        "prompt": text,
        "mode": "embedding"
    });
    
    let resp = client.post("http://127.0.0.1:5000/generate")
        .json(&body)
        .send()
        .map_err(|e| anyhow::anyhow!("Ошибка соединения с nano-vLLM: {}", e))?;
    
    let json: serde_json::Value = resp.json()
        .map_err(|e| anyhow::anyhow!("Ошибка парсинга ответа: {}", e))?;
    
    // Ответ приходит в поле "response" как строка с эмбеддингом?
    // Или как JSON массив? Нужно посмотреть структуру ответа
    
    if let Some(emb_str) = json["response"].as_str() {
        // Если это строка с числами через запятую
        let emb: Vec<f32> = emb_str.split(',')
            .filter_map(|s| s.trim().parse::<f32>().ok())
            .collect();
        if !emb.is_empty() {
            return Ok(emb);
        }
    }
    
    if let Some(emb_array) = json["embedding"].as_array() {
        return Ok(emb_array.iter()
            .map(|v| v.as_f64().unwrap_or(0.0) as f32)
            .collect());
    }
    
    // Если пришел обычный текст - возможно это не эмбеддинг
    anyhow::bail!("Не могу найти эмбеддинг в ответе: {}", json)
}

fn main() -> Result<()> {
    let path = PathBuf::from("jarvis.binvg");
    
    let mut store = if path.exists() {
        BinVGr::open(&path)?
    } else {
        BinVGr::create(&path, 10000, 50000, 128)? // 10k узлов, 50k связей, 128-dim
    };
    
    let cli = Cli::parse();
    
    match cli.command {
        Commands::Add { text, intent } => {
            let id = store.add_node(&text, &intent)?;
            println!("✅ Добавлен узел {id}: {text} [{intent}]");
        }
        Commands::Search { query, top_k } => {
            println!("🔍 Поиск (без эмбеддингов, показываю все узлы):");
    
            // Пока просто показываем все узлы
            for id in 0..store.node_count() {
                if let Ok(node) = store.get_node(id) {
                    println!("  [{}] {}", id, node.text);
                }
            }
        }
        Commands::Connect { from, to, weight } => {
            store.add_edge(from, to, weight)?;
            println!("🔗 Связь {from} → {to} (вес {weight})");
        }
        Commands::Stats => {
            println!("📊 Статистика BinVGr");
            println!("  Узлов: {}", store.node_count());
            println!("  Связей: {}", store.edge_count());
        }
    }
    
    Ok(())
}