from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def test_model():
    model_path = "C:/Users/Usuario/Jarvis/nano-vllm/models/Qwen3-0.6B"
    
    print("📂 Загрузка токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, 
        trust_remote_code=True,
        fix_mistral_regex=True
    )
    
    print("🚀 Загрузка модели на GPU...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Тестовые промпты
    prompts = [
        "Привет! Как дела? Расскажи коротко о себе.",
        "Напиши функцию на Python для сортировки списка.",
        "Что такое графовая память простыми словами?"
    ]
    
    for user_prompt in prompts:
        print(f"\n{'='*50}")
        print(f"📝 Запрос: {user_prompt}")
        
        messages = [{"role": "user", "content": user_prompt}]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        
        print("🤔 Думаю...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,  # увеличили до 200
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        input_length = inputs['input_ids'].shape[1]
        response = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
        
        print(f"\n💬 Ответ:\n{response}")

if __name__ == "__main__":
    test_model()
