//! object_detector.rs — определение типа объекта (с оптимизированным regex)
use std::path::Path;
use once_cell::sync::Lazy;
use regex::Regex;

static DATE_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^\d{1,2}[.-]\d{1,2}[.-]\d{2,4}$|^\d{4}[.-]\d{1,2}[.-]\d{1,2}$").unwrap()
});

#[derive(Debug, Clone, PartialEq)]
pub enum EntityType {
    File,
    Folder,
    Document,
    Text,
    Number,
    Url,
    Date,
    Task,
    Unknown,
}

pub struct ObjectDetector;

impl ObjectDetector {
    pub fn detect(token: &str) -> EntityType {
        let token = token.trim_matches('"');
        // файл с расширением
        if token.contains('.') && !token.ends_with('.') && Path::new(token).extension().is_some() {
            return EntityType::File;
        }
        // папка
        if token.contains('/') || token.contains('\\') {
            return EntityType::Folder;
        }
        // URL
        if token.starts_with("http://") || token.starts_with("https://") || token.starts_with("www.") {
            return EntityType::Url;
        }
        // число
        if token.parse::<f64>().is_ok() {
            return EntityType::Number;
        }
        // дата
        if DATE_REGEX.is_match(token) {
            return EntityType::Date;
        }
        // по умолчанию текст
        EntityType::Text
    }
}

// для числового идентификатора объектов (object_id)
pub fn entity_to_id(entity: &EntityType) -> u32 {
    match entity {
        EntityType::File => 1,
        EntityType::Folder => 2,
        EntityType::Document => 3,
        EntityType::Text => 4,
        EntityType::Number => 5,
        EntityType::Url => 6,
        EntityType::Date => 7,
        EntityType::Task => 8,
        EntityType::Unknown => 0,
    }
}