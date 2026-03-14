from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def test_model():
    model_path = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"
    
    print("📂 Загрузка токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, 
        trust_remote_code=True,
        fix_mistral_regex=True  # фикс для предупреждения
    )
    
    print("🚀 Загрузка модели на GPU...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Правильный формат промпта для Qwen3
    messages = [
        {"role": "user", "content": "Привет! Как дела? Расскажи коротко."}
    ]
    
    # Применяем шаблон чата
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    print(f"\n📝 Форматированный запрос: {prompt}")
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    print("🤔 Генерация...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1  # штраф за повторы
        )
    
    # Извлекаем только ответ (без промпта)
    input_length = inputs['input_ids'].shape[1]
    response = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
    
    print(f"\n💬 Ответ: {response}")

if __name__ == "__main__":
    test_model()
