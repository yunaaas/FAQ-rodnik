import sqlite3
import random
import string
from datetime import datetime

class GreetingsDB:
    def __init__(self, db_name='greetings.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица для информации о пользователях
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                first_seen TIMESTAMP,
                last_active TIMESTAMP
            )
        ''')

        # Таблица для ссылок пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                link_code TEXT UNIQUE,
                created_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица для всех поздравлений
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS greetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_code TEXT,
                owner_user_id INTEGER,
                sender_user_id INTEGER,
                sender_first_name TEXT,
                sender_last_name TEXT,
                sender_username TEXT,
                is_anonymous BOOLEAN DEFAULT 0,
                message_text TEXT,
                media_type TEXT,
                media_file_id TEXT,
                created_at TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (link_code) REFERENCES user_links (link_code),
                FOREIGN KEY (owner_user_id) REFERENCES users (user_id),
                FOREIGN KEY (sender_user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица для статистики
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS greetings_stats (
                user_id INTEGER PRIMARY KEY,
                total_greetings INTEGER DEFAULT 0,
                last_greeting_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        self.conn.commit()

    def save_or_update_user(self, user_id, first_name, last_name, username):
        """Сохраняет или обновляет информацию о пользователе"""
        now = datetime.now()

        self.cursor.execute('''
            INSERT INTO users (user_id, first_name, last_name, username, first_seen, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                username = excluded.username,
                last_active = excluded.last_active
        ''', (user_id, first_name, last_name, username, now, now))

        self.conn.commit()

    def get_all_participants(self):
        """Получает ВСЕХ пользователей, которые когда-либо создавали ссылки"""
        self.cursor.execute('''
            SELECT DISTINCT 
                u.user_id,
                u.first_name,
                u.last_name,
                u.username,
                COALESCE(gs.total_greetings, 0) as total_greetings,
                ul.created_at as link_created,
                ul.link_code
            FROM users u
            INNER JOIN user_links ul ON u.user_id = ul.user_id
            LEFT JOIN greetings_stats gs ON u.user_id = gs.user_id
            WHERE ul.is_active = 1
            ORDER BY total_greetings DESC, u.last_active DESC
        ''')

        results = self.cursor.fetchall()

        print(f"=== ВСЕ УЧАСТНИКИ (создавшие ссылки) ===")
        for r in results:
            display_name = r[1] or r[2] or r[3] or str(r[0])
            print(f"User {r[0]}: {display_name} - {r[4]} поздравлений")

        return results

    def get_user_info(self, user_id):
        """Получает полную информацию о пользователе"""
        self.cursor.execute('''
            SELECT user_id, first_name, last_name, username, first_seen, last_active
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        return self.cursor.fetchone()

    def create_or_get_link(self, user_id, user_first_name=None, user_last_name=None, user_username=None):
        """Создает или получает существующую ссылку для пользователя"""
        
        # Сначала сохраняем/обновляем информацию о пользователе
        if user_first_name is not None:  # Проверяем, что данные переданы
            self.save_or_update_user(user_id, user_first_name, user_last_name, user_username)
        
        # Проверяем существующую ссылку
        self.cursor.execute("SELECT link_code FROM user_links WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Создаем новую ссылку
        link_code = self.generate_unique_code()
        now = datetime.now()
        
        self.cursor.execute('''
            INSERT INTO user_links (user_id, link_code, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, link_code, now))
        
        # Создаем запись в статистике
        self.cursor.execute('''
            INSERT INTO greetings_stats (user_id, total_greetings)
            VALUES (?, 0)
        ''', (user_id,))
        
        self.conn.commit()
        return link_code

    def save_greeting(self, link_code, owner_user_id, sender, is_anonymous, message_text, media_type=None, media_file_id=None):
        """Сохраняет полученное поздравление и обновляет информацию об отправителе"""

        # Сохраняем информацию об отправителе
        self.save_or_update_user(
            sender.id,
            sender.first_name,
            sender.last_name,
            sender.username
        )

        now = datetime.now()

        self.cursor.execute('''
            INSERT INTO greetings 
            (link_code, owner_user_id, sender_user_id, sender_first_name, sender_last_name, 
             sender_username, is_anonymous, message_text, media_type, media_file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            link_code, owner_user_id, sender.id, sender.first_name, sender.last_name,
            sender.username, is_anonymous, message_text, media_type, media_file_id, now
        ))

        # Обновляем статистику
        self.cursor.execute('''
            UPDATE greetings_stats 
            SET total_greetings = total_greetings + 1, last_greeting_date = ?
            WHERE user_id = ?
        ''', (now, owner_user_id))

        self.conn.commit()
        return self.cursor.lastrowid
    
    def generate_unique_code(self):
        """Генерирует уникальный код для ссылки"""
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            self.cursor.execute("SELECT id FROM user_links WHERE link_code = ?", (code,))
            if not self.cursor.fetchone():
                return code

    
    def get_user_by_link(self, link_code):
        """Получает user_id по коду ссылки"""
        self.cursor.execute("SELECT user_id FROM user_links WHERE link_code = ? AND is_active = 1", (link_code,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def save_greeting(self, link_code, owner_user_id, sender, is_anonymous, message_text, media_type=None, media_file_id=None):
        """Сохраняет полученное поздравление (полные данные отправителя всегда сохраняются)"""
        now = datetime.now()
        
        self.cursor.execute('''
            INSERT INTO greetings 
            (link_code, owner_user_id, sender_user_id, sender_first_name, sender_last_name, 
             sender_username, is_anonymous, message_text, media_type, media_file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            link_code, owner_user_id, sender.id, sender.first_name, sender.last_name,
            sender.username, is_anonymous, message_text, media_type, media_file_id, now
        ))
        
        # Обновляем статистику
        self.cursor.execute('''
            UPDATE greetings_stats 
            SET total_greetings = total_greetings + 1, last_greeting_date = ?
            WHERE user_id = ?
        ''', (now, owner_user_id))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user_greetings(self, user_id, limit=50, offset=0):
        """Получает все поздравления пользователя (для админки/статистики)"""
        self.cursor.execute('''
            SELECT * FROM greetings 
            WHERE owner_user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        return self.cursor.fetchall()
    
    def get_greeting_by_id(self, greeting_id):
        """Получает конкретное поздравление по ID"""
        self.cursor.execute("SELECT * FROM greetings WHERE id = ?", (greeting_id,))
        return self.cursor.fetchone()
    
    def mark_as_read(self, greeting_id):
        """Отмечает поздравление как прочитанное"""
        self.cursor.execute("UPDATE greetings SET is_read = 1 WHERE id = ?", (greeting_id,))
        self.conn.commit()
    
    def get_stats(self, user_id):
        """Получает статистику пользователя"""
        self.cursor.execute("SELECT total_greetings, last_greeting_date FROM greetings_stats WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()
    
    def deactivate_link(self, user_id):
        """Деактивирует ссылку пользователя"""
        self.cursor.execute("UPDATE user_links SET is_active = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def get_all_links(self):
        """Получает все активные ссылки (для администратора)"""
        self.cursor.execute("SELECT * FROM user_links WHERE is_active = 1")
        return self.cursor.fetchall()


    def get_all_users_with_links(self):
        """Получает всех пользователей с активными ссылками и статистикой"""
        self.cursor.execute('''
            SELECT ul.user_id, ul.link_code, ul.created_at, ul.is_active, 
                   COALESCE(gs.total_greetings, 0) as total
            FROM user_links ul
            LEFT JOIN greetings_stats gs ON ul.user_id = gs.user_id
            WHERE ul.is_active = 1
            ORDER BY total DESC
        ''')
        return self.cursor.fetchall()
    
    def get_user(self, user_id):
        """Получает информацию о пользователе по его telegram_id"""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()
    
    def get_greeting_by_id(self, greeting_id):
        """Получает конкретное поздравление по ID"""
        self.cursor.execute("SELECT * FROM greetings WHERE id = ?", (greeting_id,))
        return self.cursor.fetchone()
    


    def get_unique_users_with_stats(self):
        """Получает уникальных пользователей с суммой всех их поздравлений"""
        self.cursor.execute('''
            SELECT 
                ul.user_id,
                MAX(ul.link_code) as link_code,
                MAX(ul.created_at) as created_at,
                MAX(ul.is_active) as is_active,
                COALESCE(SUM(gs.total_greetings), 0) as total_greetings
            FROM user_links ul
            LEFT JOIN greetings_stats gs ON ul.user_id = gs.user_id
            WHERE ul.is_active = 1
            GROUP BY ul.user_id
            ORDER BY total_greetings DESC
        ''')
        
        results = self.cursor.fetchall()
        
        # Для отладки выведем все результаты
        print("=== УНИКАЛЬНЫЕ ПОЛЬЗОВАТЕЛИ ===")
        for r in results:
            print(f"User {r[0]}: {r[4]} поздравлений")
        
        return results

    def get_user_display_info(self, user_id):
        """Получает информацию для отображения пользователя (username, имя)"""
        # Сначала ищем по username
        self.cursor.execute('''
            SELECT 
                sender_username,
                sender_first_name,
                sender_last_name
            FROM greetings 
            WHERE owner_user_id = ? 
                AND sender_username IS NOT NULL 
                AND sender_username != ''
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user_id,))

        result = self.cursor.fetchone()

        if result and result[0]:
            return result

        # Если нет username, ищем по имени/фамилии
        self.cursor.execute('''
            SELECT 
                sender_username,
                sender_first_name,
                sender_last_name
            FROM greetings 
            WHERE owner_user_id = ? 
                AND (sender_first_name IS NOT NULL OR sender_last_name IS NOT NULL)
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user_id,))

        return self.cursor.fetchone()
# Создаем глобальный экземпляр БД
greetings_db = GreetingsDB()