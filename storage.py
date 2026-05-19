import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "sent_tasks.db"


def init_db():
    """Створює базу даних і таблицю якщо їх ще немає"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_tasks (
                id TEXT PRIMARY KEY,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("✅ База даних готова")


def is_task_sent(task_id: str) -> bool:
    """Повертає True якщо це завдання вже надсилали раніше"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT id FROM sent_tasks WHERE id = ?", (task_id,)
        )
        return cursor.fetchone() is not None


def mark_task_sent(task_id: str):
    """Зберігає ID завдання щоб не надсилати його повторно"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_tasks (id) VALUES (?)", (task_id,)
        )
        conn.commit()
    logger.info(f"Завдання збережено в БД: {task_id}")
