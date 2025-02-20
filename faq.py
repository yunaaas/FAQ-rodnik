import sqlite3

class QuestionAnswerDB:
    def __init__(self, db_name="questions_answers.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS questions_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор для каждого вопроса
            question TEXT,
            answer TEXT
        )''')
        self.conn.commit()

    def add_question_answer(self, question: str, answer: str):
        self.cursor.execute("INSERT INTO questions_answers (question, answer) VALUES (?, ?)", (question, answer))
        self.conn.commit()

    def get_answer(self, question_id: int):
        self.cursor.execute("SELECT answer FROM questions_answers WHERE id=?", (question_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_questions(self):
        self.cursor.execute("SELECT id, question FROM questions_answers")
        result = self.cursor.fetchall()
        return result  # Возвращаем список из кортежей (id, question)
