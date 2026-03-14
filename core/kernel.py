import importlib
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import sys

class JarvisKernel:
    """Ядро Jarvis - загрузчик модулей и шина событий"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.plugins: Dict[str, Any] = {}
        self.event_subscribers: Dict[str, list] = {}
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.running = True
        self.lock = threading.RLock()
        
    def _load_config(self, config_path: str) -> dict:
        """Загрузка конфигурации из JSON"""
        path = Path(config_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {"name": "Jarvis", "version": "0.1.0"}
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'jarvis.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('Jarvis')
    
    def subscribe_event(self, event_name: str, callback):
        """Подписка на событие"""
        with self.lock:
            if event_name not in self.event_subscribers:
                self.event_subscribers[event_name] = []
            self.event_subscribers[event_name].append(callback)
            self.logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe_event(self, event_name: str, callback):
        """Отписка от события"""
        with self.lock:
            if event_name in self.event_subscribers:
                if callback in self.event_subscribers[event_name]:
                    self.event_subscribers[event_name].remove(callback)
                    self.logger.debug(f"Unsubscribed from event: {event_name}")
    
    def emit_event(self, event_name: str, data=None):
        """Отправка события всем подписчикам"""
        with self.lock:
            if event_name in self.event_subscribers:
                for callback in self.event_subscribers[event_name]:
                    try:
                        callback(event_name, data)
                    except Exception as e:
                        self.logger.error(f"Error in event handler {event_name}: {e}")
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Динамическая загрузка плагина"""
        plugin_path = Path(f"plugins/{plugin_name}")
        if not plugin_path.exists():
            self.logger.error(f"Plugin directory not found: {plugin_name}")
            return False
            
        main_file = plugin_path / "main.py"
        if not main_file.exists():
            self.logger.error(f"Plugin main.py not found: {plugin_name}")
            return False
        
        try:
            # Простой и надежный способ импорта для Python 3.13
            import importlib.util
            import sys
            
            # Читаем содержимое файла как текст
            with open(main_file, 'r', encoding='utf-8') as f:
                plugin_code = f.read()
            
            # Создаем уникальное имя модуля
            module_name = f"plugins_{plugin_name}_main"
            
            # Создаем спецификацию
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            if spec is None:
                self.logger.error(f"Failed to create spec for {plugin_name}")
                return False
            
            # Создаем модуль
            module = importlib.util.module_from_spec(spec)
            
            # Выполняем код в контексте модуля
            exec(plugin_code, module.__dict__)
            
            # Добавляем в sys.modules
            sys.modules[module_name] = module
            
            # Проверяем наличие класса Plugin
            if not hasattr(module, 'Plugin'):
                self.logger.error(f"Plugin class 'Plugin' not found in {plugin_name}")
                return False
            
            # Создаем экземпляр плагина
            plugin_instance = module.Plugin(self)
            plugin_instance.name = plugin_name
            
            # Сохраняем плагин
            with self.lock:
                self.plugins[plugin_name] = plugin_instance
                print(f"  ✓ Плагин '{plugin_name}' загружен")
            
            # Инициализируем плагин
            try:
                if hasattr(plugin_instance, 'on_load'):
                    plugin_instance.on_load()
            except Exception as e:
                self.logger.error(f"Error in plugin {plugin_name}.on_load(): {e}")
            
            self.logger.info(f"Plugin '{plugin_name}' loaded successfully")
            return True
            
        except ImportError as e:
            self.logger.error(f"ImportError loading plugin '{plugin_name}': {e}")
            print(f"  ❌ ImportError: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            print(f"  ❌ Ошибка: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Выгрузка плагина"""
        with self.lock:
            if plugin_name not in self.plugins:
                return False
            
            plugin = self.plugins[plugin_name]
            try:
                if hasattr(plugin, 'on_unload'):
                    plugin.on_unload()
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            
            # Удаляем из списка плагинов
            del self.plugins[plugin_name]
            
            # Отписываем от событий
            for event_name in list(self.event_subscribers.keys()):
                self.event_subscribers[event_name] = [
                    cb for cb in self.event_subscribers[event_name] 
                    if not hasattr(cb, '__self__') or cb.__self__ != plugin
                ]
            
            self.logger.info(f"Plugin '{plugin_name}' unloaded")
            return True
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Получить экземпляр плагина"""
        with self.lock:
            return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, str]:
        """Список загруженных плагинов с их статусом"""
        result = {}
        with self.lock:
            for name, plugin in self.plugins.items():
                result[name] = {
                    "status": "active",
                    "version": getattr(plugin, 'version', 'unknown'),
                    "description": getattr(plugin, 'description', 'No description')
                }
        return result
    
    def shutdown(self):
        """Корректное завершение работы Jarvis"""
        self.logger.info("Initiating shutdown sequence...")
        self.running = False
        
        # Выгружаем все плагины
        plugin_names = list(self.plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)
        
        self.logger.info("Jarvis shutdown complete")
    
    def broadcast_message(self, message: str, level: str = "INFO"):
        """Отправка сообщения всем плагинам"""
        self.emit_event("broadcast_message", {
            "message": message,
            "level": level,
            "timestamp": logging._defaultFormatter.formatTime(logging.makeLogRecord({}))
        })