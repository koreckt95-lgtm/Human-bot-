import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Емодзі для кожного типу завдання
KEYWORD_EMOJI = {
    "контрольна робота": "📝",
    "підсумкова робота": "📋",
    "узагальнення знань": "📚",
    "контроль аудіювання": "🎧",
    "узагальнення теми": "📖",
    "практична робота": "🔬",
    "тематичне оцінювання": "⭐",
    "інструктаж бдж": "⚠️",
}


def send_message(text: str):
    """Надсилає довільний текст в Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_TOKEN або TELEGRAM_CHAT_ID не задані в Environment Variables!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Повідомлення надіслано в Telegram")
            return True
        else:
            logger.error(f"❌ Telegram API помилка {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Немає з'єднання з Telegram")
        return False
    except Exception as e:
        logger.error(f"❌ Невідома помилка: {e}")
        return False


def send_notification(task: dict):
    """Формує повідомлення про важливе завдання і надсилає в Telegram"""
    keyword = task.get("keyword", "")
    emoji = KEYWORD_EMOJI.get(keyword, "📌")
    text = task.get("text", "").strip()

    # Обрізаємо якщо дуже довгий текст
    if len(text) > 500:
        text = text[:500] + "..."

    message = (
        f"{emoji} *ВАЖЛИВЕ ЗАВДАННЯ*\n"
        f"{'─' * 25}\n"
        f"*Тип:* {keyword.title()}\n\n"
        f"*Деталі:*\n{text}"
    )

    send_message(message)


def send_startup_message():
    """Надсилає повідомлення при запуску бота — для перевірки що все працює"""
    send_message("✅ *Human Bot запущено!*\nБуду надсилати сповіщення про важливі завдання.")
