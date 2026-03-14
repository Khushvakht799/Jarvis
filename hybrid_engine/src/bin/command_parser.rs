//! command_parser.rs — обновлён для работы с JVGRNode.id и MemoryGraph
use std::env;
use hybrid_engine::nlp_minimal::process_text;
use hybrid_engine::verb_engine::VerbEngine;
use hybrid_engine::object_detector::{ObjectDetector, entity_to_id};
use hybrid_engine::param_extractor::ParamExtractor;
use hybrid_engine::jvgr::JVGRGraph;
use hybrid_engine::executor::Executor;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Использование: command_parser <текст команды>");
        return;
    }
    let input = args[1..].join(" ");
    println!("📥 Ввод: {}", input);

    // 1. Токенизация (сырые токены)
    let raw_tokens: Vec<String> = input.split_whitespace().map(|s| s.to_string()).collect();
    println!("🔤 Сырые токены: {:?}", raw_tokens);

    // 2. Определение глагола (по сырым токенам)
    let verb_engine = VerbEngine::new();
    let mut verb_id = None;
    let mut verb_index = 0;
    for (i, token) in raw_tokens.iter().enumerate() {
        if let Some(id) = verb_engine.get_verb_id(token) {
            verb_id = Some(id);
            verb_index = i;
            break;
        }
    }
    if verb_id.is_none() {
        eprintln!("❌ Не удалось определить действие");
        return;
    }
    let verb_id = verb_id.unwrap();
    println!("🎯 verb_id: {} ({:?})", verb_id, verb_engine.get_canonical_action(verb_id).unwrap());

    // 3. NLP для оставшихся токенов (определение объекта и параметров)
    let remaining = raw_tokens[verb_index+1..].join(" ");
    let nlp_tokens = process_text(&remaining);
    println!("🔤 NLP токены: {:?}", nlp_tokens);

    // 4. Object detection (по первому NLP токену)
    let object_type = if !nlp_tokens.is_empty() {
        ObjectDetector::detect(&nlp_tokens[0])
    } else {
        hybrid_engine::object_detector::EntityType::Unknown
    };
    let object_id = entity_to_id(&object_type);
    let object_str = nlp_tokens.first().cloned().unwrap_or_else(|| "".to_string());
    println!("📦 Объект: {:?} (id: {}), строка: '{}'", object_type, object_id, object_str);

    // 5. Параметры: включаем токен объекта + остальные токены
    let mut params = Vec::new();
    if !nlp_tokens.is_empty() {
        params.push(nlp_tokens[0].clone());
        params.extend(ParamExtractor::extract(&nlp_tokens, 1));
    }
    println!("📎 Параметры: {:?}", params);

    // 6. Создание JVGR графа и узла (с автоматическим id)
    let mut graph = JVGRGraph::new();
    let node_id = graph.add_node(verb_id, object_id, params.clone());
    println!("✅ JVGR узел создан с id: {}", node_id);

    // 7. Исполнение через Executor с памятью
    let mut executor = Executor::new(10000);
    executor.execute_graph(&mut graph);

    // 8. Покажем последнюю запись памяти
    if let Some(last) = executor.memory_graph().last_memory() {
        println!("💾 Последняя запись памяти: memory_id={}, jvgr_node_id={}, verb_id={}, object='{}', duration_ms={}",
                 last.memory_id, last.jvgr_node_id, last.verb_id, last.object, last.result.duration_ms);
    }
}