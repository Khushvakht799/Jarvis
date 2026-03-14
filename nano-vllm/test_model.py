from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def test_model():
    model_path = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"
    
    print("📂 Загрузка токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    print("🚀 Загрузка модели на GPU...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Простой тест
    prompt = "Привет! Как дела?"
    print(f"\n📝 Запрос: {prompt}")
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    print("🤔 Генерация...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\n💬 Ответ: {response}")

if __name__ == "__main__":
    test_model()
