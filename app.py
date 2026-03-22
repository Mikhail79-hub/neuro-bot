import os, asyncio, random, aiohttp, socket, time, threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from tavily import TavilyClient

# --- ЗАГЛУШКА ДЛЯ RENDER (чтобы не было Timed Out) ---
app = Flask(__name__)
@app.route('/')
def hello(): return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
CHANNEL_ID = "@neuro_engineer_lab"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

async def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            res = await resp.json()
            return res['choices'][0]['message']['content'] if 'choices' in res else str(res)

def get_image_url(prompt_en):
    seed = random.randint(1, 999999)
    clean_prompt = "".join(c for c in prompt_en if c.isalnum() or c.isspace()).replace(" ", ",")
    return f"https://image.pollinations.ai/prompt/{clean_prompt}?seed={seed}&width=1024&height=1024&nologo=true"

async def generate_post():
    try:
        search = tavily.search(query="latest electronics AI physics news 2025", search_depth="basic")
        news_content = search['results'][0]['content']
        post_text = await ask_ai(f"Напиши пост на русском для канала 'Нейро-Инженер' про это: {news_content}")
        img_prompt_raw = await ask_ai(f"Short English prompt for image about: {news_content}")
        img_prompt_en = img_prompt_raw.split('\n')[0].strip()
        photo_url = get_image_url(img_prompt_en)
        try:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_url, caption=post_text[:1024], parse_mode="Markdown")
        except:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_text[:4000])
    except Exception as e:
        print(f"ERROR: {e}")

@dp.message_handler(commands=['post'])
async def manual_post(message: types.Message):
    await message.reply("🚀 Начинаю генерацию...")
    await generate_post()
    await message.answer("✅ Готово!")

if __name__ == '__main__':
    # Запускаем веб-сервер в отдельном потоке
    threading.Thread(target=run_flask).start()
    # Запускаем бота
    print("--- БОТ ЗАПУЩЕН ---")
    executor.start_polling(dp, skip_updates=True)
