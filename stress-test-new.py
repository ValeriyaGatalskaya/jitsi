import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Проверка и установка зависимостей
try:
    import selenium
except ImportError:
    subprocess.check_call(["python", "-m", "pip", "install", "selenium"])

# Запрос данных у пользователя
server_address = input("Введите адрес сервера (http(s)//jitsi.meet): ").strip('/')
num_conferences = int(input("Введите количество конференций: "))
num_sessions_per_conference = int(input("Введите количество сессий на конференцию: "))
runtime = int(input("Введите время выполнения теста в секундах: "))
media_option = int(input("Выберите опцию медиа (1 - Видео и Аудио [по умолчанию], 2 - Только видео, 3 - Только аудио, 4 - Нет): ") or 1)
max_concurrent_sessions = int(input("Введите максимальное количество одновременных сессий (например, 10): ") or 10)

# Настройка ChromeDriver
chrome_options = Options()

if media_option in [1, 2]:
    chrome_options.add_argument(f"--use-file-for-fake-video-capture={os.path.abspath('test_video.y4m')}")
if media_option in [1, 3]:
    chrome_options.add_argument(f"--use-file-for-fake-audio-capture={os.path.abspath('test_audio.wav')}")

chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Функция для запуска сессии
def start_session(username, conference_url):
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(conference_url)
    try:
        # Ожидание загрузки конференции и проверка, что пользователь в конференции
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class^='videocontainer']")))
        print(f"\n{username} успешно присоединился к конференции: {conference_url}")
        # Поддержание сессии активной в течение времени теста
        time.sleep(runtime)
    except Exception as e:
        print(f"\n{username} не смог присоединиться к конференции: {conference_url}. Ошибка: {e}")
    finally:
        driver.quit()

# Создание URL конференций с параметрами для пропуска экрана предварительного присоединения
conference_urls = [
    f"{server_address}/StressTestJitsi{i}#userInfo.displayName=%22Checker%22&config.prejoinConfig.enabled=false&config.notifications=[]" 
    for i in range(num_conferences)
]

# Запуск сессий с ограничением на количество одновременных сессий
started_sessions = 0
with ThreadPoolExecutor(max_workers=max_concurrent_sessions) as executor:
    futures = []
    for i, conference_url in enumerate(conference_urls):
        for j in range(num_sessions_per_conference):
            username = f"Test{i}_{j}"
            futures.append(executor.submit(start_session, username, conference_url))
            started_sessions += 1
            print(f"Запущена сессия {started_sessions} из {num_conferences * num_sessions_per_conference}")

    # Ожидание завершения всех сессий
    for future in as_completed(futures):
        future.result()

print("Стресс-тест завершен.")
