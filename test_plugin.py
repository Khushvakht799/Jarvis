import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Заглушка для kernel
class DummyKernel:
    def __init__(self):
        self.config = {}
    def get_plugin(self, name):
        return None

# Импортируем плагин
from plugins.llm_chat import LLMChatPlugin

print("🔄 Инициализация плагина...")
plugin = LLMChatPlugin(DummyKernel())
if plugin.initialize():
    print("✅ Плагин инициализирован")
    
    # Показываем доступные модели
    print("\n📋 Доступные модели:")
    for m in plugin.get_models_list():
        print(f"  - {m['name']}: {m['description']}")
        
    # Пробуем загрузить Qwen3
    print("\n🔄 Загрузка Qwen3...")
    result = plugin.load_model("qwen3")
    print(f"Результат: {result}")
else:
    print("❌ Ошибка инициализации")
