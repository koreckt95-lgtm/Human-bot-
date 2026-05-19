import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

HUMAN_EMAIL = os.getenv("HUMAN_EMAIL")
HUMAN_PASSWORD = os.getenv("HUMAN_PASSWORD")

# Ключові слова для фільтрації важливих завдань
KEYWORDS = [
    "контрольна робота",
    "підсумкова робота",
    "узагальнення знань",
    "контроль аудіювання",
    "узагальнення теми",
    "практична робота",
    "тематичне оцінювання",
    "інструктаж бдж",
]


def get_driver():
    """Створює headless Chrome для роботи на Render"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver


def login(driver):
    """Логін на сайт Human"""
    logger.info("Відкриваю сторінку логіну...")
    driver.get("https://id.human.ua/auth/login")
    wait = WebDriverWait(driver, 20)

    try:
        # Чекаємо поле email
        email_input = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            )
        )
        email_input.clear()
        email_input.send_keys(HUMAN_EMAIL)
        time.sleep(0.5)

        # Поле пароля
        password_input = driver.find_element(
            By.CSS_SELECTOR, "input[type='password']"
        )
        password_input.clear()
        password_input.send_keys(HUMAN_PASSWORD)
        time.sleep(0.5)

        # Кнопка входу
        submit_btn = driver.find_element(
            By.CSS_SELECTOR, "button[type='submit']"
        )
        submit_btn.click()

        # Чекаємо поки URL зміниться (вдалий логін)
        wait.until(lambda d: "id.human.ua/auth/login" not in d.current_url)
        logger.info(f"✅ Логін успішний. Поточний URL: {driver.current_url}")
        time.sleep(2)
        return True

    except TimeoutException:
        logger.error("❌ Не вдалось залогінитись — перевір email/пароль")
        return False


def extract_tasks(driver):
    """Шукає важливі завдання на сторінці щоденника"""
    tasks = []

    try:
        # Переходимо на головну сторінку після логіну
        driver.get("https://app.human.ua/")
        time.sleep(3)

        # Пробуємо знайти і відкрити щоденник/розклад
        diary_xpaths = [
            "//a[contains(@href, 'diary')]",
            "//a[contains(@href, 'schedule')]",
            "//a[contains(@href, 'tasks')]",
            "//a[contains(text(), 'Щоденник')]",
            "//a[contains(text(), 'Розклад')]",
            "//span[contains(text(), 'Щоденник')]",
        ]
        for xpath in diary_xpaths:
            try:
                driver.find_element(By.XPATH, xpath).click()
                time.sleep(2)
                logger.info(f"Відкрив розділ за xpath: {xpath}")
                break
            except NoSuchElementException:
                continue

        logger.info(f"Аналізую сторінку: {driver.current_url}")

        # Зчитуємо весь текст сторінки рядками
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = page_text.split("\n")

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if not line_lower:
                continue

            for kw in KEYWORDS:
                if kw in line_lower:
                    # Беремо контекст — 2 рядки до і 4 після
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    context = "\n".join(lines[start:end]).strip()

                    task_id = f"task_{hash(context)}"

                    # Не додаємо дублікати
                    if not any(t["id"] == task_id for t in tasks):
                        tasks.append({
                            "id": task_id,
                            "text": context,
                            "keyword": kw,
                            "url": driver.current_url,
                        })
                        logger.info(f"🎯 Знайдено: [{kw}]")
                    break

    except Exception as e:
        logger.error(f"Помилка при зчитуванні завдань: {e}", exc_info=True)

    logger.info(f"Всього знайдено важливих завдань: {len(tasks)}")
    return tasks


def get_important_tasks():
    """Головна функція — логін + парсинг завдань"""
    driver = None
    try:
        driver = get_driver()
        if not login(driver):
            return []
        return extract_tasks(driver)
    except Exception as e:
        logger.error(f"Критична помилка парсера: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()
            logger.info("Браузер закрито")
