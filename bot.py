# Install Chrome version 136
# Run in Colab only. Not required in deployment.
# !wget -q https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.113/linux64/chrome-linux64.zip
# !unzip -q chrome-linux64.zip
# !mv chrome-linux64 /opt/chrome
# !ln -sf /opt/chrome/chrome /usr/bin/google-chrome

# !rm -f /usr/local/bin/chromedriver
# !wget -q -O chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.113/linux64/chromedriver-linux64.zip
# !unzip -o chromedriver.zip
# !mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
# !chmod +x /usr/local/bin/chromedriver

import nest_asyncio
nest_asyncio.apply()

import os
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display

API_ID = 28590286
API_HASH = "6a68cc6b41219dc57b7a52914032f92f"
BOT_TOKEN = "7412939071:AAFgfHJGhMXw9AuGAAnPuGk_LbAlB5kX2KY"
# NEW (Render-compatible path)
DOWNLOAD_DIR = "downloads"
RECORD_PATH = "session_recording.mp4"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.environ["DISPLAY"] = ":0"

driver = None
display_screen = None
ffmpeg_process = None

app = Client("jnvu_result_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    global driver, display_screen, ffmpeg_process
    await message.reply("🧑‍💻 Starting browser & screen recording...")

    if driver is None:
        display_screen = Display(visible=0, size=(1280, 720))
        display_screen.start()
        time.sleep(2)

        ffmpeg_process = subprocess.Popen([
            "ffmpeg", "-y",
            "-video_size", "1280x720",
            "-f", "x11grab",
            "-i", ":0.0",
            "-r", "25", RECORD_PATH
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        chrome_options = Options()
        chrome_options.binary_location = "/opt/chrome/chrome"
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

        driver.get("https://share.google/RiGoUdAWQEkczypqg")
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/form/div[3]/div/div[1]/fieldset/div/div[1]/div/div[1]/table/tbody/tr[2]/td/div/div/ul/li[1]/span[3]/a").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/form/div[3]/div/div/fieldset/div/div[3]/div/div/div/table/tbody/tr[2]/td/div/ul/div/table/tbody/tr[2]/td[2]/span[1]/a").click()
        time.sleep(2)

        await message.reply("✅ Bot is ready! Now send your roll number like `25rba00299`.")

@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_roll_number(client: Client, message: Message):
    global driver
    roll_number = message.text.strip()

    if not (6 <= len(roll_number) <= 15 and roll_number.isalnum()):
        await message.reply("❌ Invalid roll number. Use lowercase like `25rba00299`")
        return

    if driver is None:
        await message.reply("❌ Browser not initialized. Send /start first.")
        return

    try:
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith(".pdf"):
                os.remove(os.path.join(DOWNLOAD_DIR, f))

        input_field = driver.find_element(By.XPATH, "/html/body/form/div[4]/div/div[2]/table/tbody/tr/td[2]/span/input")
        input_field.clear()
        input_field.send_keys(roll_number)
        time.sleep(1)

        driver.find_element(By.XPATH, "/html/body/form/div[4]/div/div[3]/span[1]/input").click()
        time.sleep(3)

        timeout = 5
        pdf_path = None
        for _ in range(timeout):
            pdf_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".pdf")]
            if pdf_files:
                pdf_path = os.path.join(DOWNLOAD_DIR, pdf_files[0])
                break
            time.sleep(1)

        if pdf_path and os.path.exists(pdf_path):
            driver.refresh()
            time.sleep(2)
            await message.reply_document(pdf_path, caption=f"✅ Result PDF for Roll Number: `{roll_number}`")
        else:
            await message.reply("📄 Result PDF not found. Please check the roll number.")

    except Exception as e:
        await message.reply(f"❌ Error: `{str(e)}`")

async def main():
    await app.start()
    print("✅ JNVU Result Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
