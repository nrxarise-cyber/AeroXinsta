import asyncio
import random
import os
import sys
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

# Environment Token fetching
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("🚨 ERROR: BOT_TOKEN environment variable missing!")
    sys.exit(1)

bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def human_type(element, text):
    try:
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.15, 0.3))
    except Exception as e:
        print(f"Typing error: {e}")

async def create_insta_account(chat_id, base_email):
    # Pure block ko isolated try-except me rakha hai taaki bot crash na ho
    try:
        await bot.send_message(chat_id, "🚀 [Railway Worker] Engine spin up started...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, 
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                locale="en-US"
            )
            
            # Anti-fingerprint injection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            
            page = await context.new_page()
            
            await bot.send_message(chat_id, "🌐 Navigation to Instagram registration pathway...")
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="domcontentloaded", timeout=50000)
            await asyncio.sleep(5)

            target_selector = 'input[name="emailOrPhone"], input[name="email"], input[type="text"]'
            
            try:
                # Dynamic visibility check
                await page.wait_for_selector(target_selector, state="visible", timeout=25000)
            except Exception:
                # Strict dynamic screenshot block
                ss_path = f"error_{chat_id}.png"
                await page.screenshot(path=ss_path, full_page=True)
                
                with open(ss_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id, 
                        photo, 
                        caption="🚨 Automation Layer Timeout. Element hidden. Visual payload attached."
                    )
                
                if os.path.exists(ss_path):
                    os.remove(ss_path)
                    
                page_title = await page.title()
                raise Exception(f"Instagram security triggered. Title: '{page_title}'")

            # Field Interaction
            email_field = page.locator(target_selector).first
            await email_field.click()
            await human_type(email_field, base_email)
            await asyncio.sleep(2)

            next_btn = page.locator('button[type="submit"], button:has-text("Next")').first
            await next_btn.click()
            await asyncio.sleep(5)
            
            await bot.send_message(chat_id, f"📩 Account stage initialized for: {base_email}")
            await browser.close()

    except Exception as e:
        try:
            await bot.send_message(chat_id, f"🚨 Runtime exception handled:\n`{str(e)}`")
        except Exception as telegram_error:
            print(f"Failed to send telegram message: {telegram_error}")

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    # Task context encapsulation to prevent loop hijacking
    asyncio.create_task(create_insta_account(message.chat.id, email))

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "⚡ Bot status: ONLINE\nSend targets containing '@' syntax.")

async def main():
    print("🤖 Production Engine Active. Connecting to Telegram Polling API...")
    try:
        await bot.infinity_polling(timeout=60, long_polling_timeout=5)
    except Exception as e:
        print(f"Polling crashed: {e}")
        await asyncio.sleep(5)

if __name__ == "__main__":
    # Event loop management logic for server dependencies
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(main())
