from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

model_name = "Qwen/Qwen3-0.6B"
local_dir = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"

print(f"📥 Загружаю {model_name}...")
print("⏳ Это займет несколько минут (около 600 МБ)")

# Создаем папку если нет
os.makedirs(local_dir, exist_ok=True)

# Загружаем токенизатор
print("📝 Загрузка токенизатора...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

# Загружаем модель (в половинной точности для экономии памяти)
print("🧠 Загрузка модели...")
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype=torch.float16,  # половинная точность
    device_map="auto",           # автоматически на GPU
    trust_remote_code=True
)

# Сохраняем локально
print("💾 Сохранение...")
model.save_pretrained(local_dir)
tokenizer.save_pretrained(local_dir)

print(f"✅ Готово! Модель сохранена в: {local_dir}")
print(f"📊 Размер на диске: примерно 600 МБ")
