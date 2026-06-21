import asyncio
import random
import os
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"

# Advanced session handling updates
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
    try:
        await bot.send_message(chat_id, "⚙️ Phase 1: Reading configuration data...")
        proxy_pool = load_proxies_from_file()
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        
        proxy_config = None
        
        # --- SMART PROXY AUTH PARSING ---
        if current_proxy:
            current_proxy = current_proxy.strip()
            if len(current_proxy.split(":")) == 4:
                ip, port, user, password = current_proxy.split(":")
                proxy_config = {
                    "server": f"http://{ip}:{port}",
                    "username": user,
                    "password": password
                }
            elif "@" in current_proxy and ":" in current_proxy:
                try:
                    auth_part, ip_part = current_proxy.split("@")
                    user, password = auth_part.split(":")
                    proxy_config = {
                        "server": f"http://{ip_part}",
                        "username": user,
                        "password": password
                    }
                except Exception:
                    proxy_config = {"server": f"http://{current_proxy}"}
            else:
                if not current_proxy.startswith("http"):
                    proxy_config = {"server": f"http://{current_proxy}"}
                else:
                    proxy_config = {"server": current_proxy}

        await bot.send_message(chat_id, "🌐 Phase 2: Launching Browser Core on Railway...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            
            await bot.send_message(chat_id, "📱 Phase 3: Synchronizing residential proxy handshake...")
            context = await browser.new_context(
                user_agent=USER_AGENT,
                proxy=proxy_config,
                viewport={"width": 360, "height": 740},
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="Asia/Kolkata"
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)

            await bot.send_message(chat_id, "🚀 Phase 4: Fetching Instagram register endpoint...")
            await page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle", timeout=45000)
            await asyncio.sleep(5)

            username = "bhai_ka_acc_" + str(random.randint(10000, 99999))
            password = "KhatarnakPass#" + str(random.randint(100, 999))

            await bot.send_message(chat_id, f"✍️ Details fill kar raha hoon...\nUser: {username}")

            # --- NAYA MOBILE-VIEW AND EMAIL SWITCH LOGIC ---
            try:
                # Pehle check karte hain agar direct email box dikh jaye
                email_input = await page.wait_for_selector('input[name="emailOrPhone"], input[autocomplete="email"]', timeout=5000)
                await email_input.click()
                await human_type(email_input, base_email)
            except Exception:
                try:
                    # Agar nahi mila, toh matlab mobile view par "Sign up with email" par click karna padega
                    await bot.send_message(chat_id, "🔗 Mobile view detected! Switching to Email sign-up tab...")
                    
                    # Alag-alag tarike se text ya button dhoond raha hai (Taaki miss na ho)
                    switch_to_email_btn = await page.wait_for_selector(
                        'role=button[name=/Sign up with email/i], text="Sign up with email", text="Use email instead"', 
                        timeout=8000
                    )
                    await switch_to_email_btn.click()
                    await asyncio.sleep(2) # Chhota sa pause tab change hone ke liye
                    
                    # Ab firse email box dhoondte hain
                    email_input = await page.wait_for_selector('input[name="emailOrPhone"], input[autocomplete="email"], input[type="text"]', timeout=10000)
                    await email_input.click()
                    await human_type(email_input, base_email)
                    
                except Exception as select_err:
                    # Agar ab bhi fail ho toh hi screenshot bhejega
                    screenshot_path = f"error_{chat_id}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    with open(screenshot_path, "rb") as photo:
                        await bot.send_photo(chat_id, photo, caption="❌ Tab badal nahi paya ya box abhi bhi nahi mila!")
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                    raise select_err

            # --- BAAKI DETAILS FILL KARNA ---
            name_input = await page.wait_for_selector('input[name="fullName"]', timeout=10000)
            await name_input.click()
            await human_type(name_input, "Rockstar Bhai")

            user_input = await page.wait_for_selector('input[name="username"]', timeout=10000)
            await user_input.click()
            await human_type(user_input, username)

            pass_input = await page.wait_for_selector('input[name="password"]', timeout=10000)
            await pass_input.click()
            await human_type(pass_input, password)

            await asyncio.sleep(2)
            signup_btn = await page.wait_for_selector('button[type="submit"], button:has-text("Sign up")', timeout=15000)
            await signup_btn.click()
            
            await asyncio.sleep(5)
            
            if "challenge" in page.url or "checkpoint" in page.url:
                await bot.send_message(chat_id, "⚠️ Account flagged! Change proxy IP pool rotation settings.")
                await browser.close()
                return

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

            otp_input = await page.wait_for_selector('input[name="email_confirmation_code"], input[type="num"]', timeout=15000)
            await otp_input.click()
            await human_type(otp_input, otp_received)
            await asyncio.sleep(1.5)
            
            confirm_btn = await page.wait_for_selector('button[type="submit"]', timeout=10000)
            await confirm_btn.click()
            
            await asyncio.sleep(10)
            await bot.send_message(chat_id, f"🔥 Boom! Account Taiyar:\n👤 User: {username}\n🔑 Pass: {password}")
            await browser.close()

    except Exception as e:
        await bot.send_message(chat_id, f"🚨 ENGINE FAILURE SYSTEM REPORT:\n`{str(e)}`", parse_mode="Markdown")
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
