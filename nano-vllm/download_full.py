from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "Qwen/Qwen3-0.6B"
local_dir = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"

print(f"📥 Загружаю {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

print("💾 Сохраняю локально...")
model.save_pretrained(local_dir)
tokenizer.save_pretrained(local_dir)

print("✅ Готово!")
