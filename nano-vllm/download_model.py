from huggingface_hub import snapshot_download
import os

model_name = "Qwen/Qwen3-0.6B"
local_dir = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"

print(f"📥 Скачиваю {model_name} в {local_dir}...")
os.makedirs(local_dir, exist_ok=True)

snapshot_download(
    repo_id=model_name,
    local_dir=local_dir,
    local_dir_use_symlinks=False,
    resume_download=True,
    ignore_patterns=["*.safetensors"]  # можно убрать если нужны все файлы
)
print("✅ Готово!")
