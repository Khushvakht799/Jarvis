use anyhow::Result;

pub trait LLMAdapter {
    fn generate(&self, prompt: &str, max_tokens: u32) -> Result<String>;
    fn embedding(&self, text: &str) -> Result<Vec<f32>>;
}

pub struct NanoVLLMAdapter {
    pub endpoint: String,
}

impl NanoVLLMAdapter {
    pub fn new(endpoint: &str) -> Self {
        Self {
            endpoint: endpoint.to_string(),
        }
    }
}

impl LLMAdapter for NanoVLLMAdapter {
    fn generate(&self, prompt: &str, _max_tokens: u32) -> Result<String> {
        // Реальный вызов к nano-vLLM
        Ok(format!("Ответ от {}: {}", self.endpoint, prompt))
    }
    
    fn embedding(&self, text: &str) -> Result<Vec<f32>> {
        // Пока заглушка
        Ok(vec![0.1; 384])
    }
}

pub struct MockAdapter;

impl MockAdapter {
    pub fn new() -> Self {
        Self
    }
}

impl LLMAdapter for MockAdapter {
    fn generate(&self, prompt: &str, _max_tokens: u32) -> Result<String> {
        Ok(format!("[Mock] {}", prompt))
    }
    
    fn embedding(&self, _text: &str) -> Result<Vec<f32>> {
        Ok(vec![0.0; 384])
    }
}
