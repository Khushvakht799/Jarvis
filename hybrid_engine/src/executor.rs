//! executor.rs — исполнение команд с сохранением результата в MemoryGraph
use crate::jvgr::{JVGRGraph, JVGRNode};
use crate::verb_engine::VerbEngine;
use crate::memory_graph::{MemoryGraph, ExecutionResult, ExecutionStatus};
use std::process::Command as StdCommand;
use std::fs;
use meval;
use std::time::Instant;

pub struct Executor {
    verb_engine: VerbEngine,
    memory_graph: MemoryGraph,
}

impl Executor {
    pub fn new(max_memory_nodes: usize) -> Self {
        Executor {
            verb_engine: VerbEngine::new(),
            memory_graph: MemoryGraph::new(max_memory_nodes),
        }
    }

    pub fn execute_graph(&mut self, graph: &mut JVGRGraph) {
        while let Some(node) = graph.current_node() {
            let (mut result, duration) = self.execute_node_with_measure(node);
            result.duration_ms = duration;
            // Сохраняем в память
            let object_str = if !node.parameters.is_empty() {
                node.parameters[0].clone()  // первый параметр считается объектом (как в command_parser)
            } else {
                String::new()
            };
            self.memory_graph.add_memory(
                node.id,
                node.verb_id,
                object_str,
                node.parameters.clone(),
                result,
            );
            graph.advance();
        }
        graph.reset();
    }

    fn execute_node_with_measure(&self, node: &JVGRNode) -> (ExecutionResult, u64) {
        let start = Instant::now();
        let res = self.execute_node(node);
        let duration = start.elapsed().as_millis() as u64;
        (res, duration)
    }

    fn execute_node(&self, node: &JVGRNode) -> ExecutionResult {
        let action = self.verb_engine.get_canonical_action(node.verb_id)
            .cloned()
            .unwrap_or_else(|| "UNKNOWN".to_string());
        let params = &node.parameters;

        // вспомогательные функции для результата (duration_ms будет заполнен позже)
        let success = |output: String| ExecutionResult {
            status: ExecutionStatus::Success,
            output,
            duration_ms: 0,
        };
        let error = |output: String| ExecutionResult {
            status: ExecutionStatus::Error,
            output,
            duration_ms: 0,
        };

        match action.as_str() {
            "SEARCH" => {
                let query = params.join(" ");
                println!("🔍 Поиск: {}", query);
                let output = format!("Поиск по запросу '{}'", query);
                // Здесь можно добавить реальный вызов hybrid_cli и захват вывода
                success(output)
            }
            "OPEN" => {
                if let Some(target) = params.first() {
                    println!("📂 Открыть: {}", target);
                    #[cfg(target_os = "windows")]
                    let cmd = StdCommand::new("explorer").arg(target).status();
                    #[cfg(not(target_os = "windows"))]
                    let cmd = StdCommand::new("xdg-open").arg(target).status();
                    match cmd {
                        Ok(_) => success(format!("Открыто {}", target)),
                        Err(e) => error(format!("Ошибка открытия {}: {}", target, e)),
                    }
                } else {
                    error("Нет цели для открытия".to_string())
                }
            }
            "DELETE" => {
                if let Some(target) = params.first() {
                    let path = std::path::Path::new(target);
                    if path.exists() {
                        let res = if path.is_file() {
                            fs::remove_file(path)
                        } else {
                            fs::remove_dir_all(path)
                        };
                        match res {
                            Ok(_) => success(format!("Удалено {}", target)),
                            Err(e) => error(format!("Ошибка удаления {}: {}", target, e)),
                        }
                    } else {
                        error(format!("Путь не найден: {}", target))
                    }
                } else {
                    error("Нет цели для удаления".to_string())
                }
            }
            "CALCULATE" => {
                let expr = params.join(" ");
                match meval::eval_str(&expr) {
                    Ok(res) => success(format!("{} = {}", expr, res)),
                    Err(e) => error(format!("Ошибка вычисления {}: {}", expr, e)),
                }
            }
            // Для других действий аналогично, пока заглушки
            _ => {
                let output = format!("Действие {} выполнено (заглушка)", action);
                println!("⚠️ {}", output);
                success(output)
            }
        }
    }

    pub fn memory_graph(&self) -> &MemoryGraph {
        &self.memory_graph
    }

    pub fn clear_memory(&mut self) {
        self.memory_graph = MemoryGraph::new(self.memory_graph.max_nodes());
    }

    pub fn save_memory(&self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.memory_graph.save_to_file(path)
    }

    pub fn load_memory(&mut self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.memory_graph = MemoryGraph::load_from_file(path)?;
        Ok(())
    }
}
