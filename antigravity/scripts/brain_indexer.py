#!/usr/bin/env python3
import os
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# =======================================================================
# 🧠 LOKI BRAIN INDEXER: TRÌNH LẬP CHỈ MỤC THẦN KINH (v5.1.0-ABYSSAL)
# =======================================================================
SKILLS_DIR = "C:/Users/<USER_NAME>/.gemini/antigravity/skills/"
DB_FILE = "C:/Users/<USER_NAME>/.gemini/antigravity/scripts/loki_brain.db"

class LokiBrainIndexer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        """Khởi tạo cấu trúc bảng Đồ thị Tri thức (Graph RAG)"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                content TEXT,
                hash TEXT,
                category TEXT,
                last_updated TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_links (
                source_id INTEGER,
                target_id INTEGER,
                rel_type TEXT,
                FOREIGN KEY(source_id) REFERENCES knowledge_nodes(id),
                FOREIGN KEY(target_id) REFERENCES knowledge_nodes(id)
            )
        ''')
        self.conn.commit()

    def _calculate_hash(self, content):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def index_all_skills(self):
        """Quét và nhúng toàn bộ tri thức tĩnh vào SQLite Brain"""
        print(f"🏗️ [INDEXER] Đang quét tri thức tại: {SKILLS_DIR} ...")
        count = 0
        for root, dirs, files in os.walk(SKILLS_DIR):
            for file in files:
                if file.endswith(('.md', '.json', '.xml', '.py', '.sh')):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, start=os.getcwd())
                    
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"⚠️ [ERROR] Không thể đọc {rel_path}: {e}")
                        continue

                    file_hash = self._calculate_hash(content)
                    category = os.path.basename(root)

                    # Update or Insert
                    self.cursor.execute('''
                        INSERT INTO knowledge_nodes (file_path, content, hash, category, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(file_path) DO UPDATE SET
                            content=excluded.content,
                            hash=excluded.hash,
                            last_updated=excluded.last_updated
                    ''', (rel_path, content, file_hash, category, datetime.now()))
                    count += 1

        self.conn.commit()
        print(f"✅ [INDEXER] Đã nạp thành công {count} Node tri thức vào loki_brain.db.")

    def search_brain(self, query):
        """Hàm tìm kiếm tri thức siêu tốc (0.01s)"""
        # SQLite FTS hoặc LIKE đơn giản cho phiên bản này
        self.cursor.execute("SELECT file_path FROM knowledge_nodes WHERE content LIKE ?", (f'%{query}%',))
        results = self.cursor.fetchall()
        return [r[0] for r in results]

if __name__ == "__main__":
    indexer = LokiBrainIndexer()
    indexer.index_all_skills()
    print("🧠 [BRAIN READY] Loki Brain has been forged.")

