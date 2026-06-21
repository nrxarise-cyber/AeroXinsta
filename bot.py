import asyncio
import random
import os
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def human_type(element, text):
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.15, 0.3))

async def create_insta_account(chat_id, base_email):
    browser = None
    try:
        await bot.send_message(chat_id, "🚀 Railway Worker: Initializing Headless Engine...")
        
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
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            
            page = await context.new_page()
            
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle", timeout=45000)
            await asyncio.sleep(4)

            target_selector = 'input[name="emailOrPhone"], input[name="email"]'
            
            try:
                # Target input ka wait karega
                await page.wait_for_selector(target_selector, state="visible", timeout=25000)
            except Exception:
                # --- SCREENSHOT LOGIC FOR RAILWAY ---
                # Agar timeout aaya, toh turant screenshot capture karega
                ss_path = f"error_{chat_id}.png"
                await page.screenshot(path=ss_path, full_page=True)
                
                # Telegram par screenshot send karna
                with open(ss_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id, 
                        photo, 
                        caption="🚨 Timeout Error! Instagram field load nahi hua. Server par ye screen dikh rahi hai."
                    )
                
                # File delete karna taaki Railway ka space na bhare
                if os.path.exists(ss_path):
                    os.remove(ss_path)
                    
                page_title = await page.title()
                raise Exception(f"Instagram blocked the server IP. Page Title: '{page_title}'")

            # Agar field mil gaya toh normal flow chalega
            email_field = page.locator(target_selector).first
            await email_field.click()
            await human_type(email_field, base_email)
            await asyncio.sleep(2)

            next_btn = page.locator('button[type="submit"], button:has-text("Next")').first
            await next_btn.click()
            
            await bot.send_message(chat_id, f"📩 Target configured for {base_email}.")

    except Exception as e:
        await bot.send_message(chat_id, f"🚨 Railway Exec Error:\n`{str(e)}`")
    finally:
        if browser:
            await browser.close()

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    asyncio.create_task(create_insta_account(message.chat.id, email))

if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
