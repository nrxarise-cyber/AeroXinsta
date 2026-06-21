import asyncio
import random
import os
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"

waiting_for_otp = {}

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
        await asyncio.sleep(random.uniform(0.15, 0.35))  # Thoda zyada natural delay

async def create_insta_account(chat_id, base_email):
    async with async_playwright() as p:
        proxy_pool = load_proxies_from_file()
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        proxy_config = {"server": current_proxy} if current_proxy else None

        await bot.send_message(chat_id, "🤖 Engine start ho raha hai...")

        # STEALTH ARGS: Browser ko undetectable banane ke liye extra arguments
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certificate-errors"
            ]
        )
        
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 360, "height": 740},
            is_mobile=True,
            has_touch=True,
            proxy=proxy_config,
            locale="en-US",
            timezone_id="Asia/Kolkata"
        )
        
        page = await context.new_page()
        
        # Super Stealth: Webdriver detect hone se bachane ke liye advanced bypass
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        try:
            await bot.send_message(chat_id, "🌐 Instagram Signup Page par jaa raha hoon...")
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(4, 6)) # Natural wait

            username = "bhai_ka_acc_" + str(random.randint(10000, 99999))
            password = "KhatarnakPass#" + str(random.randint(100, 999))

            await bot.send_message(chat_id, f"✍️ Details fill kar raha hoon...\nUser: {username}")

            # Instagram ke badalte hue selectors ke liye backup selectors use kiye hain
            email_input = await page.wait_for_selector('input[name="emailOrPhone"], input[type="text"]', timeout=20000)
            await email_input.click() # Pehle click karo jaise insan karta hai
            await asyncio.sleep(0.5)
            await human_type(email_input, base_email)

            name_input = await page.wait_for_selector('input[name="fullName"]')
            await name_input.click()
            await asyncio.sleep(0.5)
            await human_type(name_input, "Rockstar Bhai")

            user_input = await page.wait_for_selector('input[name="username"]')
            await user_input.click()
            await asyncio.sleep(0.5)
            await human_type(user_input, username)

            pass_input = await page.wait_for_selector('input[name="password"]')
            await pass_input.click()
            await asyncio.sleep(0.5)
            await human_type(pass_input, password)

            await asyncio.sleep(2)
            
            # Submit button dhoondhne ka advanced tareeka
            signup_btn = await page.wait_for_selector('button[type="submit"], button:has-text("Sign up")', timeout=15000)
            await signup_btn.click()
            
            await asyncio.sleep(5)
            
            # Check if blocked or challenged right away
            if "challenge" in page.url or "checkpoint" in page.url:
                await bot.send_message(chat_id, "⚠️ Oops! Instagram ne Robot/Captcha challenge de diya. Proxy change karni padegi.")
                await browser.close()
                return

            await bot.send_message(chat_id, "📩 Code bhej diya hai lala! Jaldi se sirf OTP code likh kar bhejo.")

            waiting_for_otp[chat_id] = None
            otp_received = None
            for _ in range(60):
                if waiting_for_otp.get(chat_id) is not None:
                    otp_received = waiting_for_otp[chat_id]
                    break
                await asyncio.sleep(1)

            if chat_id in waiting_for_otp:
                del waiting_for_otp[chat_id]

            if not otp_received:
                await bot.send_message(chat_id, "❌ Time khatam! Tumne OTP nahi diya.")
                await browser.close()
                return

            otp_input = await page.wait_for_selector('input[name="email_confirmation_code"], input[type="num"]', timeout=15000)
            await otp_input.click()
            await human_type(otp_input, otp_received)
            await asyncio.sleep(1.5)
            
            confirm_btn = await page.wait_for_selector('button[type="submit"]')
            await confirm_btn.click()
            
            await asyncio.sleep(10)
            await bot.send_message(chat_id, f"🔥 Boom! Account Taiyar:\n👤 User: {username}\n🔑 Pass: {password}")

        except Exception as e:
            # Agar fail ho jaye toh screen ka screenshot lelo samajhne ke liye (Railway par debug ke liye best hai)
            try:
                await page.screenshot(path=f"error_{chat_id}.png")
                with open(f"error_{chat_id}.png", "rb") as photo:
                    await bot.send_photo(chat_id, photo, caption=f"⚠️ Error ke waqt screen aisi dikh rahi thi: {str(e)}")
                os.remove(f"error_{chat_id}.png")
            except:
                await bot.send_message(chat_id, f"⚠️ Error aa gaya lala: {str(e)}")
        
        finally:
            await browser.close()

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Railway System Online! Gmail bhejo, account banate hain.")

@bot.message_handler(func=lambda message: message.chat.id in waiting_for_otp and message.text.isdigit())
async def capture_otp(message):
    waiting_for_otp[message.chat.id] = message.text.strip()
    await bot.reply_to(message, "🔄 OTP mil gaya! Verify kar raha hoon...")

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    asyncio.create_task(create_insta_account(message.chat.id, email))

if __name__ == "__main__":
    import time
    
    while True:
        try:
            print("🤖 Bot is starting cleanly...")
            # infinity_polling automated restarts ko smoothly handle karta hai
            asyncio.run(bot.infinity_polling(timeout=60, long_polling_timeout=30))
        except Exception as e:
            print(f"⚠️ Polling connection conflict: {e}")
            print("⏳ Waiting 20 seconds for Telegram to clear old session...")
            time.sleep(20) # Yeh Railway ko thanda rakhega
