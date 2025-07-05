import nest_asyncio
nest_asyncio.apply()

import os
import time
import asyncio
import subprocess
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from fastapi import FastAPI
import uvicorn

# FastAPI instance
app_web = FastAPI()

@app_web.get("/")
def home():
    return {"status": "JNVU Bot is running on Render"}

# Telegram bot config
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_DIR = "downloads"
RECORD_PATH = "session_recording.mp4"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.environ["DISPLAY"] = ":0"

driver = None
display_screen = None
ffmpeg_process = None

bot = Client("jnvu_result_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
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

@bot.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
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

def start_bot():
    asyncio.run(bot.start())
    asyncio.get_event_loop().run_until_complete(asyncio.Event().wait())

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
