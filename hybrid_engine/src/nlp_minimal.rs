//! Минимальный NLP на Rust для Jarvis
use std::collections::HashSet;

pub struct Tokenizer;
impl Tokenizer {
    pub fn tokenize(text: &str) -> Vec<String> {
        let mut tokens = Vec::new();
        let mut current = String::new();
        for c in text.chars() {
            if c.is_alphanumeric() || c == '.' || c == '-' || c == ':' {
                current.push(c);
            } else {
                if !current.is_empty() {
                    tokens.push(current.clone());
                    current.clear();
                }
            }
        }
        if !current.is_empty() {
            tokens.push(current);
        }
        let mut refined = Vec::new();
        for token in tokens {
            if token.contains('.') && token.len() > 2 {
                for part in token.split('.') {
                    if !part.is_empty() {
                        refined.push(part.to_lowercase());
                    }
                }
            } else {
                refined.push(token.to_lowercase());
            }
        }
        refined
    }
}

pub struct Normalizer;
impl Normalizer {
    pub fn normalize(word: &str) -> String {
        let w = word.to_lowercase();
        let chars: Vec<char> = w.chars().collect();
        let len = chars.len();
        if len > 5 {
            let suffix: String = chars[len-5..].iter().collect();
            if suffix == "ового" || suffix == "евого" || suffix == "овую" || suffix == "евую" {
                return chars[..len-5].iter().collect();
            }
        }
        if len > 4 {
            let suffix: String = chars[len-4..].iter().collect();
            if suffix == "овой" || suffix == "евой" || suffix == "овая" || suffix == "евая" {
                return chars[..len-4].iter().collect();
            }
        }
        if len > 3 {
            let suffix3: String = chars[len-3..].iter().collect();
            let suffix2: String = chars[len-2..].iter().collect();
            match suffix2.as_str() {
                "ая" | "яя" | "ый" | "ий" | "ой" | "ое" | "ее" | "ые" | "ие" | "ую" | "юю" => {
                    return chars[..len-2].iter().collect();
                }
                _ => {}
            }
            match suffix3.as_str() {
                "ого" | "его" | "ому" | "ему" => {
                    return chars[..len-3].iter().collect();
                }
                _ => {}
            }
        }
        if len > 2 {
            let suffix1: String = chars[len-1..].iter().collect();
            let suffix2: String = chars[len-2..].iter().collect();
            match suffix1.as_str() {
                "а" | "я" | "у" | "ю" | "ы" | "и" | "е" | "ё" => {
                    return chars[..len-1].iter().collect();
                }
                _ => {}
            }
            match suffix2.as_str() {
                "ом" | "ем" | "ов" | "ев" => {
                    return chars[..len-2].iter().collect();
                }
                _ => {}
            }
        }
        w
    }
}

pub struct StopFilter {
    stop_words: HashSet<&'static str>,
}
impl StopFilter {
    pub fn new() -> Self {
        let stop_words = HashSet::from_iter(vec![
            "и", "в", "во", "на", "с", "со", "к", "ко", "у", "о", "об",
            "от", "ото", "до", "за", "про", "без", "безо", "над", "под",
            "а", "но", "да", "или", "либо", "то", "что", "чтобы", "если",
            "как", "так", "же", "бы", "ли", "ни", "не", "вот", "это", "тот",
            "этот", "такой", "свой", "его", "её", "их", "нас", "вас", "меня",
            "тебя", "себя", "кто", "что", "где", "куда", "откуда", "почему",
            "зачем", "потому", "поэтому", "когда", "всегда", "никогда",
            "очень", "совсем", "почти", "уже", "ещё", "тоже", "также",
        ]);
        Self { stop_words }
    }
    pub fn is_stop(&self, word: &str) -> bool {
        self.stop_words.contains(word)
    }
}

pub fn process_text(text: &str) -> Vec<String> {
    let stop_filter = StopFilter::new();
    let tokens = Tokenizer::tokenize(text);
    let mut result = Vec::new();
    for token in tokens {
        let norm = Normalizer::normalize(&token);
        if !stop_filter.is_stop(&norm) && norm.len() > 1 {
            result.push(norm);
        }
    }
    result
}