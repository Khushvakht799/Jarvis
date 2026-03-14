from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import threading

app = Flask(__name__)

# Глобальные переменные для модели
model = None
tokenizer = None
lock = threading.Lock()

def load_model():
    global model, tokenizer
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
    print("✅ Модель готова!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": "Qwen3-0.6B"})

@app.route('/generate', methods=['POST'])
def generate():
    with lock:
        data = request.json
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 200)
        temperature = data.get('temperature', 0.7)
        
        # Форматируем промпт
        messages = [{"role": "user", "content": prompt}]
        formatted = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer(formatted, return_tensors="pt").to("cuda")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        input_length = inputs['input_ids'].shape[1]
        response = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
        
        return jsonify({"response": response})

if __name__ == '__main__':
    load_model()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
