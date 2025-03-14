import sqlite3

class QuestionAnswerDB:
    def __init__(self, db_name="questions_answers.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()


    def create_table(self):
        """Создает таблицу вопросов и ответов, если она еще не существует"""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS questions_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор для каждого вопроса
            question TEXT,
            answer TEXT
        )''')
        self.conn.commit()


    def add_question_answer(self, question: str, answer: str):
        """Добавляет новый вопрос и ответ в базу данных"""
        self.cursor.execute("INSERT INTO questions_answers (question, answer) VALUES (?, ?)", (question, answer))
        self.conn.commit()


    def get_answer(self, question_id: int):
        """Возвращает ответ на вопрос по ID"""
        self.cursor.execute("SELECT answer FROM questions_answers WHERE id=?", (question_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None


    def get_all_questions(self):
        """Возвращает все вопросы с их ID"""
        self.cursor.execute("SELECT id, question FROM questions_answers")
        result = self.cursor.fetchall()
        return result  # Возвращаем список из кортежей (id, question)


    def delete_question(self, question_id: int):
        """Удаляет вопрос по ID"""
        self.cursor.execute("DELETE FROM questions_answers WHERE id=?", (question_id,))
        self.conn.commit()


    def update_question_answer(self, question_id: int, question: str = None, answer: str = None):
        """Обновляет вопрос или ответ по ID. Можно обновить только вопрос или только ответ."""
        update_fields = []
        update_values = []

        if question:
            update_fields.append("question=?")
            update_values.append(question)
        if answer:
            update_fields.append("answer=?")
            update_values.append(answer)

        if update_fields:
            query = f"UPDATE questions_answers SET {', '.join(update_fields)} WHERE id=?"
            update_values.append(question_id)
            self.cursor.execute(query, tuple(update_values))
            self.conn.commit()


    def add_question_answer(self, question: str, answer: str):
        """Добавляет новый вопрос и ответ в базу данных"""
        self.cursor.execute("INSERT INTO questions_answers (question, answer) VALUES (?, ?)", (question, answer))
        self.conn.commit()