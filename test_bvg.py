import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from plugins.bvg_memory.main import BVGGraph

print("🔍 Тестирование BVG...")

# Создаем граф
graph = BVGGraph()

# Тест 1: Создание узлов
print("\n📝 Тест 1: Создание узлов")
node1 = graph.create_node("Привет! Меня зовут Иван", "greeting")
print(f"   Создан узел: {node1.id} ({node1.intent})")

node2 = graph.create_node("Какое у меня имя?", "question")
print(f"   Создан узел: {node2.id} ({node2.intent})")

# Тест 2: Контекст
print("\n🔗 Тест 2: Получение контекста")
context = graph.get_context()
for msg in context:
    print(f"   [{msg['intent']}] {msg['content'][:30]}...")

# Тест 3: Завершение узла
print("\n✅ Тест 3: Завершение узла")
node2.resolve("Вас зовут Иван")
print(f"   Узел {node2.id} разрешен")

# Тест 4: Сохранение
print("\n💾 Тест 4: Сохранение")
graph.save()
print(f"   Сохранено в data/bvg/graph.json")

print("\n🎉 Тесты завершены!")
