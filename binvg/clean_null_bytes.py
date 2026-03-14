import os
import re

def clean_file(filepath):
    """Удаляет нулевые байты из файла"""
    if not os.path.exists(filepath):
        print(f"Файл не найден: {filepath}")
        return
    
    # Читаем как бинарный
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Удаляем нулевые байты
    cleaned = content.replace(b'\x00', b'')
    
    # Записываем обратно
    with open(filepath, 'wb') as f:
        f.write(cleaned)
    
    print(f"✅ Очищен: {filepath}")
    print(f"   Было: {len(content)} байт, стало: {len(cleaned)} байт")

# Очищаем проблемные файлы
files_to_clean = [
    "web/app.py",
    "run_web.py",
    "run_daemon.py",
    "core/engine/interpreter.py",
    "core/orchestrator/engine.py"
]

for filepath in files_to_clean:
    clean_file(filepath)

print("\n✅ Все файлы очищены от нулевых байтов")
