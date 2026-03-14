"""
TUI интерфейс Jarvis на Textual
Окна, вкладки, дерево файлов - как Windows Explorer
"""

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, DirectoryTree, Static, Label, Button, TabbedContent, TabPane, Tree, ListView, ListItem, Input, TextArea, DataTable, Markdown, LoadingIndicator
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.message import Message
from pathlib import Path
import time
from datetime import datetime
import psutil
import asyncio
from typing import Optional, Dict, Any
import json

class FileExplorerPane(TabPane):
    """Панель файлового менеджера с деревом и списком"""
    
    def __init__(self, kernel, title="Explorer", **kwargs):
        super().__init__(title, **kwargs)
        self.kernel = kernel
        self.file_explorer = kernel.plugins.get("file_explorer")
        self.current_path = Path.cwd()
        self.selected_files = []
        
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Боковая панель с деревом
            with Vertical(id="sidebar"):
                yield Label("📁 Locations", classes="sidebar-title")
                yield Button("🏠 Home", id="btn-home", variant="primary")
                yield Button("📁 Documents", id="btn-documents")
                yield Button("⬇️ Downloads", id="btn-downloads")
                yield Button("🖼️ Desktop", id="btn-desktop")
                yield Static("", classes="spacer")
                yield Label("🔧 Quick Access", classes="sidebar-title")
                yield Button("⭐ Favorites", id="btn-favorites")
                yield Button("🔄 Recent", id="btn-recent")
                yield Button("🗑️ Recycle Bin", id="btn-trash")
            
            # Основная область с файлами
            with Vertical(id="main-area"):
                # Панель инструментов
                with Horizontal(id="toolbar"):
                    yield Button("←", id="btn-back", classes="toolbar-btn")
                    yield Button("→", id="btn-forward", classes="toolbar-btn")
                    yield Button("↑", id="btn-up", classes="toolbar-btn")
                    yield Button("🔄", id="btn-refresh", classes="toolbar-btn")
                    yield Static("", classes="spacer")
                    yield Input(placeholder="Search files...", id="search-input")
                    yield Button("🔍", id="btn-search", classes="toolbar-btn")
                
                # Путь и статистика
                with Horizontal(id="path-bar"):
                    yield Label("Path:", classes="path-label")
                    yield Label(str(self.current_path), id="current-path", classes="path-value")
                    yield Static("", classes="spacer")
                    yield Label("Items: 0", id="item-count", classes="stats")
                    yield Label("Size: 0", id="total-size", classes="stats")
                
                # Заголовки столбцов
                with Horizontal(id="column-headers"):
                    yield Label("Name", classes="col-header", id="col-name")
                    yield Label("Size", classes="col-header", id="col-size")
                    yield Label("Modified", classes="col-header", id="col-modified")
                    yield Label("Type", classes="col-header", id="col-type")
                
                # Список файлов (через ListView для прокрутки)
                yield ListView(id="file-list")
                
                # Панель статуса
                with Horizontal(id="status-bar"):
                    yield Label("Ready", id="status-message")
                    yield Static("", classes="spacer")
                    yield Label("JARVIS TUI", id="app-name")

class SystemMonitorPane(TabPane):
    """Панель мониторинга системы"""
    
    def __init__(self, kernel, **kwargs):
        super().__init__("System", **kwargs)
        self.kernel = kernel
        self.stats = {}
        
    def compose(self) -> ComposeResult:
        with Grid(id="system-grid"):
            # CPU Usage
            with Container(classes="metric-card"):
                yield Label("💻 CPU Usage", classes="metric-title")
                yield Static("[██████████]", id="cpu-bar", classes="metric-bar")
                yield Label("0%", id="cpu-percent", classes="metric-value")
                yield Label("Cores: 0", id="cpu-cores", classes="metric-detail")
            
            # Memory Usage
            with Container(classes="metric-card"):
                yield Label("🧠 Memory", classes="metric-title")
                yield Static("[██████████]", id="mem-bar", classes="metric-bar")
                yield Label("0%", id="mem-percent", classes="metric-value")
                yield Label("0GB / 0GB", id="mem-details", classes="metric-detail")
            
            # Disk Usage
            with Container(classes="metric-card"):
                yield Label("💾 Disk", classes="metric-title")
                yield Static("[██████████]", id="disk-bar", classes="metric-bar")
                yield Label("0%", id="disk-percent", classes="metric-value")
                yield Label("0GB free", id="disk-details", classes="metric-detail")
            
            # Network
            with Container(classes="metric-card"):
                yield Label("🌐 Network", classes="metric-title")
                yield Label("↑ 0 KB/s", id="net-up", classes="metric-value")
                yield Label("↓ 0 KB/s", id="net-down", classes="metric-value")
                yield Label("Connected", id="net-status", classes="metric-detail")
            
            # Processes Table
            with Container(classes="wide-card"):
                yield Label("🔄 Processes", classes="metric-title")
                yield DataTable(id="process-table")

class AIPane(TabPane):
    """Панель AI Assistant"""
    
    def __init__(self, kernel, **kwargs):
        super().__init__("AI Assistant", **kwargs)
        self.kernel = kernel
        self.chat_history = []
        
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Чат
            with Vertical(id="ai-chat"):
                yield Label("🤖 JARVIS AI", classes="pane-title")
                yield TextArea(id="chat-display", read_only=True)
                with Horizontal():
                    yield Input(placeholder="Ask me anything...", id="ai-input")
                    yield Button("Send", id="send-msg", variant="primary")
            
            # Панель инструментов
            with Vertical(id="ai-tools", classes="tools-pane"):
                yield Label("🛠️ Tools", classes="pane-title")
                yield Button("📝 Summarize", id="tool-summarize")
                yield Button("🔍 Analyze", id="tool-analyze")
                yield Button("🐛 Debug", id="tool-debug")
                yield Button("💡 Explain", id="tool-explain")
                yield Button("⚡ Optimize", id="tool-optimize")
                yield Static("", classes="spacer")
                yield Label("⚙️ Settings", classes="pane-title")
                yield Button("🧠 Model: GPT-3.5", id="btn-model")
                yield Button("🌡️ Temperature: 0.7", id="btn-temp")

class PluginsPane(TabPane):
    """Панель управления плагинами"""
    
    def __init__(self, kernel, **kwargs):
        super().__init__("Plugins", **kwargs)
        self.kernel = kernel
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🧩 Plugin Manager", classes="pane-title")
            
            with Horizontal():
                yield Button("🔄 Refresh", id="refresh-plugins", variant="primary")
                yield Button("➕ Install", id="install-plugin")
                yield Button("🗑️ Remove", id="remove-plugin")
                yield Button("⚙️ Configure", id="configure-plugin")
            
            yield DataTable(id="plugins-table")

class JarvisTUI(App):
    """Основное TUI приложение Jarvis"""
    
    CSS_PATH = "tui_style.css"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "show_help", "Help"),
        Binding("f2", "new_file", "New File"),
        Binding("f3", "search", "Search"),
        Binding("f5", "refresh", "Refresh"),
        Binding("ctrl+n", "new_folder", "New Folder"),
        Binding("ctrl+c", "copy", "Copy"),
        Binding("ctrl+x", "cut", "Cut"),
        Binding("ctrl+v", "paste", "Paste"),
        Binding("delete", "delete", "Delete"),
        Binding("f10", "toggle_fullscreen", "Fullscreen"),
    ]
    
    def __init__(self, kernel, file_explorer):
        super().__init__()
        self.kernel = kernel
        self.file_explorer = file_explorer
        self.current_tab = "explorer"
        self.clipboard = []
        self.clipboard_op = "copy"
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent(initial="explorer"):
            yield FileExplorerPane(self.kernel, title="Explorer", id="explorer-tab")
            yield SystemMonitorPane(self.kernel, id="system-tab")
            yield AIPane(self.kernel, id="ai-tab")
            yield PluginsPane(self.kernel, id="plugins-tab")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Инициализация при загрузке"""
        self.title = "JARVIS Modular Assistant"
        self.sub_title = "TUI Interface"
        
        # Запускаем обновление статистики
        self.set_interval(2, self.update_system_stats)
        
        # Загружаем файлы в текущей директории
        self.load_current_directory()
    
    async def load_current_directory(self):
        """Загрузка файлов текущей директории"""
        file_list = self.query_one("#file-list")
        file_list.clear()
        
        result = self.file_explorer.list_directory()
        if "error" not in result:
            for item in result["items"]:
                icon = "📁" if item["is_dir"] else "📄"
                name = f"{icon} {item['name']}"
                list_item = ListItem(Label(name))
                list_item.file_data = item
                file_list.append(list_item)
            
            # Обновляем статистику
            path_label = self.query_one("#current-path")
            path_label.update(str(self.file_explorer.current_path))
            
            count_label = self.query_one("#item-count")
            count_label.update(f"Items: {result['total']}")
    
    async def update_system_stats(self):
        """Обновление системной статистики"""
        plugin = self.kernel.get_plugin("system_monitor")
        if plugin:
            stats = plugin.get_system_stats()
            
            # CPU
            cpu_percent = stats["cpu"]["percent"]
            cpu_bar = self.query_one("#cpu-bar")
            cpu_value = self.query_one("#cpu-percent")
            
            bar_length = 10
            filled = int(cpu_percent / 10)
            cpu_bar.update("[" + "█" * filled + " " * (bar_length - filled) + "]")
            cpu_value.update(f"{cpu_percent}%")
            
            # Memory
            mem_percent = stats["memory"]["percent"]
            mem_bar = self.query_one("#mem-bar")
            mem_value = self.query_one("#mem-percent")
            
            filled = int(mem_percent / 10)
            mem_bar.update("[" + "█" * filled + " " * (bar_length - filled) + "]")
            mem_value.update(f"{mem_percent}%")
            
            # Cores
            cores_label = self.query_one("#cpu-cores")
            cores_label.update(f"Cores: {stats['cpu']['cores']}")
            
            # Memory details
            mem_details = self.query_one("#mem-details")
            used_gb = stats["memory"]["used"] / (1024**3)
            total_gb = stats["memory"]["total"] / (1024**3)
            mem_details.update(f"{used_gb:.1f}GB / {total_gb:.1f}GB")
    
    # Обработчики действий
    def action_refresh(self):
        """Обновление текущего вида"""
        asyncio.create_task(self.load_current_directory())
    
    def action_new_file(self):
        """Создание нового файла"""
        self.notify("New File - Press Ctrl+N", severity="information")
    
    def action_new_folder(self):
        """Создание новой папки"""
        self.notify("New Folder - Implementation in progress", severity="information")
    
    def action_copy(self):
        """Копирование файлов"""
        self.notify("Copy to clipboard", severity="information")
    
    def action_cut(self):
        """Вырезание файлов"""
        self.notify("Cut to clipboard", severity="information")
    
    def action_paste(self):
        """Вставка файлов"""
        self.notify("Paste from clipboard", severity="information")
    
    def action_delete(self):
        """Удаление файлов"""
        self.notify("Delete selected files", severity="warning")
    
    def action_toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        self.toggle_fullscreen()
    
    def action_show_help(self):
        """Показать справку"""
        self.notify("""
JARVIS TUI Help:
F1 - This help
F2 - New File
F3 - Search
F5 - Refresh
Ctrl+N - New Folder
Ctrl+C/X/V - Copy/Cut/Paste
Del - Delete
F10 - Fullscreen
        """, severity="information", timeout=5)

def run_tui_interface(kernel, file_explorer):
    """Запуск TUI интерфейса"""
    app = JarvisTUI(kernel, file_explorer)
    app.run()