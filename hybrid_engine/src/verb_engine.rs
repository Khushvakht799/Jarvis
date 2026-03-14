//! verb_engine.rs — загрузка словаря глаголов с canonical_action
use std::collections::HashMap;
use serde_json::Value;
use std::fs;

pub struct VerbEngine {
    word_to_id: HashMap<String, u32>,
    id_to_canonical: HashMap<u32, String>,
}

impl VerbEngine {
    pub fn new() -> Self {
        let mut engine = VerbEngine {
            word_to_id: HashMap::new(),
            id_to_canonical: HashMap::new(),
        };
        engine.load_from_file("brain/verbs.json").ok();
        engine
    }

    fn load_from_file(&mut self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        let content = fs::read_to_string(path)?;
        let json: Value = serde_json::from_str(&content)?;
        if let Value::Object(map) = json {
            for (id_str, data) in map {
                if let Ok(verb_id) = id_str.parse::<u32>() {
                    if let Some(verbs_array) = data.get("verbs").and_then(|v| v.as_array()) {
                        let canonical = data["canonical_action"].as_str().unwrap_or("").to_string();
                        self.id_to_canonical.insert(verb_id, canonical);
                        for v in verbs_array {
                            if let Some(verb) = v.as_str() {
                                self.word_to_id.insert(verb.to_lowercase(), verb_id);
                            }
                        }
                    }
                }
            }
        }
        Ok(())
    }

    /// Возвращает идентификатор глагола по сырому токену
    pub fn get_verb_id(&self, raw_token: &str) -> Option<u32> {
        self.word_to_id.get(&raw_token.to_lowercase()).copied()
    }

    /// Возвращает canonical_action по идентификатору
    pub fn get_canonical_action(&self, verb_id: u32) -> Option<&String> {
        self.id_to_canonical.get(&verb_id)
    }

    /// Для обратной совместимости: возвращает canonical_action или "UNKNOWN"
    pub fn get_action_by_id(&self, verb_id: u32) -> Option<&String> {
        self.get_canonical_action(verb_id)
    }
}