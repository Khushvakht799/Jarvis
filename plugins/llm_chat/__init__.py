from .binvg_adapter import BinVGrAdapter

class LLMChatPlugin:
    def __init__(self):
        # ... существующий код ...
        
        # Заменяем старый BVG на BinVGr
        self.binvg = BinVGrAdapter("jarvis.binvg")
        
        # Загружаем начальные узлы из лога
        self.init_binvg_memory()
        
    def init_binvg_memory(self):
        """Инициализировать бинарную память из существующих данных"""
        # Узлы, которые были при запуске
        memories = [
            ("приветствие", "greeting"),
            ("вопрос", "question"),
            ("команда", "command"),
            ("функция на python", "coding_task"),
            ("история разговора", "context")
        ]
        
        for text, intent in memories:
            self.binvg.add_memory(text, intent)
            
        # Добавим связи
        self.binvg.add_relationship("функция на python", "история разговора", 0.8)
        self.binvg.add_relationship("приветствие", "вопрос", 0.5)
        
    def cmd_chat(self, text):
        # 1. Ищем в бинарной памяти
        memories = self.binvg.query(text, top_k=3)
        
        # 2. Строим контекст
        context = "🧠 BinVGr Memory (бинарная память с весами):\n"
        for mem in memories:
            context += f"- {mem['text']} [intent: {mem['intent']}, relevance: {mem['similarity']:.2f}]\n"
            
        # 3. Добавляем в промпт
        full_prompt = context + "\n" + self.get_history() + "\n\nUser: " + text
        
        # 4. Генерация
        response = self.llm.generate(full_prompt)
        
        # 5. Запоминаем этот диалог
        self.binvg.add_memory(f"User: {text[:50]}", "user_query")
        self.binvg.add_memory(f"Assistant: {response[:50]}", "assistant_response")
        
        return response
        
    def cmd_binvg_stats(self):
        """Показать статистику бинарного хранилища"""
        print(f"📊 BinVGr Storage:")
        print(f"  Файл: {self.binvg.binvg.filename}")
        print(f"  Макс. узлов: {self.binvg.binvg.max_nodes}")
        print(f"  Размер embedding: {self.binvg.binvg.emb_size}")
        print(f"  Следующий ID узла: {self.binvg.next_node_id}")
        
        # Покажем несколько последних узлов
        print("\n📝 Последние узлы:")
        for i in range(max(0, self.binvg.next_node_id-5), self.binvg.next_node_id):
            try:
                node = self.binvg.binvg.read_node(i)
                if node['name']:
                    print(f"  {i}: {node['name']} [{node['intent']}]")
            except:
                pass
                
    def cmd_binvg_search(self, query):
        """Поиск в бинарной памяти"""
        results = self.binvg.query(query, top_k=10)
        print(f"🔍 Поиск: '{query}'")
        for r in results:
            print(f"  {r['similarity']:.3f}: {r['text']} [{r['intent']}]")