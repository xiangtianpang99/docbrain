import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = "docbrain.db"

class HistoryManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_session(self, title: str = "New Chat") -> str:
        """创建一个新会话，返回 session_id"""
        session_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (id, title) VALUES (?, ?)",
                (session_id, title)
            )
            conn.commit()
        return session_id

    def delete_session(self, session_id: str):
        """删除会话及其所有消息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话列表，按时间倒序"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                {"id": row[0], "title": row[1], "created_at": row[2]}
                for row in rows
            ]

    def add_message(self, session_id: str, role: str, content: str):
        """向会话添加一条消息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 确保会话存在
            cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                # 如果会话不存在（例如第一次存），自动创建
                self.create_session(title=content[:20] + "..." if len(content) > 20 else content)
            
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            
            # 如果是第一条用户消息，自动更新会话标题
            if role == "user":
                 cursor.execute("SELECT count(*) FROM messages WHERE session_id = ?", (session_id,))
                 count = cursor.fetchone()[0]
                 if count <= 2: # 第1或2条消息（考虑系统消息）
                     new_title = content[:30] + "..." if len(content) > 30 else content
                     cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))

            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """获取指定会话的所有消息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            return [
                {"role": row[0], "content": row[1], "created_at": row[2]}
                for row in rows
            ]

# 全局单例
history_manager = HistoryManager()
