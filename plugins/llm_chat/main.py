"""
LLM Chat Plugin with BVG Memory
Поддержка локальных моделей с семантической памятью
"""

import os
import json
import threading
from pathlib import Path
from datetime import datetime

# Импортируем BVG (теперь напрямую, без sys.path)
from plugins.bvg_memory.main import BVGGraph

# Попытка импорта llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    Llama = None

class Plugin:
    """Плагин для работы с локальными LLM моделями с BVG памятью"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.name = "llm_chat"
        self.version = "0.2.0"
        self.description = "Local LLM Chat with BVG Memory"
        
        # Конфигурация моделей
        self.models = {
            "qwen3": {
                "path": r"C:\Users\Usuario\Documents\LM\Qwen3-0.6B-Q8_0.gguf",
                "name": "Qwen3 0.6B Instruct",
                "context": 40960,
                "template": "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
                "stop": ["<|im_end|>"],
                "temperature": 0.7,
                "max_tokens": 2048,
                "description": "40K контекст, Q8 точность"
            },
            "phi3": {
                "path": r"C:\Users\Usuario\Documents\LM\phi3-mini.gguf",
                "name": "Phi-3 Mini",
                "context": 4096,
                "template": "<|user|>\n{prompt}<|end|>\n<|assistant|>\n",
                "stop": ["<|end|>"],
                "temperature": 0.7,
                "max_tokens": 2048,
                "description": "Хорош для диалогов"
            },
            "deepseek": {
                "path": r"C:\Users\Usuario\Documents\LM\deepseek-coder-1.3b-base.Q2_K.gguf",
                "name": "DeepSeek Coder 1.3B",
                "context": 16384,
                "template": "### Instruction:\n{prompt}\n\n### Response:\n",
                "stop": ["\n###", "\n\n"],
                "temperature": 0.5,
                "max_tokens": 2048,
                "description": "Для кода"
            }
        }

        self.current_model = "qwen3"
        self.model_instance = None
        self.chat_history = []
        self.loading_thread = None
        self.history_dir = Path("data/chat_history")
        self.history_dir.mkdir(exist_ok=True)
        
        # Инициализируем BVG
        self.bvg = BVGGraph()
        print(f"  📚 BVG: {self.bvg.get_conversation_summary()}")

    def on_load(self):
        """Вызывается при загрузке плагина"""
        print(f"  • {self.name}: Загрузка...")

        if not LLAMA_AVAILABLE:
            print(f"  ⚠️  {self.name}: llama-cpp-python не установлен")
            return False

        # Проверяем наличие файлов моделей
        available = []
        for model_id, config in self.models.items():
            if Path(config["path"]).exists():
                size = Path(config["path"]).stat().st_size / (1024**3)
                print(f"     ✓ {config['name']}: {size:.1f} GB")
                available.append(model_id)
            else:
                print(f"     ✗ {config['name']}: файл не найден")

        if not available:
            print(f"  ❌ {self.name}: Нет доступных моделей")
            return False

        print(f"  ✓ {self.name}: Готов (доступно {len(available)} моделей)")
        return True

    def on_unload(self):
        """Вызывается при выгрузке плагина"""
        if self.model_instance:
            del self.model_instance
            self.model_instance = None
        self.bvg.save()
        print(f"  • {self.name}: память сохранена")

    def get_models_list(self):
        """Получить список доступных моделей"""
        models = []
        for model_id, config in self.models.items():
            if Path(config["path"]).exists():
                models.append({
                    "id": model_id,
                    "name": config["name"],
                    "description": config["description"],
                    "context": config["context"],
                    "current": model_id == self.current_model
                })
        return models

    def load_model(self, model_id=None, force=False):
        """Загрузка модели в фоне"""
        if model_id is None:
            model_id = self.current_model

        if model_id not in self.models:
            return {"error": f"Модель {model_id} не найдена"}

        config = self.models[model_id]
        if not Path(config["path"]).exists():
            return {"error": f"Файл модели не найден: {config['path']}"}

        if self.model_instance and self.current_model == model_id and not force:
            return {"status": "already_loaded", "model": model_id}

        def _load():
            try:
                print(f"  🔄 {self.name}: Загрузка {config['name']}...")
                self.model_instance = Llama(
                    model_path=config["path"],
                    n_ctx=config["context"],
                    n_threads=4,
                    verbose=False
                )
                self.current_model = model_id
                print(f"  ✓ {self.name}: Модель загружена")
            except Exception as e:
                print(f"  ❌ {self.name}: Ошибка загрузки: {e}")
                self.model_instance = None

        if self.loading_thread and self.loading_thread.is_alive():
            return {"status": "loading"}

        self.loading_thread = threading.Thread(target=_load)
        self.loading_thread.start()
        return {"status": "loading_started"}

    def chat(self, prompt, model_id=None, system_prompt=None):
        """Отправить запрос к модели с BVG памятью"""
        
        # 1. Создаем узел в BVG
        node = self.bvg.create_node(prompt)
        
        # 2. Получаем контекст из BVG
        context = self.bvg.get_context(max_depth=3)
        
        # 3. Формируем промт с контекстом
        context_text = ""
        for msg in context[:-1]:
            context_text += f"[{msg['intent']}] {msg['content']}\n"
        
        if context_text:
            full_prompt = f"""Предыдущий контекст разговора (намерения в скобках):
{context_text}

Текущий запрос ({node.intent}): {prompt}

Ответь естественно, учитывая историю разговора."""
        else:
            full_prompt = prompt
        
        if not LLAMA_AVAILABLE:
            return {"error": "llama-cpp-python не установлен"}
            
        if model_id is None:
            model_id = self.current_model

        if not self.model_instance or self.current_model != model_id:
            load_result = self.load_model(model_id)
            if load_result.get("error"):
                return load_result
            return {"status": "loading", "message": "Модель загружается"}

        config = self.models[model_id]

        if system_prompt:
            model_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n{config['template'].format(prompt=full_prompt)}"
        else:
            model_prompt = config['template'].format(prompt=full_prompt)

        try:
            response = self.model_instance(
                model_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                stop=config["stop"],
                echo=False
            )

            answer = response['choices'][0]['text'].strip()

            node.resolve(answer)
            
            self.chat_history.append({
                "timestamp": datetime.now().isoformat(),
                "model": model_id,
                "prompt": prompt,
                "response": answer,
                "bvg_node": node.id
            })

            self.bvg.save()

            return {
                "response": answer,
                "model": model_id,
                "tokens": response.get('usage', {}).get('total_tokens', 0),
                "bvg_node": node.id
            }

        except Exception as e:
            return {"error": str(e)}

    def save_history(self, filename=None):
        if filename is None:
            filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.history_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "model": self.current_model,
                "history": self.chat_history[-50:],
                "bvg_summary": self.bvg.get_conversation_summary()
            }, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def clear_history(self):
        self.chat_history = []
        self.bvg = BVGGraph()
        
    def bvg_stats(self):
        return self.bvg.get_conversation_summary()

# Регистрация плагина
plugin_class = Plugin