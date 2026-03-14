import os
import shutil
import stat
from pathlib import Path
from datetime import datetime
import mimetypes
from typing import List, Dict, Any, Optional
import fnmatch

class FileExplorer:
    """Масштазируемый файловый менеджер - ядро Jarvis"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.current_path = Path.home()
        self.clipboard = None
        self.clipboard_operation = None  # 'copy' или 'cut'
        self.view_mode = "details"  # list, grid, details, tree
        self.sort_by = "name"
        self.sort_reverse = False
        self.hidden_files = False
        self.mime = mimetypes.MimeTypes()
        
        # Кеш для быстрого доступа
        self._cache = {}
        self._cache_time = {}
        
    def _human_readable_size(self, size_bytes: int) -> str:
        """Конвертация размера в человекочитаемый формат"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {units[i]}"
    
    def _get_file_type(self, path: Path) -> str:
        """Определение типа файла по расширению"""
        if path.is_dir():
            return "Directory"
        
        ext = path.suffix.lower()
        type_map = {
            '.py': 'Python Script',
            '.js': 'JavaScript',
            '.html': 'HTML Document',
            '.css': 'Stylesheet',
            '.json': 'JSON File',
            '.txt': 'Text Document',
            '.md': 'Markdown',
            '.pdf': 'PDF Document',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.png': 'PNG Image',
            '.gif': 'GIF Image',
            '.mp4': 'MP4 Video',
            '.mp3': 'MP3 Audio',
            '.zip': 'ZIP Archive',
            '.rar': 'RAR Archive',
            '.exe': 'Executable',
            '.dll': 'Dynamic Library',
        }
        
        return type_map.get(ext, "File")
    
    def list_directory(self, path: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
        """Список содержимого директории с метаданными"""
        target_path = Path(path) if path else self.current_path
        
        if not target_path.exists():
            return {"error": f"Path does not exist: {target_path}"}
        
        if not target_path.is_dir():
            return {"error": f"Not a directory: {target_path}"}
        
        # Проверяем кеш (кешируем на 5 секунд для производительности)
        cache_key = str(target_path)
        if not refresh and cache_key in self._cache:
            if (datetime.now() - self._cache_time[cache_key]).seconds < 5:
                return self._cache[cache_key]
        
        items = []
        try:
            for item in target_path.iterdir():
                # Пропускаем скрытые файлы если не включены
                if not self.hidden_files and item.name.startswith('.'):
                    continue
                
                try:
                    stat_info = item.stat()
                    
                    item_data = {
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": stat_info.st_size if not item.is_dir() else 0,
                        "size_human": self._human_readable_size(stat_info.st_size) if not item.is_dir() else "",
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                        "extension": item.suffix.lower() if not item.is_dir() else "",
                        "type": self._get_file_type(item),
                        "permissions": oct(stat_info.st_mode)[-3:],
                        "hidden": item.name.startswith('.'),
                        "readable": os.access(item, os.R_OK),
                        "writable": os.access(item, os.W_OK),
                        "executable": os.access(item, os.X_OK),
                        "inode": stat_info.st_ino
                    }
                    
                    # Определяем MIME тип
                    if not item.is_dir():
                        mime_type, _ = mimetypes.guess_type(str(item))
                        item_data["mime_type"] = mime_type or "application/octet-stream"
                    
                    items.append(item_data)
                    
                except (PermissionError, OSError) as e:
                    # Добавляем информацию даже для недоступных файлов
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "error": str(e),
                        "readable": False,
                        "writable": False
                    })
                    
        except PermissionError as e:
            return {"error": f"Permission denied: {e}"}
        
        # Сортировка
        if self.sort_by == "name":
            items.sort(key=lambda x: x["name"].lower(), reverse=self.sort_reverse)
        elif self.sort_by == "size":
            items.sort(key=lambda x: x["size"], reverse=not self.sort_reverse)
        elif self.sort_by == "modified":
            items.sort(key=lambda x: x["modified"], reverse=not self.sort_reverse)
        elif self.sort_by == "type":
            items.sort(key=lambda x: (x["is_dir"], x["type"], x["name"].lower()), 
                      reverse=self.sort_reverse)
        
        result = {
            "path": str(target_path),
            "items": items,
            "total": len(items),
            "parent": str(target_path.parent) if target_path.parent != target_path else None,
            "free_space": self.get_free_space(target_path),
            "timestamp": datetime.now().isoformat()
        }
        
        # Кешируем результат
        self._cache[cache_key] = result
        self._cache_time[cache_key] = datetime.now()
        
        return result
    
    def get_free_space(self, path: Path) -> Dict[str, Any]:
        """Получение информации о свободном месте на диске"""
        try:
            import shutil
            usage = shutil.disk_usage(path)
            return {
                "total": usage.total,
                "total_human": self._human_readable_size(usage.total),
                "used": usage.used,
                "used_human": self._human_readable_size(usage.used),
                "free": usage.free,
                "free_human": self._human_readable_size(usage.free),
                "percent_used": (usage.used / usage.total) * 100
            }
        except:
            return {}
    
    def navigate(self, path: str) -> bool:
        """Переход в директорию"""
        try:
            target = Path(path)
            
            # Поддержка относительных путей
            if not target.is_absolute():
                target = self.current_path / target
            
            # Поддержка специальных путей
            if path == "..":
                target = self.current_path.parent
            elif path == "~" or path == "home":
                target = Path.home()
            elif path == "/" or path == "root":
                target = Path("/") if os.name != 'nt' else Path("C:\\")
            
            if target.exists() and target.is_dir():
                self.current_path = target.resolve()
                self.kernel.emit_event("directory_changed", {
                    "path": str(self.current_path)
                })
                return True
                
        except Exception as e:
            self.kernel.logger.error(f"Navigation error: {e}")
        
        return False
    
    def quick_search(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Быстрый поиск файлов по шаблону"""
        results = []
        query_lower = query.lower()
        
        try:
            for root, dirs, files in os.walk(self.current_path, topdown=True):
                # Ищем в директориях
                for d in dirs:
                    if query_lower in d.lower():
                        full_path = Path(root) / d
                        results.append({
                            "name": d,
                            "path": str(full_path),
                            "is_dir": True,
                            "context": root,
                            "score": self._calculate_search_score(d, query)
                        })
                
                # Ищем в файлах
                for f in files:
                    if query_lower in f.lower():
                        full_path = Path(root) / f
                        results.append({
                            "name": f,
                            "path": str(full_path),
                            "is_dir": False,
                            "context": root,
                            "score": self._calculate_search_score(f, query)
                        })
                
                # Ограничение количества результатов
                if len(results) >= max_results:
                    break
                    
        except PermissionError:
            pass
        
        # Сортировка по релевантности
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:max_results]
    
    def _calculate_search_score(self, text: str, query: str) -> float:
        """Расчёт релевантности для поиска"""
        text_lower = text.lower()
        query_lower = query.lower()
        
        if text_lower == query_lower:
            return 1.0
        elif text_lower.startswith(query_lower):
            return 0.9
        elif query_lower in text_lower:
            return 0.8
        else:
            # Частичное совпадение с помощью fnmatch
            if fnmatch.fnmatch(text_lower, f"*{query_lower}*"):
                return 0.7
            return 0.0
    
    def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """Копирование файла/папки с прогрессом"""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return {"success": False, "error": "Source does not exist"}
        
        # Если destination - директория, копируем внутрь
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        try:
            # Отправляем событие начала операции
            self.kernel.emit_event("file_operation_start", {
                "operation": "copy",
                "source": str(source_path),
                "destination": str(dest_path)
            })
            
            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
                result = {"success": True, "message": f"File copied to {dest_path}"}
            elif source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                result = {"success": True, "message": f"Directory copied to {dest_path}"}
            else:
                result = {"success": False, "error": "Unknown source type"}
            
            # Отправляем событие завершения
            self.kernel.emit_event("file_operation_complete", {
                "operation": "copy",
                "source": str(source_path),
                "destination": str(dest_path),
                "success": result["success"]
            })
            
            # Очищаем кеш для целевой директории
            self._invalidate_cache(dest_path.parent)
            
            return result
            
        except Exception as e:
            error_msg = f"Copy failed: {e}"
            self.kernel.logger.error(error_msg)
            
            self.kernel.emit_event("file_operation_error", {
                "operation": "copy",
                "source": str(source_path),
                "destination": str(dest_path),
                "error": str(e)
            })
            
            return {"success": False, "error": error_msg}
    
    def move(self, source: str, destination: str) -> Dict[str, Any]:
        """Перемещение файла/папки"""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return {"success": False, "error": "Source does not exist"}
        
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        try:
            self.kernel.emit_event("file_operation_start", {
                "operation": "move",
                "source": str(source_path),
                "destination": str(dest_path)
            })
            
            shutil.move(source_path, dest_path)
            
            self.kernel.emit_event("file_operation_complete", {
                "operation": "move",
                "source": str(source_path),
                "destination": str(dest_path),
                "success": True
            })
            
            # Очищаем кеш для обеих директорий
            self._invalidate_cache(source_path.parent)
            self._invalidate_cache(dest_path.parent)
            
            return {"success": True, "message": f"Moved to {dest_path}"}
            
        except Exception as e:
            error_msg = f"Move failed: {e}"
            self.kernel.logger.error(error_msg)
            
            self.kernel.emit_event("file_operation_error", {
                "operation": "move",
                "source": str(source_path),
                "destination": str(dest_path),
                "error": str(e)
            })
            
            return {"success": False, "error": error_msg}
    
    def delete(self, path: str, permanent: bool = False) -> Dict[str, Any]:
        """Удаление файла/папки"""
        target = Path(path)
        
        if not target.exists():
            return {"success": False, "error": "Path does not exist"}
        
        try:
            self.kernel.emit_event("file_operation_start", {
                "operation": "delete",
                "path": str(target),
                "permanent": permanent
            })
            
            if target.is_file():
                if permanent:
                    os.unlink(target)
                else:
                    # В Windows перемещаем в корзину
                    if os.name == 'nt':
                        import send2trash
                        send2trash.send2trash(str(target))
                    else:
                        # На Linux просто удаляем
                        os.unlink(target)
            elif target.is_dir():
                if permanent:
                    shutil.rmtree(target)
                else:
                    if os.name == 'nt':
                        import send2trash
                        send2trash.send2trash(str(target))
                    else:
                        shutil.rmtree(target)
            
            self.kernel.emit_event("file_operation_complete", {
                "operation": "delete",
                "path": str(target),
                "permanent": permanent,
                "success": True
            })
            
            # Очищаем кеш для родительской директории
            self._invalidate_cache(target.parent)
            
            return {"success": True, "message": f"Deleted {target.name}"}
            
        except Exception as e:
            error_msg = f"Delete failed: {e}"
            self.kernel.logger.error(error_msg)
            
            self.kernel.emit_event("file_operation_error", {
                "operation": "delete",
                "path": str(target),
                "permanent": permanent,
                "error": str(e)
            })
            
            return {"success": False, "error": error_msg}
    
    def create_directory(self, path: str, name: str) -> Dict[str, Any]:
        """Создание новой директории"""
        parent = Path(path)
        new_dir = parent / name
        
        if new_dir.exists():
            return {"success": False, "error": "Directory already exists"}
        
        try:
            new_dir.mkdir(parents=True, exist_ok=False)
            
            self.kernel.emit_event("directory_created", {
                "path": str(new_dir),
                "parent": str(parent)
            })
            
            self._invalidate_cache(parent)
            
            return {"success": True, "path": str(new_dir), "message": f"Directory created"}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create directory: {e}"}
    
    def create_file(self, path: str, name: str, content: str = "") -> Dict[str, Any]:
        """Создание нового файла"""
        parent = Path(path)
        new_file = parent / name
        
        if new_file.exists():
            return {"success": False, "error": "File already exists"}
        
        try:
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.kernel.emit_event("file_created", {
                "path": str(new_file),
                "parent": str(parent),
                "size": len(content)
            })
            
            self._invalidate_cache(parent)
            
            return {"success": True, "path": str(new_file), "message": f"File created"}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create file: {e}"}
    
    def read_file(self, path: str, limit: int = 10000) -> Dict[str, Any]:
        """Чтение содержимого файла с ограничением"""
        file_path = Path(path)
        
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}
        
        if not file_path.is_file():
            return {"success": False, "error": "Not a file"}
        
        try:
            # Проверяем размер файла
            size = file_path.stat().st_size
            
            if size > limit:
                # Читаем только первые N байт для больших файлов
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(limit)
                truncated = True
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                truncated = False
            
            # Определяем тип содержимого
            is_binary = False
            try:
                content.encode('utf-8')
            except:
                is_binary = True
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content if not is_binary else None,
                "binary": is_binary,
                "size": size,
                "truncated": truncated,
                "readable": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {e}"}
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Расширенная информация о файле"""
        file_path = Path(path)
        
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}
        
        try:
            stat_info = file_path.stat()
            import hashlib
            
            # Вычисляем хеш MD5 для файлов среднего размера
            md5_hash = None
            if file_path.is_file() and stat_info.st_size < 100 * 1024 * 1024:  # < 100MB
                try:
                    with open(file_path, 'rb') as f:
                        md5_hash = hashlib.md5(f.read()).hexdigest()
                except:
                    pass
            
            info = {
                "success": True,
                "name": file_path.name,
                "path": str(file_path),
                "absolute_path": str(file_path.absolute()),
                "is_dir": file_path.is_dir(),
                "is_file": file_path.is_file(),
                "is_symlink": file_path.is_symlink(),
                "size": stat_info.st_size,
                "size_human": self._human_readable_size(stat_info.st_size),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "extension": file_path.suffix.lower(),
                "type": self._get_file_type(file_path),
                "permissions": oct(stat_info.st_mode),
                "inode": stat_info.st_ino,
                "device": stat_info.st_dev,
                "links": stat_info.st_nlink,
                "uid": stat_info.st_uid if hasattr(stat_info, 'st_uid') else None,
                "gid": stat_info.st_gid if hasattr(stat_info, 'st_gid') else None,
                "md5": md5_hash,
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK),
                "executable": os.access(file_path, os.X_OK),
            }
            
            # Добавляем MIME тип
            if file_path.is_file():
                mime_type, encoding = mimetypes.guess_type(str(file_path))
                info["mime_type"] = mime_type or "application/octet-stream"
                info["encoding"] = encoding
            
            return info
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get file info: {e}"}
    
    def _invalidate_cache(self, path: Optional[Path] = None):
        """Очистка кеша для пути"""
        if path:
            cache_key = str(path)
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()
    
    def set_clipboard(self, paths: List[str], operation: str = "copy"):
        """Установка буфера обмена для файлов"""
        self.clipboard = paths
        self.clipboard_operation = operation
        
        self.kernel.emit_event("clipboard_updated", {
            "count": len(paths),
            "operation": operation
        })
    
    def paste(self, destination: str) -> List[Dict[str, Any]]:
        """Вставка из буфера обмена"""
        if not self.clipboard or not self.clipboard_operation:
            return []
        
        dest_path = Path(destination)
        results = []
        
        for source in self.clipboard:
            source_path = Path(source)
            
            if self.clipboard_operation == "copy":
                result = self.copy(source, destination)
            elif self.clipboard_operation == "cut":
                result = self.move(source, destination)
            else:
                result = {"success": False, "error": "Unknown operation"}
            
            results.append({
                "source": source,
                "destination": str(dest_path / source_path.name),
                "operation": self.clipboard_operation,
                **result
            })
        
        # Очищаем буфер после операции cut
        if self.clipboard_operation == "cut":
            self.clipboard = None
            self.clipboard_operation = None
        
        return results
    
    def rename(self, old_path: str, new_name: str) -> Dict[str, Any]:
        """Переименование файла/папки"""
        old = Path(old_path)
        
        if not old.exists():
            return {"success": False, "error": "Path does not exist"}
        
        new_path = old.parent / new_name
        
        if new_path.exists():
            return {"success": False, "error": "Target already exists"}
        
        try:
            old.rename(new_path)
            
            self.kernel.emit_event("file_renamed", {
                "old_path": str(old),
                "new_path": str(new_path)
            })
            
            # Очищаем кеш для родительской директории
            self._invalidate_cache(old.parent)
            
            return {"success": True, "message": f"Renamed to {new_name}"}
            
        except Exception as e:
            return {"success": False, "error": f"Rename failed: {e}"}