
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

# Check and install dependencies
try:
    import selenium
except ImportError:
    subprocess.check_call(["python", "-m", "pip", "install", "selenium"])

# Ask for server address, number of conferences, sessions, runtime, and media options
server_address = input("Please enter the server address (http(s)//jitsi.meet): ").strip('/')
num_conferences = int(input("Please enter the number of conferences: "))
num_sessions_per_conference = int(input("Please enter the number of sessions per conference: "))
runtime = int(input("Please enter the runtime in seconds: "))
media_option = int(input("Choose the media option (1 - Video and Audio [default], 2 - Video only, 3 - Audio only, 4 - None): ") or 1)
max_concurrent_sessions = int(input("Enter the maximum number of concurrent sessions (e.g., 10): ") or 10)

# ChromeDriver configuration
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

# Function to start a session
def start_session(username, conference_url):
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(conference_url)
    try:
        # Wait for the conference to load and check if the user is in the conference
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class^='videocontainer']")))
        print(f"\n{username} successfully joined the conference: {conference_url}")
        # Keep the session alive for the duration of the test
        time.sleep(runtime)
    except Exception as e:
        print(f"\n{username} failed to join the conference: {conference_url}. Error: {e}")
    finally:
        driver.quit()

# Create conference URLs
conference_urls = [f"{server_address}/StressTestJitsi{i}" for i in range(num_conferences)]

# Start sessions with a limit on concurrent sessions
started_sessions = 0
with ThreadPoolExecutor(max_workers=max_concurrent_sessions) as executor:
    futures = []
    for i, conference_url in enumerate(conference_urls):
        for j in range(num_sessions_per_conference):
            username = f"Test{i}_{j}"
            futures.append(executor.submit(start_session, username, conference_url))
            started_sessions += 1
            print(f"Started session {started_sessions} of {num_conferences * num_sessions_per_conference}")

    # Wait for all sessions to complete
    for future in as_completed(futures):
        future.result()

print("Stress test completed.")