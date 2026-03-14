use std::fs;
use serde_json::Value;

fn main() {
    // 1. Читаем JSON
    let json_str = fs::read_to_string("jarvis_binvg.json")?;
    let json: Value = serde_json::from_str(&json_str)?;
    
    // 2. Создаём новый бинарный файл
    let mut binvg = BinVGr::create("jarvis.binvg", 100000, 200000, 128)?;
    
    // 3. Конвертируем узлы
    let nodes = json["nodes"].as_object().unwrap();
    for (id_str, node) in nodes {
        let id: u32 = id_str.parse().unwrap();
        let text = node["text"].as_str().unwrap();
        let intent = node["intent"].as_str().unwrap_or("memory");
        
        // Получаем эмбеддинг (если есть) или генерируем пустой
        let emb = match node["embedding"].as_array() {
            Some(arr) => arr.iter().map(|v| v.as_f64().unwrap() as f32).collect(),
            None => vec![0.0; 128] // заглушка
        };
        
        binvg.add_node(text, intent, &emb)?;
    }
    
    // 4. Конвертируем связи
    let edges = json["edges"].as_array().unwrap();
    for edge in edges {
        let from = edge["from"].as_u64().unwrap() as u32;
        let to = edge["to"].as_u64().unwrap() as u32;
        let weight = edge["weight"].as_f64().unwrap_or(0.7) as f32;
        
        binvg.add_edge(from, to, weight)?;
    }
    
    println!("✅ Конвертация завершена: {} узлов, {} связей", 
             binvg.node_count(), binvg.edge_count());
}