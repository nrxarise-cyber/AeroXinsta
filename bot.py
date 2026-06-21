import asyncio
import random
import os
import sys
import re
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

# Environment Variables fetching
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("🚨 ERROR: BOT_TOKEN environment variable missing!")
    sys.exit(1)

bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
PROXY_FILE = "proxies.txt"

def get_parsed_proxy():
    """proxies.txt file se random proxy utha kar usey Playwright format me parse karta hai"""
    if not os.path.exists(PROXY_FILE):
        return None
        
    with open(PROXY_FILE, "r") as f:
        # Khali lines aur comments (#) ko filter out karne ke liye
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not proxies:
        return None
        
    raw_proxy = random.choice(proxies)
    
    # Regex formula: http://user:pass@ip:port ya http://ip:port dono ko parse karne ke liye
    match = re.match(r'(?:https?://)?(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', raw_proxy)
    
    if match:
        username, password, ip, port = match.groups()
        proxy_config = {"server": f"http://{ip}:{port}"}
        if username and password:
            proxy_config["username"] = username
            proxy_config["password"] = password
        return proxy_config
    
    return {"server": raw_proxy}

async def human_type(element, text):
    """Insano ki tarah thoda ruk-ruk kar type karne ke liye"""
    try:
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.1, 0.25))
    except Exception as e:
        print(f"Typing error: {e}")

async def create_insta_account(chat_id, base_email):
    ss_path = f"ss_{chat_id}.png"
    try:
        await bot.send_message(chat_id, "🚀 [Railway Worker] Engine spinning up with strict network layers...")
        
        async with async_playwright() as p:
            launch_args = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            }
            
            # 🔄 PROXY LOADING LOGIC
            proxy_config = get_parsed_proxy()
            if proxy_config:
                launch_args["proxy"] = proxy_config
                # Safe log formatting: Telegram par user/pass leak na ho, sirf IP:Port dikhe
                clean_server = proxy_config["server"].split('@')[-1]
                await bot.send_message(chat_id, f"🌐 Proxy Authenticated & Loaded: `{clean_server}`")
            else:
                await bot.send_message(chat_id, f"⚠️ Warning: '{PROXY_FILE}' empty/missing. Running on default host IP.")

            browser = await p.chromium.launch(**launch_args)
            
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                locale="en-US"
            )
            
            # Webdriver fingerprint bypass script inject karna
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page = await context.new_page()
            
            await bot.send_message(chat_id, "🌐 Launching Instagram sign-up gateway...")
            
            try:
                await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle", timeout=60000)
            except Exception as net_err:
                raise Exception(f"Network/Proxy Error: Page failed to load. Proxy dead ho sakti hai. Details: {net_err}")
                
            await asyncio.sleep(4)

            # --- 📱 MOBILE LAYOUT DETECTION & INSTANT EMAIL SWITCH ---
            email_instead_btn = page.locator('button:has-text("Sign up with email instead"), span:has-text("Sign up with email")').first
            if await email_instead_btn.is_visible():
                await bot.send_message(chat_id, "📱 Mobile UI/Phone layout detected. Switching to Email interface...")
                await email_instead_btn.click()
                await asyncio.sleep(2)

            target_selector = 'input[name="emailOrPhone"], input[name="email"], input[type="text"]'
            
            try:
                await page.wait_for_selector(target_selector, state="visible", timeout=20000)
            except Exception:
                # Agar element na mile toh instant screenshot bhej kar block error dena
                await page.screenshot(path=ss_path, full_page=True)
                if os.path.exists(ss_path):
                    with open(ss_path, "rb") as photo:
                        await bot.send_photo(chat_id, photo, caption="🚨 Flow blocked. Form element missing. Check snapshot.")
                    os.remove(ss_path)
                page_title = await page.title()
                raise Exception(f"Element validation failed. Title: '{page_title}'")

            # Email Input Field Interaction
            email_field = page.locator(target_selector).first
            await email_field.click()
            await human_type(email_field, base_email)
            await asyncio.sleep(1.5)

            # 🔘 NEXT BUTTON PUSH
            next_btn = page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Sign up")').first
            await next_btn.click()
            await bot.send_message(chat_id, "⏳ 'Next' button clicked. Waiting for security/OTP verification layout...")
            
            # OTP screen transition ke liye safe waiting gap
            await asyncio.sleep(6)
            
            # 📸 OTP SCREENSHOT REPORT
            await page.screenshot(path=ss_path, full_page=True)
            if os.path.exists(ss_path):
                with open(ss_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id, 
                        photo, 
                        caption=f"📩 Target Processed: {base_email}\nNext page sequence captured (OTP / Status Screen Check) 👇"
                    )
                os.remove(ss_path)

            await browser.close()

    except Exception as e:
        try:
            await bot.send_message(chat_id, f"🚨 Execution Exception:\n`{str(e)}`")
        except Exception as telegram_error:
            print(f"Telegram report failed: {telegram_error}")
        finally:
            # File system cleanup safeguard
            if os.path.exists(ss_path):
                os.remove(ss_path)

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    asyncio.create_task(create_insta_account(message.chat.id, email))

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "⚡ Engine: ONLINE\nSend base target emails to execute automated sequence.")

async def main():
    print("🤖 Production Engine Active. Polling Telegram backend...")
    try:
        await bot.infinity_polling(timeout=60, request_timeout=300)
    except Exception as e:
        print(f"Polling crashed: {e}")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🤖 Engine: OFFLINE")
