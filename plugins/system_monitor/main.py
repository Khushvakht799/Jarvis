import psutil
import time
from datetime import datetime
from threading import Thread

class Plugin:
    """Системный монитор - пример плагина"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.name = "system_monitor"
        self.version = "1.0.0"
        self.description = "System monitoring and statistics"
        self.running = False
        self.monitor_thread = None
        
    def on_load(self):
        """Вызывается при загрузке плагина"""
        self.kernel.logger.info(f"System Monitor plugin loaded")
        self.kernel.subscribe_event("get_system_stats", self.handle_get_stats)
        self.start_monitoring()
        
    def on_unload(self):
        """Вызывается при выгрузке плагина"""
        self.stop_monitoring()
        self.kernel.unsubscribe_event("get_system_stats", self.handle_get_stats)
        self.kernel.logger.info(f"System Monitor plugin unloaded")
        
    def handle_get_stats(self, event_name, data):
        """Обработчик события запроса статистики"""
        return self.get_system_stats()
        
    def get_system_stats(self):
        """Получить статистику системы"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # Информация о процессах
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "system": {
                    "boot_time": boot_time.isoformat(),
                    "uptime": time.time() - psutil.boot_time(),
                    "process_count": len(processes),
                    "users": [user._asdict() for user in psutil.users()]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.kernel.logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
        
    def start_monitoring(self):
        """Запуск фонового мониторинга"""
        self.running = True
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
    def _monitor_loop(self):
        """Фоновый цикл мониторинга"""
        while self.running:
            stats = self.get_system_stats()
            if "error" not in stats:
                # Отправляем регулярные обновления
                self.kernel.emit_event("system_stats_update", stats)
            time.sleep(2)  # Обновляем каждые 2 секунды
