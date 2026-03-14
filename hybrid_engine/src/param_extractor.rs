//! param_extractor.rs — извлечение параметров после глагола
pub struct ParamExtractor;

impl ParamExtractor {
    /// Возвращает срез токенов, начиная с индекса start
    pub fn extract(tokens: &[String], start: usize) -> Vec<String> {
        if start < tokens.len() {
            tokens[start..].to_vec()
        } else {
            Vec::new()
        }
    }
}