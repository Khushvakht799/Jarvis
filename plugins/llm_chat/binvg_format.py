import struct
import mmap
import numpy as np
from pathlib import Path

class BinVGrFile:
    """
    Бинарный формат файла для хранения графа с векторными связями
    Структура:
    [MAGIC][HEADER][NODES][EDGES][EMBEDDINGS]
    """
    
    MAGIC = b'BINVG1.0'  # 8 байт магическое число
    HEADER_SIZE = 32     # Заголовок
    
    def __init__(self, filename="jarvis.binvg"):
        self.filename = filename
        self.file = None
        self.mmap = None
        
    def create_new(self, num_nodes=1000, num_edges=5000):
        """Создать новый бинарный файл с резервированием места"""
        with open(self.filename, 'wb') as f:
            # 1. Магическое число (8 байт)
            f.write(self.MAGIC)
            
            # 2. Заголовок (32 байта)
            header = struct.pack(
                'IIIIQQ',  # 4 ints + 2 qwords
                num_nodes,           # максимальное количество узлов
                num_edges,           # максимальное количество связей
                128,                 # размер embedding'а (например, 128 байт)
                0,                   # флаги/версия
                0,                   # смещение до секции узлов
                0                    # смещение до секции связей
            )
            f.write(header)
            
            # 3. Резервируем место под узлы
            # Каждый узел: id(4) + имя(64) + интент(32) + embedding(128) + флаги(4) = 232 байта
            node_size = 232
            f.write(b'\x00' * (num_nodes * node_size))
            
            # 4. Резервируем место под связи
            # Каждая связь: from(4) + to(4) + вес(4) + тип(4) = 16 байт
            edge_size = 16
            f.write(b'\x00' * (num_edges * edge_size))
            
        print(f"✅ Создан бинарный файл {self.filename}: {num_nodes} узлов, {num_edges} связей")
        
    def open_mmap(self):
        """Открыть файл в memory-mapped режиме (очень быстро)"""
        self.file = open(self.filename, 'r+b')
        self.mmap = mmap.mmap(self.file.fileno(), 0)
        
        # Читаем заголовок
        magic = self.mmap[:8]
        if magic != self.MAGIC:
            raise ValueError("Неверный формат файла")
            
        # Распарсить заголовок
        header_data = struct.unpack('IIIIQQ', self.mmap[8:40])
        self.max_nodes, self.max_edges, self.emb_size, self.flags, self.nodes_offset, self.edges_offset = header_data
        
        print(f"📊 BinVGr загружен: {self.max_nodes} узлов макс, embedding {self.emb_size}")
        
    def write_node(self, node_id, name, intent, embedding=None):
        """Записать узел по прямому смещению"""
        if node_id >= self.max_nodes:
            raise ValueError(f"node_id {node_id} превышает максимум {self.max_nodes}")
            
        # Смещение до узла
        node_size = 232
        offset = 40 + node_id * node_size  # 40 = MAGIC(8) + HEADER(32)
        
        # Упаковываем данные
        name_bytes = name.encode('utf-8')[:63].ljust(64, b'\x00')
        intent_bytes = intent.encode('utf-8')[:31].ljust(32, b'\x00')
        
        if embedding is None:
            embedding = np.zeros(self.emb_size, dtype=np.float32)
        emb_bytes = embedding.astype(np.float32).tobytes()
        
        # Пишем прямо в memory-mapped файл
        self.mmap[offset:offset+4] = struct.pack('I', node_id)  # id
        self.mmap[offset+4:offset+68] = name_bytes  # имя
        self.mmap[offset+68:offset+100] = intent_bytes  # интент
        self.mmap[offset+100:offset+100+self.emb_size*4] = emb_bytes  # embedding (float32)
        self.mmap[offset+100+self.emb_size*4:offset+232] = struct.pack('I', 0)  # флаги
        
        # Форсируем запись на диск
        self.mmap.flush(offset, 232)
        
    def write_edge(self, edge_id, from_id, to_id, weight=0.5, edge_type=0):
        """Записать связь"""
        if edge_id >= self.max_edges:
            raise ValueError(f"edge_id {edge_id} превышает максимум {self.max_edges}")
            
        # Смещение до связи (после всех узлов)
        edge_size = 16
        offset = 40 + self.max_nodes * 232 + edge_id * edge_size
        
        data = struct.pack('IIfI', from_id, to_id, weight, edge_type)
        self.mmap[offset:offset+16] = data
        self.mmap.flush(offset, 16)
        
    def read_node(self, node_id):
        """Быстрое чтение узла по ID"""
        offset = 40 + node_id * 232
        
        # Читаем напрямую из memory-mapped области
        node_id_read = struct.unpack('I', self.mmap[offset:offset+4])[0]
        name = self.mmap[offset+4:offset+68].split(b'\x00')[0].decode('utf-8')
        intent = self.mmap[offset+68:offset+100].split(b'\x00')[0].decode('utf-8')
        
        # Читаем embedding
        emb_bytes = self.mmap[offset+100:offset+100+self.emb_size*4]
        embedding = np.frombuffer(emb_bytes, dtype=np.float32)
        
        return {
            'id': node_id_read,
            'name': name,
            'intent': intent,
            'embedding': embedding
        }
        
    def find_similar_nodes(self, query_embedding, top_k=5):
        """Найти похожие узлы по embedding (быстрый линейный поиск по памяти)"""
        results = []
        
        # Пробегаем по всем узлам (очень быстро, т.к. всё в памяти)
        for node_id in range(self.max_nodes):
            try:
                node = self.read_node(node_id)
                if node['name']:  # непустой узел
                    # Косинусное расстояние
                    sim = np.dot(query_embedding, node['embedding'])
                    sim /= (np.linalg.norm(query_embedding) * np.linalg.norm(node['embedding']) + 1e-8)
                    
                    results.append((sim, node))
            except:
                continue
                
        results.sort(key=lambda x: -x[0])
        return results[:top_k]
    
    def close(self):
        """Закрыть файл"""
        if self.mmap:
            self.mmap.close()
        if self.file:
            self.file.close()