import asyncio
import random
import os
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

# Railway ke Environment Variables se token uthayenge
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

# Global dictionary to keep track of waiting OTPs per chat session
waiting_for_otp = {}

def load_proxies_from_file():
    """Repo ke andar se proxies.txt file read karne ke liye function"""
    file_path = "proxies.txt"
    proxies = []
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                # Khali lines ya comment (#) ko skip karne ke liye
                if line and not line.startswith("#"):
                    proxies.append(line)
        print(f"📦 Repo se total {len(proxies)} proxies load ho gayi hain.")
    else:
        print("⚠️ proxies.txt file nahi mili! Bina proxy ke chal raha hai.")
        
    return proxies

async def human_type(element, text):
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.1, 0.3))

async def create_insta_account(chat_id, base_email):
    async with async_playwright() as p:
        # Har baar function chalne par file se fresh proxies load karega
        proxy_pool = load_proxies_from_file()
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        proxy_config = {"server": current_proxy} if current_proxy else None

        if current_proxy:
            await bot.send_message(chat_id, f"🤖 Proxy Connected: {current_proxy.split('@')[-1] if '@' in current_proxy else current_proxy}")
        else:
            await bot.send_message(chat_id, "⚠️ Warning: Bina proxy ke browser start ho raha hai!")

        # Server par headless=True hi chalega
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 360, "height": 740},
            is_mobile=True,
            has_touch=True,
            proxy=proxy_config
        )
        
        page = await context.new_page()
        await page.add_init_script("delete navigator.__proto__.webdriver;")

        try:
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)

            username = "bhai_ka_acc_" + str(random.randint(10000, 99999))
            password = "KhatarnakPass#" + str(random.randint(100, 999))

            await bot.send_message(chat_id, f"✍️ Details fill kar raha hoon...\nUser: {username}")

            email_input = await page.wait_for_selector('input[name="emailOrPhone"]', timeout=15000)
            await human_type(email_input, base_email)

            name_input = await page.wait_for_selector('input[name="fullName"]')
            await human_type(name_input, "Rockstar Bhai")

            user_input = await page.wait_for_selector('input[name="username"]')
            await human_type(user_input, username)

            pass_input = await page.wait_for_selector('input[name="password"]')
            await human_type(pass_input, password)

            signup_btn = await page.wait_for_selector('button[type="submit"]')
            await signup_btn.click()
            
            await bot.send_message(chat_id, "📩 Insta ne OTP bhej diya! Jaldi se sirf OTP code likh kar bhejo.")

            # Session register karo ki hum OTP ka wait kar rahe hain
            waiting_for_otp[chat_id] = None
            
            otp_received = None
            for _ in range(60):
                if waiting_for_otp.get(chat_id) is not None:
                    otp_received = waiting_for_otp[chat_id]
                    break
                await asyncio.sleep(1)

            # Session clear karo
            if chat_id in waiting_for_otp:
                del waiting_for_otp[chat_id]

            if not otp_received:
                await bot.send_message(chat_id, "❌ Time khatam! Tumne OTP nahi diya.")
                await browser.close()
                return

            otp_input = await page.wait_for_selector('input[name="email_confirmation_code"]', timeout=10000)
            await human_type(otp_input, otp_received)
            
            confirm_btn = await page.wait_for_selector('button[type="submit"]')
            await confirm_btn.click()
            
            await asyncio.sleep(8)
            await bot.send_message(chat_id, f"🔥 Boom! Account Taiyar:\n👤 User: {username}\n🔑 Pass: {password}")

        except Exception as e:
            await bot.send_message(chat_id, f"⚠️ Error aa gaya lala: {str(e)}")
        
        finally:
            await browser.close()

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Railway System Online! Gmail bhejo, account banate hain.")

@bot.message_handler(func=lambda message: message.chat.id in waiting_for_otp and message.text.isdigit())
async def capture_otp(message):
    waiting_for_otp[message.chat.id] = message.text.strip()
    await bot.reply_to(message, "🔄 OTP mil gaya! Fill kar raha hoon...")

@bot.message_handler(func=lambda message: "@" in message.text)
async def start_automation(message):
    email = message.text.strip()
    # Task ko background mein daal rahe hain taaki bot crash ya freeze na ho
    asyncio.create_task(create_insta_account(message.chat.id, email))

if __name__ == "__main__":
    print("Bot is polling on Railway with Async Architecture...")
    asyncio.run(bot.polling(non_stop=True))
