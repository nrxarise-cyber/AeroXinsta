import asyncio
import random
import os
import sys
import re
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright
# FIX: stealth module se specific stealth_sync function import kiya
from playwright_stealth import stealth_sync

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("🚨 ERROR: BOT_TOKEN missing!")
    sys.exit(1)

bot = AsyncTeleBot(BOT_TOKEN)
PROXY_FILE = "proxies.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def get_parsed_proxy():
    if not os.path.exists(PROXY_FILE):
        return None
    with open(PROXY_FILE, "r") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not proxies:
        return None
    
    raw_proxy = random.choice(proxies)
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
    try:
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.1, 0.25))
    except Exception as e:
        print(f"Typing error: {e}")

async def create_insta_account(chat_id, base_email):
    ss_path = f"ss_{chat_id}.png"
    await bot.send_message(chat_id, "🚀 [Worker] Initializing environment modules...")
    
    try:
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
            
            proxy_config = get_parsed_proxy()
            if proxy_config:
                launch_args["proxy"] = proxy_config
                clean_server = proxy_config["server"].split('@')[-1]
                await bot.send_message(chat_id, f"🌐 Proxy Loaded: `{clean_server}`")
            else:
                await bot.send_message(chat_id, "⚠️ Running on default host IP (No proxy).")

            async with await p.chromium.launch(**launch_args) as browser:
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1280, "height": 720},
                    locale="en-US"
                )
                
                page = await context.new_page()
                
                # FIX: stealth_sync use kiya jo module callable issue ko crash nahi hone deta
                stealth_sync(page)
                
                await bot.send_message(chat_id, "🌐 Loading registration gateway...")
                
                try:
                    await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="domcontentloaded", timeout=45000)
                except Exception as net_err:
                    raise Exception(f"Network/Proxy Timeout: {net_err}")
                    
                await asyncio.sleep(3)

                email_instead_btn = page.locator('button:has-text("Sign up with email instead"), span:has-text("Sign up with email")').first
                if await email_instead_btn.is_visible():
                    await bot.send_message(chat_id, "📱 Phone layout detected. Switching interface...")
                    await email_instead_btn.click()
                    await asyncio.sleep(2)

                target_selector = 'input[name="emailOrPhone"], input[name="email"], input[type="text"]'
                
                try:
                    await page.wait_for_selector(target_selector, state="visible", timeout=15000)
                except Exception:
                    try:
                        await page.screenshot(path=ss_path, full_page=False, timeout=3000)
                    except Exception as ss_err:
                        print(f"Screenshot failed: {ss_err}")

                    if os.path.exists(ss_path):
                        with open(ss_path, "rb") as photo:
                            await bot.send_photo(chat_id, photo, caption="🚨 Verification element missing.")
                        os.remove(ss_path)
                    
                    page_title = await page.title()
                    raise Exception(f"Form Element Not Found. Current Title: '{page_title}'")

                email_field = page.locator(target_selector).first
                await email_field.click()
                await human_type(email_field, base_email)
                await asyncio.sleep(1.5)

                next_btn = page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Sign up")').first
                await next_btn.click()
                await bot.send_message(chat_id, "⏳ Sequence triggered. Fetching response interface...")
                
                await asyncio.sleep(6)
                
                try:
                    await page.screenshot(path=ss_path, full_page=False, timeout=3000)
                except Exception as ss_err:
                    print(f"Final screenshot failed: {ss_err}")

                if os.path.exists(ss_path):
                    with open(ss_path, "rb") as photo:
                        await bot.send_photo(chat_id, photo, caption=f"📩 Result for: {base_email}")
                    os.remove(ss_path)

    except Exception as e:
        print(f"Worker Error: {e}")
        try:
            await bot.send_message(chat_id, f"🚨 Execution Exception:\n`{str(e)}`")
        except Exception as telegram_error:
            print(f"Telegram reporting failed: {telegram_error}")
    finally:
        if os.path.exists(ss_path):
            try:
                os.remove(ss_path)
            except Exception:
                pass

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    task = asyncio.create_task(create_insta_account(message.chat.id, email))
    
    def handle_result(t):
        try:
            t.result()
        except Exception as ex:
            print(f"Task generated an unhandled exception: {ex}")
            
    task.add_done_callback(handle_result)

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "⚡ Automation Engine: ONLINE\nSend target identifier to execute.")

async def main():
    print("🤖 Polling Telegram backend...")
    while True:
        try:
            await bot.infinity_polling(timeout=60, request_timeout=300)
        except Exception as e:
            print(f"Polling crashed, restarting in 5s: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🤖 Engine: OFFLINE")
