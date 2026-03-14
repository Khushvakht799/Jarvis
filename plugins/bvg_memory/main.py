"""
BVG Memory Plugin for Jarvis
Binary Vector Graph - семантическая память
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class BVGNode:
    """Узел семантической памяти"""
    
    def __init__(self, intent: str, content: str, parent_id: str = None):
        self.id = str(uuid.uuid4())[:8]
        self.intent = intent
        self.state = "pending"
        self.content = content
        self.created = datetime.now().isoformat()
        self.parent = parent_id
        self.children = []
        self.evolution = []
        
    def resolve(self, response: str):
        self.state = "resolved"
        self.evolution.append({
            "time": datetime.now().isoformat(),
            "action": "resolve",
            "response": response
        })
        
    def add_child(self, child_id: str):
        if child_id not in self.children:
            self.children.append(child_id)
            
    def to_dict(self):
        return {
            "id": self.id,
            "intent": self.intent,
            "state": self.state,
            "content": self.content,
            "created": self.created,
            "parent": self.parent,
            "children": self.children,
            "evolution": self.evolution
        }

class BVGGraph:
    """Граф семантической памяти"""
    
    def __init__(self, storage_path: str = "data/bvg"):
        self.storage = Path(storage_path)
        self.storage.mkdir(exist_ok=True)
        self.nodes: Dict[str, BVGNode] = {}
        self.current_node_id: Optional[str] = None
        self.load()
        
    def load(self):
        graph_file = self.storage / "graph.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for node_data in data.get("nodes", []):
                        node = BVGNode("", "")
                        node.__dict__.update(node_data)
                        self.nodes[node.id] = node
                    self.current_node_id = data.get("current")
                print(f"  📂 BVG: загружено {len(self.nodes)} узлов")
            except Exception as e:
                print(f"  ⚠️ BVG: ошибка загрузки: {e}")
                
    def save(self):
        data = {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "current": self.current_node_id,
            "updated": datetime.now().isoformat()
        }
        with open(self.storage / "graph.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def detect_intent(self, text: str) -> str:
        text_low = text.lower()
        
        if any(g in text_low for g in ["привет", "здравствуй", "хай", "hello"]):
            return "greeting"
        elif any(q in text_low for q in ["кто", "что", "где", "когда", "почему", "как"]):
            return "question"
        elif any(c in text_low for c in ["сделай", "напиши", "создай", "покажи", "напиши код"]):
            return "command"
        elif text_low in ["да", "нет", "ок", "хорошо", "yes", "no"]:
            return "confirmation"
        else:
            return "statement"
            
    def create_node(self, content: str, intent: str = None) -> BVGNode:
        if intent is None:
            intent = self.detect_intent(content)
            
        node = BVGNode(intent, content, self.current_node_id)
        self.nodes[node.id] = node
        
        if self.current_node_id and self.current_node_id in self.nodes:
            parent = self.nodes[self.current_node_id]
            parent.add_child(node.id)
            
        self.current_node_id = node.id
        self.save()
        return node
        
    def get_context(self, max_depth: int = 5) -> List[Dict]:
        context = []
        node_id = self.current_node_id
        
        depth = 0
        while node_id and node_id in self.nodes and depth < max_depth:
            node = self.nodes[node_id]
            context.append({
                "role": "user",
                "content": node.content,
                "intent": node.intent,
                "state": node.state
            })
            node_id = node.parent
            depth += 1
            
        return list(reversed(context))
        
    def get_conversation_summary(self) -> str:
        """Краткая сводка разговора"""
        if not self.nodes:
            return "Нет истории"
            
        total = len(self.nodes)
        resolved = sum(1 for n in self.nodes.values() if n.state == "resolved")
        intents = {}
        for n in self.nodes.values():
            intents[n.intent] = intents.get(n.intent, 0) + 1
            
        return f"Узлов: {total}, выполнено: {resolved}, намерения: {intents}"

class Plugin:
    """Плагин BVG памяти для Jarvis"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.name = "bvg_memory"
        self.version = "1.0.0"
        self.description = "Binary Vector Graph - семантическая память"
        self.graph = BVGGraph()
        
    def on_load(self):
        print(f"  • {self.name}: загрузка...")
        print(f"     {self.graph.get_conversation_summary()}")
        print(f"  ✓ {self.name}: готов")
        return True
        
    def on_unload(self):
        self.graph.save()
        print(f"  • {self.name}: память сохранена")
        
    def create_node(self, content: str, intent: str = None):
        return self.graph.create_node(content, intent)
        
    def get_context(self):
        return self.graph.get_context()
        
    def get_stats(self):
        return self.graph.get_conversation_summary()

# Регистрация плагина
plugin_class = Plugin