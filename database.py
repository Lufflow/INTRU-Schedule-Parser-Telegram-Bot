import sqlite3
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file="users.db"):
        self.db_file = db_file
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_user_group(self, user_id, group_name):
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO users (user_id, group_name)
                    VALUES (?, ?)
                """, (user_id, group_name))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False

    def get_user_group(self, user_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                result = conn.execute(
                    "SELECT group_name FROM users WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if result:
                    return result[0]
                return None
        except Exception as e:
            logger.error(f"Ошибка получения: {e}")
            return None

    def get_user_id_list(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                result = conn.execute(
                    "SELECT user_id FROM users"
                ).fetchall()
                if result:
                    return [user_id[0] for user_id in result]
                return []
        except Exception as e:
            logger.error(f"Ошибка получения: {e}")
            return []

    def delete_user(self, user_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления: {e}")
            return False
