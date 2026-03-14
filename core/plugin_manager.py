"""
Расширенный менеджер плагинов с поддержкой магазина
"""

import importlib
import json
import zipfile
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib
from datetime import datetime
import sys

@dataclass
class PluginMetadata:
    """Метаданные плагина"""
    name: str
    version: str
    description: str
    author: str
    license: str
    dependencies: List[str]
    min_jarvis_version: str
    tags: List[str]
    repository: str = ""
    icon: str = ""
    screenshot: str = ""
    readme: str = ""

class PluginManager:
    """Расширенный менеджер плагинов с магазином"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.plugins_dir = Path("plugins")
        self.installed_plugins: Dict[str, Dict] = {}
        self.plugin_store_url = "https://raw.githubusercontent.com/jarvis-plugins/store/main/"
        self.local_store_path = Path("data/plugin_store.json")
        
        self._load_installed_plugins()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создание необходимых директорий"""
        directories = [
            "plugins/disabled",
            "data/plugins",
            "data/plugins/cache",
            "data/plugins/backups"
        ]
        
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _load_installed_plugins(self):
        """Загрузка информации об установленных плагинах"""
        self.installed_plugins = {}
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir.name != "disabled":
                manifest_path = plugin_dir / "plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            self.installed_plugins[plugin_dir.name] = {
                                "manifest": manifest,
                                "path": str(plugin_dir),
                                "enabled": True,
                                "loaded": plugin_dir.name in self.kernel.plugins
                            }
                    except Exception as e:
                        self.kernel.logger.error(f"Error loading plugin manifest {plugin_dir.name}: {e}")
    
    def install_from_url(self, url: str) -> Dict[str, Any]:
        """Установка плагина из URL"""
        try:
            # Скачивание плагина
            self.kernel.logger.info(f"Downloading plugin from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем временный файл
            temp_file = Path("data/plugins/temp_plugin.zip")
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Устанавливаем из ZIP
            return self.install_from_zip(temp_file)
            
        except Exception as e:
            return {"success": False, "error": f"Download failed: {e}"}
    
    def install_from_zip(self, zip_path: Path) -> Dict[str, Any]:
        """Установка плагина из ZIP архива"""
        try:
            # Временная директория для распаковки
            temp_dir = Path("data/plugins/temp_extract")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True)
            
            # Распаковка
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Ищем manifest
            manifest_files = list(temp_dir.rglob("plugin.json"))
            if not manifest_files:
                # Ищем в корне
                manifest_files = list(temp_dir.glob("plugin.json"))
            
            if not manifest_files:
                return {"success": False, "error": "No plugin.json found"}
            
            manifest_path = manifest_files[0]
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            plugin_name = manifest.get("name", "unknown")
            plugin_version = manifest.get("version", "1.0.0")
            
            # Проверяем зависимости
            dependencies = manifest.get("dependencies", [])
            for dep in dependencies:
                if not self._check_dependency(dep):
                    return {"success": False, "error": f"Dependency not met: {dep}"}
            
            # Целевая директория для плагина
            target_dir = self.plugins_dir / plugin_name
            
            # Делаем бэкап старой версии если есть
            if target_dir.exists():
                backup_dir = Path(f"data/plugins/backups/{plugin_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.move(target_dir, backup_dir)
                self.kernel.logger.info(f"Backup created at {backup_dir}")
            
            # Копируем плагин
            shutil.copytree(manifest_path.parent, target_dir)
            
            # Устанавливаем зависимости
            requirements_file = target_dir / "requirements.txt"
            if requirements_file.exists():
                self._install_dependencies(requirements_file)
            
            # Обновляем список плагинов
            self._load_installed_plugins()
            
            return {
                "success": True,
                "plugin": plugin_name,
                "version": plugin_version,
                "message": f"Plugin {plugin_name} v{plugin_version} installed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Installation failed: {e}"}
        finally:
            # Очистка временных файлов
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if zip_path.exists():
                zip_path.unlink(missing_ok=True)
    
    def _check_dependency(self, dependency: str) -> bool:
        """Проверка зависимости"""
        # Формат: "plugin_name>=1.0.0" или "package>=1.0.0"
        if ">=" in dependency:
            name, version = dependency.split(">=")
        elif "==" in dependency:
            name, version = dependency.split("==")
        else:
            name, version = dependency, "0.0.0"
        
        # Проверяем плагины
        if name in self.installed_plugins:
            plugin_version = self.installed_plugins[name]["manifest"].get("version", "0.0.0")
            return self._compare_versions(plugin_version, version) >= 0
        
        # Проверяем Python пакеты
        try:
            import importlib.metadata
            pkg_version = importlib.metadata.version(name)
            return self._compare_versions(pkg_version, version) >= 0
        except:
            return False
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Сравнение версий"""
        import re
        
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
        
        v1_norm = normalize(v1)
        v2_norm = normalize(v2)
        
        if v1_norm < v2_norm:
            return -1
        elif v1_norm > v2_norm:
            return 1
        return 0
    
    def _install_dependencies(self, requirements_file: Path):
        """Установка зависимостей из requirements.txt"""
        try:
            import subprocess
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file)
            ], check=True)
        except Exception as e:
            self.kernel.logger.warning(f"Failed to install some dependencies: {e}")
    
    def uninstall_plugin(self, plugin_name: str, keep_data: bool = False) -> Dict[str, Any]:
        """Удаление плагина"""
        if plugin_name not in self.installed_plugins:
            return {"success": False, "error": f"Plugin {plugin_name} not found"}
        
        try:
            plugin_path = Path(self.installed_plugins[plugin_name]["path"])
            
            # Выгружаем если загружен
            if self.installed_plugins[plugin_name]["loaded"]:
                self.kernel.unload_plugin(plugin_name)
            
            # Делаем бэкап
            backup_dir = Path(f"data/plugins/backups/{plugin_name}_uninstalled_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            if keep_data:
                # Сохраняем data директорию если есть
                data_dir = plugin_path / "data"
                if data_dir.exists():
                    backup_data_dir = backup_dir / "data"
                    backup_data_dir.mkdir(parents=True)
                    shutil.copytree(data_dir, backup_data_dir, dirs_exist_ok=True)
            
            # Копируем плагин в бэкап
            shutil.copytree(plugin_path, backup_dir)
            
            # Удаляем плагин
            shutil.rmtree(plugin_path)
            
            # Обновляем список
            del self.installed_plugins[plugin_name]
            
            return {
                "success": True,
                "plugin": plugin_name,
                "backup_path": str(backup_dir),
                "message": f"Plugin {plugin_name} uninstalled"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Uninstall failed: {e}"}
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Включение плагина"""
        if plugin_name not in self.installed_plugins:
            return False
        
        disabled_dir = self.plugins_dir / "disabled" / plugin_name
        enabled_dir = self.plugins_dir / plugin_name
        
        if disabled_dir.exists():
            shutil.move(disabled_dir, enabled_dir)
            self.installed_plugins[plugin_name]["enabled"] = True
            return True
        
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Отключение плагина"""
        if plugin_name not in self.installed_plugins:
            return False
        
        # Выгружаем если загружен
        if self.installed_plugins[plugin_name]["loaded"]:
            self.kernel.unload_plugin(plugin_name)
        
        enabled_dir = self.plugins_dir / plugin_name
        disabled_dir = self.plugins_dir / "disabled" / plugin_name
        
        if enabled_dir.exists():
            disabled_dir.parent.mkdir(exist_ok=True)
            shutil.move(enabled_dir, disabled_dir)
            self.installed_plugins[plugin_name]["enabled"] = False
            return True
        
        return False
    
    def update_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Обновление плагина"""
        if plugin_name not in self.installed_plugins:
            return {"success": False, "error": f"Plugin {plugin_name} not found"}
        
        manifest = self.installed_plugins[plugin_name]["manifest"]
        repository = manifest.get("repository", "")
        
        if not repository:
            return {"success": False, "error": "No repository URL in manifest"}
        
        # Проверяем наличие новой версии
        try:
            response = requests.get(repository.replace("github.com", "raw.githubusercontent.com") + "/main/plugin.json")
            if response.status_code == 200:
                new_manifest = response.json()
                current_version = manifest.get("version", "0.0.0")
                new_version = new_manifest.get("version", "0.0.0")
                
                if self._compare_versions(new_version, current_version) > 0:
                    # Есть обновление
                    download_url = new_manifest.get("download_url", repository + "/archive/main.zip")
                    return self.install_from_url(download_url)
                else:
                    return {"success": True, "message": "Plugin is up to date", "current_version": current_version}
            else:
                return {"success": False, "error": f"Cannot fetch plugin info: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Update check failed: {e}"}
    
    def fetch_store_plugins(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получение списка плагинов из магазина"""
        # Проверяем кеш
        if not force_refresh and self.local_store_path.exists():
            cache_age = datetime.now().timestamp() - self.local_store_path.stat().st_mtime
            if cache_age < 3600:  # 1 час
                try:
                    with open(self.local_store_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        try:
            # Загружаем из удаленного источника
            store_url = self.plugin_store_url + "plugins.json"
            response = requests.get(store_url, timeout=10)
            response.raise_for_status()
            plugins = response.json()
            
            # Сохраняем в кеш
            with open(self.local_store_path, 'w', encoding='utf-8') as f:
                json.dump(plugins, f, indent=2, ensure_ascii=False)
            
            return plugins
            
        except Exception as e:
            self.kernel.logger.error(f"Failed to fetch plugin store: {e}")
            # Возвращаем пустой список или закешированный
            if self.local_store_path.exists():
                try:
                    with open(self.local_store_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
            return []
    
    def search_store(self, query: str, category: str = "") -> List[Dict[str, Any]]:
        """Поиск плагинов в магазине"""
        plugins = self.fetch_store_plugins()
        query_lower = query.lower()
        
        results = []
        for plugin in plugins:
            # Поиск по названию и описанию
            if (query_lower in plugin.get("name", "").lower() or
                query_lower in plugin.get("description", "").lower() or
                query_lower in " ".join(plugin.get("tags", [])).lower()):
                
                # Фильтр по категории
                if category and category not in plugin.get("categories", []):
                    continue
                
                # Добавляем информацию об установке
                plugin["installed"] = plugin["name"] in self.installed_plugins
                if plugin["installed"]:
                    installed_info = self.installed_plugins[plugin["name"]]
                    plugin["installed_version"] = installed_info["manifest"].get("version", "unknown")
                    plugin["update_available"] = self._compare_versions(
                        plugin.get("version", "0.0.0"),
                        plugin["installed_version"]
                    ) > 0
                
                results.append(plugin)
        
        return results
    
    def create_plugin_template(self, plugin_name: str, author: str = "User") -> Dict[str, Any]:
        """Создание шаблона для нового плагина"""
        plugin_dir = self.plugins_dir / plugin_name
        if plugin_dir.exists():
            return {"success": False, "error": f"Plugin {plugin_name} already exists"}
        
        try:
            plugin_dir.mkdir(parents=True)
            
            # Создаем manifest
            manifest = {
                "name": plugin_name,
                "version": "1.0.0",
                "description": f"A custom plugin for JARVIS",
                "author": author,
                "license": "MIT",
                "dependencies": [],
                "min_jarvis_version": "0.1.0",
                "tags": ["custom", "utility"],
                "repository": "",
                "icon": "icon.png",
                "readme": "README.md"
            }
            
            with open(plugin_dir / "plugin.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Создаем основной файл
            main_py = plugin_dir / "main.py"
            with open(main_py, 'w', encoding='utf-8') as f:
                f.write(f'''"""
{plugin_name} - Custom plugin for JARVIS
"""

class Plugin:
    """{plugin_name} plugin for JARVIS"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.name = "{plugin_name}"
        self.version = "1.0.0"
        self.description = "A custom plugin for JARVIS"
        
    def on_load(self):
        """Called when plugin is loaded"""
        self.kernel.logger.info(f"{{self.name}} plugin loaded")
        
    def on_unload(self):
        """Called when plugin is unloaded"""
        self.kernel.logger.info(f"{{self.name}} plugin unloaded")
        
    def handle_event(self, event_name, data):
        """Handle events from kernel"""
        pass
''')
            
            # Создаем README
            readme = plugin_dir / "README.md"
            with open(readme, 'w', encoding='utf-8') as f:
                f.write(f"""# {plugin_name}

A custom plugin for JARVIS Modular Assistant.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

1. Copy this folder to `plugins/{plugin_name}/`
2. Restart JARVIS or load the plugin from Plugin Manager

## Configuration

Add configuration to `config/{plugin_name}.json`:

```json
{{
  "setting1": "value1",
  "setting2": true
}}