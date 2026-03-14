"""
Flask API для веб-интерфейса Jarvis
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import json
from pathlib import Path
import threading

class JarvisWebAPI:
    """API для веб-интерфейса"""
    
    def __init__(self, kernel, file_explorer, host='localhost', port=8080):
        self.kernel = kernel
        self.file_explorer = file_explorer
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.route('/')
        def index():
            """Главная страница"""
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>JARVIS</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        color: #fff;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        text-align: center;
                        padding: 40px 20px;
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 15px;
                        margin-bottom: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    .logo {
                        font-size: 48px;
                        margin-bottom: 10px;
                    }
                    .subtitle {
                        color: #a0a0c0;
                        font-size: 18px;
                    }
                    .dashboard {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }
                    .card {
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 10px;
                        padding: 20px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        transition: transform 0.3s, border-color 0.3s;
                    }
                    .card:hover {
                        transform: translateY(-5px);
                        border-color: rgba(100, 150, 255, 0.3);
                    }
                    .card-title {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        margin-bottom: 15px;
                        font-size: 20px;
                    }
                    .stat-grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 15px;
                    }
                    .stat-item {
                        text-align: center;
                    }
                    .stat-value {
                        font-size: 24px;
                        font-weight: bold;
                        color: #64ffda;
                    }
                    .stat-label {
                        font-size: 12px;
                        color: #a0a0c0;
                        text-transform: uppercase;
                    }
                    .progress-bar {
                        height: 8px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                        margin: 10px 0;
                        overflow: hidden;
                    }
                    .progress-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #64ffda, #00b4d8);
                        border-radius: 4px;
                        transition: width 0.5s;
                    }
                    .file-list {
                        max-height: 300px;
                        overflow-y: auto;
                    }
                    .file-item {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        padding: 10px;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        transition: background 0.2s;
                    }
                    .file-item:hover {
                        background: rgba(255, 255, 255, 0.05);
                    }
                    .file-icon {
                        font-size: 20px;
                    }
                    .file-name {
                        flex: 1;
                    }
                    .file-size {
                        color: #a0a0c0;
                        font-size: 12px;
                    }
                    .btn {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: 500;
                        transition: transform 0.2s, box-shadow 0.2s;
                        text-decoration: none;
                        display: inline-block;
                    }
                    .btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                    }
                    .footer {
                        text-align: center;
                        margin-top: 40px;
                        color: #a0a0c0;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🤖 JARVIS</div>
                        <h1>Модульный Ассистент</h1>
                        <p class="subtitle">Файловый менеджер + AI помощник + Мониторинг системы</p>
                    </div>
                    
                    <div class="dashboard">
                        <!-- Системная статистика -->
                        <div class="card" id="stats-card">
                            <div class="card-title">📊 Статистика системы</div>
                            <div class="stat-grid" id="system-stats">
                                <div class="stat-item">
                                    <div class="stat-value" id="cpu-usage">0%</div>
                                    <div class="stat-label">ЦП</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" id="cpu-bar" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="ram-usage">0%</div>
                                    <div class="stat-label">Память</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" id="ram-bar" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="disk-usage">0%</div>
                                    <div class="stat-label">Диск</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" id="disk-bar" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="process-count">0</div>
                                    <div class="stat-label">Процессы</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Файловый менеджер -->
                        <div class="card">
                            <div class="card-title">📁 Файловый менеджер</div>
                            <div id="current-path" style="color: #a0a0c0; margin-bottom: 10px; font-size: 14px;">Загрузка...</div>
                            <div class="file-list" id="file-list">
                                <!-- Файлы будут здесь -->
                            </div>
                            <div style="margin-top: 15px;">
                                <button class="btn" onclick="loadFiles()">🔄 Обновить</button>
                            </div>
                        </div>
                        
                        <!-- Плагины -->
                        <div class="card">
                            <div class="card-title">🧩 Плагины</div>
                            <div id="plugins-list">
                                <!-- Плагины будут здесь -->
                            </div>
                        </div>
                        
                        <!-- AI Assistant -->
                        <div class="card">
                            <div class="card-title">🤖 AI Помощник</div>
                            <p style="color: #a0a0c0; margin-bottom: 15px;">Задайте вопрос системе</p>
                            <div style="margin-bottom: 15px;">
                                <input type="text" id="ai-question" placeholder="Введите вопрос..." 
                                       style="width: 100%; padding: 10px; border-radius: 5px; 
                                              border: 1px solid rgba(255, 255, 255, 0.2); 
                                              background: rgba(255, 255, 255, 0.05); 
                                              color: white;">
                            </div>
                            <button class="btn" onclick="askAI()">📨 Спросить</button>
                            <div id="ai-response" style="margin-top: 15px; padding: 10px; 
                                                        background: rgba(255, 255, 255, 0.05); 
                                                        border-radius: 5px; display: none;">
                            </div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="/api/files" class="btn" style="margin-right: 10px;">📂 API Файлов</a>
                        <a href="/api/system/stats" class="btn" style="margin-right: 10px;">📊 API Статистики</a>
                        <a href="/api/plugins" class="btn">🧩 API Плагинов</a>
                    </div>
                    
                    <div class="footer">
                        <p>JARVIS v0.2.0 | Модульный ассистент с открытым исходным кодом</p>
                        <p>💻 Текущая папка: <span id="current-folder">Загрузка...</span></p>
                    </div>
                </div>
                
                <script>
                    // Загрузка системной статистики
                    async function loadStats() {
                        try {
                            const response = await fetch('/api/system/stats');
                            const data = await response.json();
                            
                            if (data.cpu && data.cpu.percent) {
                                document.getElementById('cpu-usage').textContent = data.cpu.percent.toFixed(1) + '%';
                                document.getElementById('cpu-bar').style.width = data.cpu.percent + '%';
                            }
                            
                            if (data.memory && data.memory.percent) {
                                document.getElementById('ram-usage').textContent = data.memory.percent.toFixed(1) + '%';
                                document.getElementById('ram-bar').style.width = data.memory.percent + '%';
                            }
                            
                            if (data.disk && data.disk.percent) {
                                document.getElementById('disk-usage').textContent = data.disk.percent.toFixed(1) + '%';
                                document.getElementById('disk-bar').style.width = data.disk.percent + '%';
                            }
                            
                            if (data.system && data.system.process_count) {
                                document.getElementById('process-count').textContent = data.system.process_count;
                            }
                        } catch (error) {
                            console.error('Ошибка загрузки статистики:', error);
                        }
                    }
                    
                    // Загрузка файлов
                    async function loadFiles() {
                        try {
                            const response = await fetch('/api/files');
                            const data = await response.json();
                            
                            if (data.path) {
                                document.getElementById('current-path').textContent = data.path;
                                document.getElementById('current-folder').textContent = data.path;
                            }
                            
                            if (data.items) {
                                const fileList = document.getElementById('file-list');
                                fileList.innerHTML = '';
                                
                                data.items.slice(0, 10).forEach(item => {
                                    const icon = item.is_dir ? '📁' : '📄';
                                    const size = item.size_human || '';
                                    
                                    const fileItem = document.createElement('div');
                                    fileItem.className = 'file-item';
                                    fileItem.innerHTML = `
                                        <div class="file-icon">${icon}</div>
                                        <div class="file-name">${item.name}</div>
                                        <div class="file-size">${size}</div>
                                    `;
                                    fileList.appendChild(fileItem);
                                });
                                
                                if (data.items.length > 10) {
                                    const moreItem = document.createElement('div');
                                    moreItem.className = 'file-item';
                                    moreItem.innerHTML = `<div style="color: #a0a0c0;">... и ещё ${data.items.length - 10} файлов</div>`;
                                    fileList.appendChild(moreItem);
                                }
                            }
                        } catch (error) {
                            console.error('Ошибка загрузки файлов:', error);
                            document.getElementById('file-list').innerHTML = '<div style="color: #ff6b6b;">Ошибка загрузки файлов</div>';
                        }
                    }
                    
                    // Загрузка плагинов
                    async function loadPlugins() {
                        try {
                            const response = await fetch('/api/plugins');
                            const data = await response.json();
                            
                            const pluginsList = document.getElementById('plugins-list');
                            pluginsList.innerHTML = '';
                            
                            if (data.plugins) {
                                Object.entries(data.plugins).forEach(([name, info]) => {
                                    const pluginItem = document.createElement('div');
                                    pluginItem.className = 'file-item';
                                    pluginItem.innerHTML = `
                                        <div>🧩</div>
                                        <div style="flex: 1;">
                                            <div><strong>${name}</strong></div>
                                            <div style="font-size: 12px; color: #a0a0c0;">${info.description || 'Нет описания'}</div>
                                        </div>
                                        <div style="color: #64ffda;">${info.status === 'active' ? '✅' : '⏸️'}</div>
                                    `;
                                    pluginsList.appendChild(pluginItem);
                                });
                            }
                        } catch (error) {
                            console.error('Ошибка загрузки плагинов:', error);
                        }
                    }
                    
                    // Вопрос к AI
                    async function askAI() {
                        const question = document.getElementById('ai-question').value;
                        if (!question.trim()) return;
                        
                        const responseDiv = document.getElementById('ai-response');
                        responseDiv.style.display = 'block';
                        responseDiv.innerHTML = '<div style="color: #a0a0c0;">🤔 Думаю...</div>';
                        
                        try {
                            // Здесь будет запрос к AI плагину
                            // Пока просто демо-ответ
                            setTimeout(() => {
                                responseDiv.innerHTML = `
                                    <div style="color: #64ffda;">🤖 JARVIS AI:</div>
                                    <div style="margin-top: 5px;">Вы спросили: "${question}"</div>
                                    <div style="margin-top: 10px; color: #a0a0c0;">
                                        AI Assistant будет доступен после загрузки соответствующего плагина.
                                        Сейчас я могу помочь с файлами и системной информацией.
                                    </div>
                                `;
                            }, 1000);
                            
                        } catch (error) {
                            responseDiv.innerHTML = `<div style="color: #ff6b6b;">❌ Ошибка: ${error}</div>`;
                        }
                    }
                    
                    // Автоматическое обновление
                    function startAutoRefresh() {
                        // Обновляем статистику каждые 3 секунды
                        setInterval(loadStats, 3000);
                        
                        // Обновляем файлы каждые 10 секунд
                        setInterval(loadFiles, 10000);
                        
                        // Обновляем плагины каждые 30 секунд
                        setInterval(loadPlugins, 30000);
                    }
                    
                    // Инициализация при загрузке
                    document.addEventListener('DOMContentLoaded', function() {
                        loadStats();
                        loadFiles();
                        loadPlugins();
                        startAutoRefresh();
                    });
                </script>
            </body>
            </html>
            ''')
        
        # API маршруты
        @self.app.route('/api/files', methods=['GET'])
        def get_files():
            """Получить список файлов"""
            path = request.args.get('path', None)
            result = self.file_explorer.list_directory(path)
            return jsonify(result)
        
        @self.app.route('/api/files/<path:filepath>', methods=['GET'])
        def get_file_info(filepath):
            """Информация о файле"""
            result = self.file_explorer.get_file_info(filepath)
            return jsonify(result)
        
        @self.app.route('/api/system/stats', methods=['GET'])
        def system_stats():
            """Статистика системы"""
            plugin = self.kernel.get_plugin('system_monitor')
            if plugin:
                return jsonify(plugin.get_system_stats())
            return jsonify({"error": "Плагин мониторинга не загружен"}), 503
        
        @self.app.route('/api/plugins', methods=['GET'])
        def list_plugins():
            """Список плагинов"""
            plugins = self.kernel.list_plugins()
            return jsonify({"plugins": plugins})
        
        @self.app.route('/api/plugins/<plugin_name>/load', methods=['POST'])
        def load_plugin(plugin_name):
            """Загрузить плагин"""
            success = self.kernel.load_plugin(plugin_name)
            return jsonify({"success": success, "plugin": plugin_name})
        
        @self.app.route('/api/plugins/<plugin_name>/unload', methods=['POST'])
        def unload_plugin(plugin_name):
            """Выгрузить плагин"""
            success = self.kernel.unload_plugin(plugin_name)
            return jsonify({"success": success, "plugin": plugin_name})
    
    def run(self, debug=False):
        """Запуск веб-сервера"""
        print(f"🌐 Веб-интерфейс: http://{self.host}:{self.port}")
        print(f"📁 API доступен по: http://{self.host}:{self.port}/api/files")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)
    
    def run_in_thread(self):
        """Запуск в отдельном потоке"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread