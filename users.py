# Класс для работы с второй базой данных (пользователи)
import sqlite3


class UserDB:
    def __init__(self, db_name="users.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            registration_date TEXT DEFAULT (datetime('now', 'localtime'))
        )
        ''')
        self.conn.commit()

    def add_user(self, user_id, first_name, last_name, username):
        self.cursor.execute("INSERT INTO users (user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
                            (user_id, first_name, last_name, username))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result if result else None

    def add_user_if_not_exists(self, user_id, first_name, last_name, username):
        """Проверяет, существует ли пользователь, и если нет, добавляет его в базу данных"""
        if not self.get_user(user_id):  # Если пользователя нет в базе
            self.add_user(user_id, first_name, last_name, username)