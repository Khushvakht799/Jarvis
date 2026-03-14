use crate::core::BinVGrGraph;
use crate::adapter::LLMAdapter;
use anyhow::Result;
use std::sync::Arc;

pub struct BinVGrPipeline<A: LLMAdapter> {
    graph: BinVGrGraph,
    adapter: Arc<A>,
}

impl<A: LLMAdapter> BinVGrPipeline<A> {
    pub fn new(graph: BinVGrGraph, adapter: A) -> Self {
        Self {
            graph,
            adapter: Arc::new(adapter),
        }
    }
    
    pub fn ask(&mut self, question: &str) -> Result<String> {
        let query_emb = self.adapter.embedding(question)?;
        let node_ids = self.graph.search(&query_emb, 5);
        let context = self.build_context(&node_ids)?;
        
        // ПРАВИЛЬНО: без экранированных слешей
        let prompt = format!("Context:\n{}\n\nQuestion: {}\nAnswer:", context, question);
        
        let response = self.adapter.generate(&prompt, 500)?;
        
        // Сохраняем диалог
        self.graph.add_node(&format!("Q: {}", question), "question")?;
        self.graph.add_node(&format!("A: {}", response), "answer")?;
        
        Ok(response)
    }
    
    fn build_context(&self, node_ids: &[u32]) -> Result<String> {
        let mut context = String::new();
        for &id in node_ids {
            if let Some(text) = self.graph.get_node_text(id)? {
                context.push_str(&format!("- {}\n", text));
            }
        }
        Ok(context)
    }
    
    pub fn add_knowledge(&mut self, text: &str, intent: &str) -> Result<u32> {
        self.graph.add_node(text, intent)
    }
    
    pub fn stats(&self) -> (u32, u32) {
        (self.graph.node_count(), self.graph.edge_count())
    }
    pub fn auto_connect(&mut self, from: u32, to: u32) -> anyhow::Result<()> {
        if from == to {
            return Ok(());
        }

        self.graph.add_edge(from, to, 0.8, 1)?;
        Ok(())
    }
}

