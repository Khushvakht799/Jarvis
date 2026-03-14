#!/usr/bin/env python3
"""
JARVIS - Modular Assistant and File Manager
Main entry point
"""

import sys
import json
import signal
import threading
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Проверка и настройка окружения"""
    print("🔧 Setting up environment...")
    
    # Проверяем наличие необходимых папок
    required_dirs = ["core", "plugins", "config", "logs", "data"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"  Creating directory: {dir_name}")
            dir_path.mkdir(exist_ok=True)
    
    # Проверяем наличие конфигурации
    config_path = Path("config/settings.json")
    if not config_path.exists():
        print("  Creating default configuration...")
        default_config = {
            "name": "Jarvis",
            "version": "0.1.0",
            "core": {
                "autostart_plugins": ["system_monitor"],
                "log_level": "INFO",
                "theme": "dark"
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
    
    print("✓ Environment ready")

def main():
    """Основная функция запуска Jarvis"""
    print("""
    ╔══════════════════════════════════════════╗
    ║            🚀 JARVIS v0.1.0              ║
    ║   Modular Assistant & File Manager       ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Настройка окружения
    setup_environment()
    
    # Динамический импорт после настройки путей
    try:
        from core.kernel import JarvisKernel
        from core.file_explorer import FileExplorer
    except ImportError as e:
        print(f"❌ Failed to import core modules: {e}")
        print("Make sure all core files exist in the 'core' directory")
        return 1
    
    # Инициализация ядра
    print("\n🔄 Initializing kernel...")
    try:
        kernel = JarvisKernel()
        
        # Инициализация файлового менеджера
        file_explorer = FileExplorer(kernel)
        kernel.plugins["file_explorer"] = file_explorer
        
        print(f"✓ Kernel initialized")
        print(f"✓ File explorer ready")
        print(f"✓ Current path: {file_explorer.current_path}")
        
        # Загрузка плагинов из конфига
        autostart_plugins = kernel.config.get('core', {}).get('autostart_plugins', [])
        print(f"\n🔌 Loading plugins ({len(autostart_plugins)}):")
        
        for plugin_name in autostart_plugins:
            print(f"  • {plugin_name}: ", end="", flush=True)
            if kernel.load_plugin(plugin_name):
                print("✓")
            else:
                print("✗")
        
        # Обработка сигналов для корректного завершения
        def signal_handler(sig, frame):
            print(f"\n🛑 Received signal {sig}, shutting down...")
            kernel.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запуск интерфейса
        print("\n" + "="*60)
        print("JARVIS is running! Choose interface:")
        print("  1. Web Interface (http://localhost:8080)")
        print("  2. Terminal UI (Textual)")
        print("  3. CLI Interface")
        print("  4. Exit")
        print("="*60)
        
        while True:
            try:
                choice = input("\nSelect option (1-4): ").strip()
                
                if choice == "1":
                    launch_web_interface(kernel, file_explorer)
                elif choice == "2":
                    launch_tui_interface(kernel, file_explorer)
                elif choice == "3":
                    launch_cli_interface(kernel, file_explorer)
                elif choice == "4":
                    print("Shutting down...")
                    kernel.shutdown()
                    break
                else:
                    print("Invalid choice. Please select 1-4")
                    
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                kernel.shutdown()
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to initialize Jarvis: {e}")
        import traceback
        traceback.print_exc()
        return 1

def launch_web_interface(kernel, file_explorer):
    """Запуск веб-интерфейса"""
    print("\n🌐 Starting web interface...")
    
    # Создаём простой веб-сервер для демонстрации
    from flask import Flask, jsonify, render_template_string
    import threading
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>JARVIS Web Interface</title>
            <style>
                body { font-family: Arial; margin: 20px; background: #1a1a1a; color: #fff; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: #2d2d2d; padding: 20px; border-radius: 8px; }
                .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }
                .stat-card { background: #2d2d2d; padding: 15px; border-radius: 8px; }
                .file-list { background: #2d2d2d; padding: 15px; border-radius: 8px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ JARVIS Web Interface</h1>
                    <p>Modular Assistant & File Manager</p>
                </div>
                <div id="stats" class="stats">
                    <!-- Stats will be loaded by JavaScript -->
                </div>
                <div class="file-list">
                    <h3>File Explorer</h3>
                    <div id="files">
                        <!-- Files will be loaded here -->
                    </div>
                </div>
            </div>
            <script>
                async function loadStats() {
                    const res = await fetch('/api/stats');
                    const data = await res.json();
                    
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <h4>CPU</h4>
                            <p>${data.cpu.percent.toFixed(1)}%</p>
                        </div>
                        <div class="stat-card">
                            <h4>Memory</h4>
                            <p>${data.memory.percent.toFixed(1)}%</p>
                        </div>
                        <div class="stat-card">
                            <h4>Disk</h4>
                            <p>${data.disk.percent.toFixed(1)}%</p>
                        </div>
                        <div class="stat-card">
                            <h4>Processes</h4>
                            <p>${data.system.process_count}</p>
                        </div>
                    `;
                }
                
                async function loadFiles() {
                    const res = await fetch('/api/files');
                    const data = await res.json();
                    
                    let html = '<ul>';
                    data.items.forEach(item => {
                        const icon = item.is_dir ? '📁' : '📄';
                        html += `<li>${icon} ${item.name} (${item.size_human || 'dir'})</li>`;
                    });
                    html += '</ul>';
                    
                    document.getElementById('files').innerHTML = html;
                }
                
                // Загружаем данные при старте
                loadStats();
                loadFiles();
                
                // Обновляем каждые 5 секунд
                setInterval(loadStats, 5000);
                setInterval(loadFiles, 10000);
            </script>
        </body>
        </html>
        ''')
    
    @app.route('/api/stats')
    def api_stats():
        # Получаем статистику через плагин system_monitor
        plugin = kernel.get_plugin('system_monitor')
        if plugin:
            return jsonify(plugin.get_system_stats())
        return jsonify({"error": "System monitor not available"})
    
    @app.route('/api/files')
    def api_files():
        return jsonify(file_explorer.list_directory())
    
    def run_flask():
        app.run(host='localhost', port=8080, debug=False, use_reloader=False)
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("✅ Web interface started at: http://localhost:8080")
    print("Press Ctrl+C to stop...")
    
    try:
        # Держим основной поток активным
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping web interface...")

def launch_tui_interface(kernel, file_explorer):
    """Запуск TUI интерфейса на Textual"""
    print("\n📟 Starting Terminal UI...")
    print("(TUI interface will be implemented in next patch)")
    
    # Заглушка для TUI
    print("\nAvailable commands:")
    print("  ls [path]     - List directory")
    print("  cd <path>     - Change directory")
    print("  search <query>- Quick search")
    print("  plugins       - List loaded plugins")
    print("  stats         - System statistics")
    print("  exit          - Return to menu")
    
    while True:
        try:
            cmd = input("\nTUI> ").strip().lower()
            
            if cmd in ['exit', 'quit', 'back']:
                break
            elif cmd.startswith('ls'):
                parts = cmd.split()
                path = parts[1] if len(parts) > 1 else None
                result = file_explorer.list_directory(path)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"\n📂 Directory: {result['path']}")
                    print("-" * 60)
                    for item in result['items'][:20]:  # Показываем первые 20
                        icon = "📁" if item['is_dir'] else "📄"
                        size = item['size_human'] if item['size_human'] else ""
                        print(f"{icon} {item['name']:<40} {size:>15}")
                    if len(result['items']) > 20:
                        print(f"... and {len(result['items']) - 20} more")
            
            elif cmd.startswith('cd '):
                path = cmd[3:].strip()
                if file_explorer.navigate(path):
                    print(f"📂 Changed to: {file_explorer.current_path}")
                else:
                    print(f"❌ Path not found: {path}")
            
            elif cmd.startswith('search '):
                query = cmd[7:].strip()
                results = file_explorer.quick_search(query, max_results=10)
                print(f"\n🔍 Found {len(results)} results:")
                for r in results:
                    icon = "📁" if r['is_dir'] else "📄"
                    print(f"{icon} {r['name']} ({r['context']})")
            
            elif cmd == 'plugins':
                plugins = kernel.list_plugins()
                print(f"\n🔌 Loaded plugins ({len(plugins)}):")
                for name, info in plugins.items():
                    print(f"  • {name} - {info.get('description', 'No description')}")
            
            elif cmd == 'stats':
                plugin = kernel.get_plugin('system_monitor')
                if plugin:
                    stats = plugin.get_system_stats()
                    print(f"\n📊 System Statistics:")
                    print(f"  CPU: {stats['cpu']['percent']:.1f}%")
                    print(f"  Memory: {stats['memory']['percent']:.1f}% ({stats['memory']['used']//1024//1024} MB)")
                    print(f"  Disk: {stats['disk']['percent']:.1f}%")
                    print(f"  Processes: {stats['system']['process_count']}")
                    print(f"  Uptime: {stats['system']['uptime']:.0f} seconds")
                else:
                    print("System monitor plugin not loaded")
            
            elif cmd == 'help':
                print("\nAvailable commands:")
                print("  ls [path]     - List directory")
                print("  cd <path>     - Change directory")
                print("  search <query>- Quick search")
                print("  plugins       - List loaded plugins")
                print("  stats         - System statistics")
                print("  exit          - Return to menu")
            
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Error: {e}")

def launch_cli_interface(kernel, file_explorer):
    """Запуск CLI интерфейса"""
    print("\n💻 Starting CLI Interface...")
    print("Type 'help' for commands, 'exit' to return to menu")
    
    while True:
        try:
            command = input("\nJARVIS> ").strip().lower()
            
            if command == 'exit' or command == 'quit':
                print("Returning to main menu...")
                break
            
            elif command == 'help':
                print("""
Available commands:
  ls [path]     - List directory
  cd <path>     - Change directory
  search <query>- Quick search
  plugins       - List loaded plugins
  info          - System info
  stats         - Detailed system stats
  exit          - Return to main menu
                """)
            
            elif command.startswith('ls'):
                parts = command.split()
                path = parts[1] if len(parts) > 1 else None
                result = file_explorer.list_directory(path)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"\nDirectory: {result['path']}")
                    print("-" * 60)
                    for item in result['items'][:15]:  # Показываем первые 15
                        icon = "📁" if item['is_dir'] else "📄"
                        size = f"{item['size_human']}" if item['size_human'] else ""
                        print(f"{icon} {item['name']:<40} {size:>15}")
                    if len(result['items']) > 15:
                        print(f"... and {len(result['items']) - 15} more")
                    print(f"Total: {result['total']} items")
            
            elif command.startswith('cd '):
                path = command[3:].strip()
                if file_explorer.navigate(path):
                    print(f"Changed to: {file_explorer.current_path}")
                else:
                    print(f"Path not found: {path}")
            
            elif command.startswith('search '):
                query = command[7:].strip()
                results = file_explorer.quick_search(query)
                print(f"\nFound {len(results)} results:")
                for r in results[:10]:  # Показываем первые 10
                    icon = "📁" if r['is_dir'] else "📄"
                    print(f"{icon} {r['name']} ({r['context']})")
            
            elif command == 'plugins':
                plugins = kernel.list_plugins()
                print(f"\nLoaded plugins ({len(plugins)}):")
                for name, info in plugins.items():
                    print(f"  • {name} - {info.get('description', 'No description')}")
            
            elif command == 'stats':
                plugin = kernel.get_plugin('system_monitor')
                if plugin:
                    stats = plugin.get_system_stats()
                    print(f"\n📊 System Statistics:")
                    print(f"  CPU: {stats['cpu']['percent']:.1f}%")
                    print(f"  Memory: {stats['memory']['percent']:.1f}%")
                    print(f"  Disk: {stats['disk']['percent']:.1f}%")
                    print(f"  Processes: {stats['system']['process_count']}")
                else:
                    print("System monitor plugin not loaded")
            
            elif command == 'info':
                import platform
                print(f"\nSystem Information:")
                print(f"  OS: {platform.system()} {platform.release()}")
                print(f"  Python: {platform.python_version()}")
                print(f"  Processor: {platform.processor()}")
                print(f"  Architecture: {platform.architecture()[0]}")
            
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Error: {e}")
def launch_web_interface(kernel, file_explorer):
    """Запуск веб-интерфейса"""
    print("\n🌐 Запуск веб-интерфейса...")
    
    try:
        from ui.web.api import JarvisWebAPI
        
        # Получаем настройки из конфига
        port = kernel.config.get('ui', {}).get('web_port', 8080)
        host = kernel.config.get('ui', {}).get('web_host', 'localhost')
        
        # Создаём и запускаем API
        web_api = JarvisWebAPI(kernel, file_explorer, host, port)
        web_thread = web_api.run_in_thread()
        
        print(f"✅ Веб-интерфейс запущен: http://{host}:{port}")
        print("   📁 API файлов: /api/files")
        print("   📊 API статистики: /api/system/stats")
        print("   🧩 API плагинов: /api/plugins")
        
        # Пытаемся открыть в браузере
        import webbrowser
        try:
            webbrowser.open(f"http://{host}:{port}")
        except:
            pass
        
        return web_thread
        
    except ImportError as e:
        print(f"❌ Ошибка импорта модулей веб-интерфейса: {e}")
        print("   Установите Flask: pip install flask flask-cors")
        return None
    except Exception as e:
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")
        return None

# В функции main(), в меню выбора интерфейса добавляем:
# elif choice == "1":
#     web_thread = launch_web_interface(kernel, file_explorer)
#     if web_thread:
#         print("\nВеб-интерфейс работает в фоне. Нажмите Enter чтобы вернуться в меню...")
#         input()
if __name__ == "__main__":
    sys.exit(main())
