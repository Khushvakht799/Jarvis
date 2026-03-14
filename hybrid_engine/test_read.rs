use std::fs;
use std::time::Instant;

fn main() {
    let start = Instant::now();
    
    let files = vec![
        "./test_docs/ai.txt",
        "./test_docs/search.txt", 
        "./test_docs/hybrid.txt",
        "./test_docs/doc1.txt",
        "./test_docs/doc2.txt",
        "./test_docs/doc3.txt",
    ];
    
    for file in files {
        match fs::read_to_string(file) {
            Ok(content) => println!(" {}: {} bytes", file, content.len()),
            Err(e) => println!(" {}: {}", file, e),
        }
    }
    
    println!(" Время: {:?}", start.elapsed());
}
