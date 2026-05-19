import os
import threading
import time
import logging
from flask import Flask, jsonify
from bot import send_notification
from parser_human import get_important_tasks
from storage import init_db, is_task_sent, mark_task_sent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Інтервал перевірки в секундах (за замовчуванням 60 хвилин)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "60")) * 60


def check_and_notify():
    """Перевіряє нові завдання і надсилає сповіщення"""
    logger.info("🔍 Перевіряю завдання на Human...")
    try:
        tasks = get_important_tasks()
        logger.info(f"Знайдено завдань: {len(tasks)}")
        new_count = 0
        for task in tasks:
            task_id = task["id"]
            if not is_task_sent(task_id):
                send_notification(task)
                mark_task_sent(task_id)
                new_count += 1
                time.sleep(1)  # пауза між повідомленнями
        logger.info(f"✅ Готово. Нових завдань надіслано: {new_count}")
    except Exception as e:
        logger.error(f"❌ Помилка: {e}", exc_info=True)


def scheduler_loop():
    """Фоновий потік — нескінченно перевіряє завдання"""
    init_db()
    logger.info(f"⏰ Scheduler запущено. Інтервал: {CHECK_INTERVAL // 60} хв.")
    while True:
        check_and_notify()
        time.sleep(CHECK_INTERVAL)


# --- Flask маршрути ---

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Human Bot працює!"})


@app.route("/check", methods=["GET"])
def manual_check():
    """Ручний запуск перевірки"""
    threading.Thread(target=check_and_notify, daemon=True).start()
    return jsonify({"status": "ok", "message": "Перевірку запущено вручну"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    # Запускаємо scheduler у фоновому потоці
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
