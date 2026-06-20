import asyncio
import random
import os
import telebot
from playwright.async_api import async_playwright

# Railway ke Environment Variables se token uthayenge
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Apni 4G/5G proxies yahan daalna mat bhoolna
PROXY_POOL = [
    # "http://username:password@ip:port"
]

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

async def human_type(element, text):
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.1, 0.3))

async def create_insta_account(chat_id, base_email):
    async with async_playwright() as p:
        current_proxy = random.choice(PROXY_POOL) if PROXY_POOL else None
        proxy_config = {"server": current_proxy} if current_proxy else None

        bot.send_message(chat_id, "🤖 Railway server par browser start ho raha hai...")

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

            email_to_use = base_email
            username = "bhai_ka_acc_" + str(random.randint(10000, 99999))
            password = "KhatarnakPass#" + str(random.randint(100, 999))

            bot.send_message(chat_id, f"✍️ Details fill kar raha hoon...\nUser: {username}")

            email_input = await page.wait_for_selector('input[name="emailOrPhone"]', timeout=15000)
            await human_type(email_input, email_to_use)

            name_input = await page.wait_for_selector('input[name="fullName"]')
            await human_type(name_input, "Rockstar Bhai")

            user_input = await page.wait_for_selector('input[name="username"]')
            await human_type(user_input, username)

            pass_input = await page.wait_for_selector('input[name="password"]')
            await human_type(pass_input, password)

            signup_btn = await page.wait_for_selector('button[type="submit"]')
            await signup_btn.click()
            
            bot.send_message(chat_id, "📩 Insta ne OTP bhej diya! Jaldi se reply mein sirf OTP code likh kar bhejo.")

            otp_received = None
            
            # OTP capture karne ke liye handler
            @bot.message_handler(func=lambda msg: msg.chat.id == chat_id and msg.text.isdigit())
            def handle_otp(msg):
                nonlocal otp_received
                otp_received = msg.text

            # 60 seconds ka wait
            for _ in range(60):
                if otp_received:
                    break
                await asyncio.sleep(1)

            if not otp_received:
                bot.send_message(chat_id, "❌ Time khatam! Tumne OTP nahi diya.")
                await browser.close()
                return

            otp_input = await page.wait_for_selector('input[name="email_confirmation_code"]', timeout=10000)
            await human_type(otp_input, otp_received)
            
            confirm_btn = await page.wait_for_selector('button[type="submit"]')
            await confirm_btn.click()
            
            await asyncio.sleep(8)
            bot.send_message(chat_id, f"🔥 Boom! Account Taiyar:\n👤 User: {username}\n🔑 Pass: {password}")

        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Error aa gaya lala: {str(e)}")
        
        await browser.close()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Railway System Online! Gmail bhejo, account banate hain.")

@bot.message_handler(func=lambda message: "@" in message.text)
def start_automation(message):
    email = message.text.strip()
    asyncio.run(create_insta_account(message.chat.id, email))

print("Bot is polling on Railway...")
bot.polling(none_stop=True)