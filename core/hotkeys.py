"""
Менеджер горячих клавиш для Jarvis
"""

import keyboard
import json
from pathlib import Path
from typing import Dict, Callable, Any, List
import threading
import time

class HotkeyManager:
    """Управление глобальными горячими клавишами"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.hotkeys: Dict[str, Dict] = {}
        self.handlers: Dict[str, Callable] = {}
        self.config_path = Path("config/hotkeys.json")
        self.load_config()
        self.running = False
        self.listener = None
        
        # Стандартные горячие клавиши
        self.default_hotkeys = {
            "toggle_jarvis": {
                "description": "Показать/скрыть Jarvis",
                "default": "ctrl+shift+j",
                "enabled": True
            },
            "quick_search": {
                "description": "Быстрый поиск файлов",
                "default": "ctrl+shift+f",
                "enabled": True
            },
            "screenshot": {
                "description": "Сделать скриншот",
                "default": "ctrl+shift+s",
                "enabled": True
            },
            "clipboard_manager": {
                "description": "Менеджер буфера обмена",
                "default": "ctrl+shift+v",
                "enabled": True
            },
            "system_monitor": {
                "description": "Показать монитор системы",
                "default": "ctrl+shift+m",
                "enabled": True
            },
            "ai_assistant": {
                "description": "Открыть AI ассистента",
                "default": "ctrl+shift+a",
                "enabled": True
            }
        }
        
    def load_config(self):
        """Загрузка конфигурации горячих клавиш"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.hotkeys = json.load(f)
            except:
                self.hotkeys = self.default_hotkeys.copy()
        else:
            self.hotkeys = self.default_hotkeys.copy()
            self.save_config()
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.hotkeys, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.kernel.logger.error(f"Error saving hotkeys config: {e}")
    
    def register_hotkey(self, name: str, handler: Callable, hotkey: str = None):
        """Регистрация горячей клавиши"""
        if name not in self.hotkeys:
            self.hotkeys[name] = {
                "description": f"Custom hotkey: {name}",
                "default": hotkey or "",
                "enabled": True if hotkey else False
            }
        
        self.handlers[name] = handler
        
        if hotkey and self.hotkeys[name]["enabled"]:
            try:
                keyboard.add_hotkey(hotkey, handler)
                self.kernel.logger.info(f"Registered hotkey: {name} -> {hotkey}")
            except Exception as e:
                self.kernel.logger.error(f"Failed to register hotkey {name}: {e}")
    
    def unregister_hotkey(self, name: str):
        """Удаление горячей клавиши"""
        if name in self.handlers:
            del self.handlers[name]
        
        if name in self.hotkeys:
            # Невозможно удалить конкретный хоткей в библиотеке keyboard
            # без удаления всех, поэтому помечаем как отключенный
            self.hotkeys[name]["enabled"] = False
            self.save_config()
    
    def set_hotkey(self, name: str, hotkey: str, enable: bool = True):
        """Установка новой горячей клавиши"""
        if name in self.hotkeys:
            # Удаляем старую привязку
            old_hotkey = self.hotkeys[name].get("current", self.hotkeys[name]["default"])
            if old_hotkey:
                try:
                    keyboard.remove_hotkey(old_hotkey)
                except:
                    pass
            
            # Устанавливаем новую
            self.hotkeys[name]["current"] = hotkey
            self.hotkeys[name]["enabled"] = enable
            
            if enable and hotkey and name in self.handlers:
                try:
                    keyboard.add_hotkey(hotkey, self.handlers[name])
                    self.kernel.logger.info(f"Updated hotkey: {name} -> {hotkey}")
                except Exception as e:
                    self.kernel.logger.error(f"Failed to set hotkey {name}: {e}")
            
            self.save_config()
            return True
        return False
    
    def start(self):
        """Запуск менеджера горячих клавиш"""
        if self.running:
            return
        
        self.running = True
        
        # Регистрируем все включенные горячие клавиши
        for name, config in self.hotkeys.items():
            if config.get("enabled", False):
                hotkey = config.get("current", config.get("default", ""))
                if hotkey and name in self.handlers:
                    try:
                        keyboard.add_hotkey(hotkey, self.handlers[name])
                    except Exception as e:
                        self.kernel.logger.error(f"Failed to start hotkey {name}: {e}")
        
        self.kernel.logger.info("Hotkey manager started")
    
    def stop(self):
        """Остановка менеджера горячих клавиш"""
        self.running = False
        keyboard.unhook_all()
        self.kernel.logger.info("Hotkey manager stopped")
    
    def get_all_hotkeys(self) -> Dict[str, Dict]:
        """Получить все горячие клавиши"""
        return self.hotkeys.copy()

class QuickSearch:
    """Быстрый поиск по системе"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.file_explorer = kernel.plugins.get("file_explorer")
        self.search_index = {}
        self.indexing = False
        
    def quick_search_ui(self):
        """Показать UI быстрого поиска"""
        # В реальной реализации здесь был бы GUI
        # Для демонстрации используем консольный ввод
        import sys
        
        print("\n" + "="*60)
        print("JARVIS Quick Search")
        print("="*60)
        print("Type search query (or 'exit' to quit):")
        
        while True:
            try:
                query = input("\nSearch: ").strip()
                if query.lower() in ['exit', 'quit', '']:
                    break
                
                results = self.search(query)
                
                if results:
                    print(f"\nFound {len(results)} results:")
                    for i, result in enumerate(results[:10], 1):
                        icon = "📁" if result["is_dir"] else "📄"
                        print(f"{i:2}. {icon} {result['name']}")
                        print(f"    Path: {result['path']}")
                        if not result["is_dir"] and result.get("size_human"):
                            print(f"    Size: {result['size_human']}")
                        print()
                else:
                    print("No results found")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Search error: {e}")
    
    def search(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Поиск файлов"""
        if not self.file_explorer:
            return []
        
        results = []
        
        # 1. Поиск в текущей директории
        current_results = self.file_explorer.quick_search(query, max_results)
        results.extend(current_results)
        
        # 2. Поиск по индексу (если есть)
        if self.search_index:
            query_lower = query.lower()
            for path, metadata in self.search_index.items():
                if (query_lower in path.lower() or 
                    query_lower in metadata.get("name", "").lower()):
                    results.append({
                        "name": metadata.get("name", Path(path).name),
                        "path": path,
                        "is_dir": metadata.get("is_dir", False),
                        "size": metadata.get("size", 0),
                        "size_human": metadata.get("size_human", ""),
                        "score": 0.5  # Ниже приоритета чем прямые результаты
                    })
        
        # Убираем дубликаты
        seen = set()
        unique_results = []
        for r in results:
            if r["path"] not in seen:
                seen.add(r["path"])
                unique_results.append(r)
        
        # Сортируем по релевантности
        unique_results.sort(key=lambda x: self._calculate_relevance(x, query), reverse=True)
        
        return unique_results[:max_results]
    
    def _calculate_relevance(self, item: Dict[str, Any], query: str) -> float:
        """Расчёт релевантности результата поиска"""
        query_lower = query.lower()
        name_lower = item["name"].lower()
        path_lower = item["path"].lower()
        
        # Высший приоритет: точное совпадение имени
        if name_lower == query_lower:
            return 1.0
        
        # Высокий приоритет: имя начинается с запроса
        if name_lower.startswith(query_lower):
            return 0.9
        
        # Средний приоритет: запрос содержится в имени
        if query_lower in name_lower:
            return 0.8
        
        # Низкий приоритет: запрос в пути
        if query_lower in path_lower:
            return 0.5
        
        return 0.0
    
    def index_directory(self, path: str, recursive: bool = True):
        """Индексация директории для быстрого поиска"""
        if self.indexing:
            return
        
        self.indexing = True
        self.kernel.logger.info(f"Indexing directory: {path}")
        
        try:
            from pathlib import Path
            import os
            
            index_count = 0
            if recursive:
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        full_path = Path(root) / name
                        try:
                            stat = full_path.stat()
                            self.search_index[str(full_path)] = {
                                "name": name,
                                "is_dir": full_path.is_dir(),
                                "size": stat.st_size if not full_path.is_dir() else 0,
                                "size_human": self._human_readable_size(stat.st_size) if not full_path.is_dir() else "",
                                "modified": stat.st_mtime,
                                "indexed": time.time()
                            }
                            index_count += 1
                        except (PermissionError, OSError):
                            continue
            else:
                for item in Path(path).iterdir():
                    try:
                        stat = item.stat()
                        self.search_index[str(item)] = {
                            "name": item.name,
                            "is_dir": item.is_dir(),
                            "size": stat.st_size if not item.is_dir() else 0,
                            "size_human": self._human_readable_size(stat.st_size) if not item.is_dir() else "",
                            "modified": stat.st_mtime,
                            "indexed": time.time()
                        }
                        index_count += 1
                    except (PermissionError, OSError):
                        continue
            
            self.kernel.logger.info(f"Indexed {index_count} items")
            self.kernel.emit_event("search_index_updated", {
                "path": path,
                "count": index_count,
                "recursive": recursive
            })
            
        except Exception as e:
            self.kernel.logger.error(f"Indexing error: {e}")
        finally:
            self.indexing = False
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Конвертация размера в читаемый формат"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {units[i]}"
    
    def clear_index(self):
        """Очистка поискового индекса"""
        self.search_index.clear()
        self.kernel.logger.info("Search index cleared")