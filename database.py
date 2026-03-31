# database.py
import sqlite3


class Database:
    def __init__(self, db_file="users.db"):
        """Инициализация базы данных"""
        self.db_file = db_file
        self._create_table()

    def _create_table(self):
        """Создание таблицы, если её нет"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_user_group(self, user_id, group_name):
        """Сохранить группу пользователя"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO users (user_id, group_name)
                    VALUES (?, ?)
                """, (user_id, group_name))
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def get_user_group(self, user_id):
        """Получить группу пользователя"""
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
            print(f"Ошибка получения: {e}")
            return None
