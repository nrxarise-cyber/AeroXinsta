import asyncio
import random
import os
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"

session_tracker = {}

def load_proxies_from_file():
    file_path = "proxies.txt"
    proxies = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
    return proxies

async def human_type(element, text):
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.15, 0.35))

async def create_insta_account(chat_id, base_email):
    page = None
    browser = None
    try:
        await bot.send_message(chat_id, "⚙️ Phase 1: Reading configuration data...")
        proxy_pool = load_proxies_from_file()
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        proxy_config = None
        
        if current_proxy:
            current_proxy = current_proxy.strip()
            if len(current_proxy.split(":")) == 4:
                ip, port, user, password = current_proxy.split(":")
                proxy_config = {"server": f"http://{ip}:{port}", "username": user, "password": password}
            else:
                proxy_config = {"server": current_proxy if current_proxy.startswith("http") else f"http://{current_proxy}"}

        await bot.send_message(chat_id, "🌐 Phase 2: Launching Browser...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"]
            )
            
            context = await browser.new_context(
                user_agent=USER_AGENT, proxy=proxy_config,
                viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True,
                locale="en-US", timezone_id="Asia/Kolkata"
            )
            
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            await bot.send_message(chat_id, "🚀 Phase 3: Opening Instagram...")
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle", timeout=45000)
            await asyncio.sleep(5)

            # --- STEP 1: GMAIL ENTER KARNA ---
            try:
                email_input = await page.wait_for_selector('input[name="emailOrPhone"], input[autocomplete="email"], input[type="text"]', timeout=7000)
                await email_input.click()
                await human_type(email_input, base_email)
            except Exception:
                await bot.send_message(chat_id, "🔄 Switching layout to Email input...")
                # FIXED: Removed await from page.locator
                switch_to_email_btn = page.locator('text=/Sign up with email|Use email instead|email/i').first
                await switch_to_email_btn.wait_for(state="visible", timeout=5000)
                await switch_to_email_btn.click()
                await asyncio.sleep(3)
                
                email_input = await page.wait_for_selector('input[name="emailOrPhone"], input[type="text"]', timeout=5000)
                await email_input.click()
                await human_type(email_input, base_email)

            # Gmail daalne ke baad Next button dabana
            # FIXED: Removed await from page.locator
            next_btn = page.locator('button[type="submit"], button:has-text("Next"), form button').first
            await next_btn.click()
            await asyncio.sleep(5)

            # --- STEP 2: OTP SELECTION & WAITING ---
            await bot.send_message(chat_id, "📩 Code bhej diya hai lala! Jaldi se sirf OTP code likh kar bhejo.")
            
            event = asyncio.Event()
            session_tracker[chat_id] = {"event": event, "otp": None}

            try:
                await asyncio.wait_for(event.wait(), timeout=60.0)
                otp_received = session_tracker[chat_id]["otp"]
            except asyncio.TimeoutError:
                otp_received = None

            if not otp_received:
                await bot.send_message(chat_id, "❌ Time khatam! Tumne OTP nahi diya.")
                await browser.close()
                return

            # OTP Input fill karna
            otp_input = await page.wait_for_selector('input[name="email_confirmation_code"], input[type="number"], input[pattern="[0-9]*"]', timeout=10000)
            await otp_input.click()
            await human_type(otp_input, otp_received)
            
            # FIXED: Removed await from page.locator
            next_btn = page.locator('button[type="submit"], button:has-text("Next"), form button').first
            await next_btn.click()
            await asyncio.sleep(6)

            # --- STEP 3: PASSWORD SET KARNA ---
            await bot.send_message(chat_id, "🔑 Password set kar raha hoon...")
            password = "KhatarnakPass#" + str(random.randint(111, 999))
            
            pass_input = await page.wait_for_selector('input[type="password"], input[name="password"]', timeout=10000)
            await pass_input.click()
            await human_type(pass_input, password)
            
            # FIXED: Removed await from page.locator
            next_btn = page.locator('button[type="submit"], button:has-text("Next"), form button').first
            await next_btn.click()
            await asyncio.sleep(6)

            # --- STEP 4: BIRTHDAY SET KARNA ---
            await bot.send_message(chat_id, "🎂 Birthday page bypass kar raha hoon...")
            try:
                # FIXED: Removed await from page.locator
                next_btn = page.locator('button[type="submit"], button:has-text("Next"), form button').first
                await next_btn.click()
                await asyncio.sleep(6)
            except Exception:
                pass

            # --- STEP 5: USERNAME SET KARNA ---
            await bot.send_message(chat_id, "👤 Username handle add kar raha hoon...")
            username = "bhai_ka_acc_" + str(random.randint(10000, 99999))
            try:
                user_input = await page.wait_for_selector('input[name="username"], input[type="text"]', timeout=5000)
                await user_input.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await human_type(user_input, username)
            except Exception:
                pass

            # Final Sign Up / Next Button
            try:
                # FIXED: Removed await from page.locator
                signup_btn = page.locator('button[type="submit"], button:has-text("Sign up"), button:has-text("Next")').first
                await signup_btn.click()
                await asyncio.sleep(10)
            except Exception:
                pass

            if "challenge" in page.url or "checkpoint" in page.url:
                await bot.send_message(chat_id, "⚠️ Account flagged! Change proxy IP pool rotation settings.")
                await browser.close()
                return

            await bot.send_message(chat_id, f"🔥 Boom! Account Taiyar:\n👤 User: {username}\n🔑 Pass: {password}")
            await browser.close()

    except Exception as e:
        try:
            if page:
                screenshot_path = f"error_final_{chat_id}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                with open(screenshot_path, "rb") as photo:
                    await bot.send_photo(chat_id, photo, caption=f"🚨 Engine Ruled Out Here:\n`{str(e)}`")
                if os.path.exists(screenshot_path): 
                    os.remove(screenshot_path)
            else:
                await bot.send_message(chat_id, f"🚨 CRITICAL SYSTEM ERROR (Browser Not Initiated):\n`{str(e)}`")
        except Exception:
            await bot.send_message(chat_id, f"🚨 CRITICAL SYSTEM ERROR:\n`{str(e)}`")
    finally:
        session_tracker.pop(chat_id, None)

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Railway Engine Configured! Gmail bhejo setup load karte hain.")

@bot.message_handler(func=lambda message: message.chat.id in session_tracker and message.text.isdigit())
async def capture_otp(message):
    chat_id = message.chat.id
    session_tracker[chat_id]["otp"] = message.text.strip()
    session_tracker[chat_id]["event"].set()
    await bot.reply_to(message, "🔄 OTP Processing...")

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    asyncio.create_task(create_insta_account(message.chat.id, email))

if __name__ == "__main__":
    print("🤖 Bot initialization process live...")
    asyncio.run(bot.infinity_polling(timeout=60))
