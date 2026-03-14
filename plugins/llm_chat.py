"""
LLM Chat Plugin for Jarvis
Поддержка локальных моделей (Qwen3, Phi-3, DeepSeek)
"""

import os
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Попытка импорта llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    Llama = None

class LLMChatPlugin:
    """Плагин для работы с локальными LLM моделями"""

    def __init__(self, kernel):
        self.kernel = kernel
        self.name = "llm_chat"
        self.description = "Local LLM Chat (Qwen3, Phi-3, DeepSeek)"
        self.version = "0.1.0"

        # Конфигурация моделей (из ваших метаданных)
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

        self.current_model = "qwen3"  # По умолчанию
        self.model_instance = None
        self.chat_history = []
        self.is_loading = False
        self.loading_thread = None

        # Путь для сохранения истории
        self.history_dir = Path("data/chat_history")
        self.history_dir.mkdir(exist_ok=True)

    def initialize(self):
        """Инициализация плагина"""
        print(f"  • {self.name}: Загрузка...")

        if not LLAMA_AVAILABLE:
            print(f"  ⚠️  {self.name}: llama-cpp-python не установлен")
            print("     Установите: pip install llama-cpp-python")
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

    def shutdown(self):
        """Выгрузка плагина"""
        if self.model_instance:
            print(f"  • {self.name}: Выгружаем модель...")
            del self.model_instance
            self.model_instance = None

    def get_models_list(self) -> List[Dict[str, Any]]:
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

    def load_model(self, model_id: str = None, force: bool = False):
        """Загрузка модели в фоне"""
        if model_id is None:
            model_id = self.current_model

        if model_id not in self.models:
            return {"error": f"Модель {model_id} не найдена"}

        config = self.models[model_id]
        if not Path(config["path"]).exists():
            return {"error": f"Файл модели не найден: {config['path']}"}

        # Если модель уже загружена и та же
        if self.model_instance and self.current_model == model_id and not force:
            return {"status": "already_loaded", "model": model_id}

        # Загружаем в фоне
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

    def chat(self, prompt: str, model_id: str = None, system_prompt: str = None) -> Dict[str, Any]:
        """Отправить запрос к модели"""
        if model_id is None:
            model_id = self.current_model

        # Проверяем загрузку
        if not self.model_instance or self.current_model != model_id:
            load_result = self.load_model(model_id)
            if load_result.get("error"):
                return load_result
            return {"status": "loading", "message": "Модель загружается, попробуйте через пару секунд"}

        config = self.models[model_id]

        # Форматируем промт
        if system_prompt:
            full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n{config['template'].format(prompt=prompt)}"
        else:
            full_prompt = config['template'].format(prompt=prompt)

        try:
            # Генерация
            response = self.model_instance(
                full_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                stop=config["stop"],
                echo=False
            )

            answer = response['choices'][0]['text'].strip()

            # Сохраняем в историю
            self.chat_history.append({
                "timestamp": datetime.now().isoformat(),
                "model": model_id,
                "prompt": prompt,
                "response": answer,
                "tokens": response.get('usage', {})
            })

            return {
                "response": answer,
                "model": model_id,
                "tokens": response.get('usage', {}).get('total_tokens', 0)
            }

        except Exception as e:
            return {"error": str(e)}

    def save_history(self, filename: str = None):
        """Сохранить историю чата"""
        if filename is None:
            filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.history_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "model": self.current_model,
                "history": self.chat_history[-50:]  # последние 50
            }, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def clear_history(self):
        """Очистить историю"""
        self.chat_history = []

    def process_document(self, file_path: str, query: str = None) -> Dict[str, Any]:
        """Анализ документа (RAG - простейшая версия)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Обрезаем под контекст модели
            max_chars = self.models[self.current_model]["context"] * 4  # примерно 4 символа на токен
            if len(content) > max_chars:
                content = content[:max_chars] + "\n...[обрезано]"

            prompt = f"Проанализируй этот документ и ответь на вопрос: {query}\n\nДокумент:\n{content[:2000]}" if query else f"Проанализируй этот документ:\n\n{content[:2000]}"

            return self.chat(prompt)

        except Exception as e:
            return {"error": f"Ошибка чтения файла: {e}"}

# Регистрация плагина
plugin_class = LLMChatPlugin