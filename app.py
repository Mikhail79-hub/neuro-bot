import os, asyncio, random, aiohttp, threading, time
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from tavily import TavilyClient

# --- ВЕБ-ЗАГЛУШКА ДЛЯ RENDER ---
app = Flask(__name__)
@app.route('/')
def index(): return "I am alive!"

def run_web():
    # Render дает порт в переменной PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БОТ ---
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

async def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "system", "content": "Ты - Нейро-Инженер. Пиши захватывающие посты для инженеров на русском языке с эмодзи."},
            {"role": "user", "content": prompt}
        ]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            res = await resp.json()
            if 'choices' in res and len(res['choices']) > 0:
                return res['choices'][0]['message']['content']
            else:
                print(f"Ошибка API: {res}")
                return "Извините, нейросеть сейчас занята, попробуйте через минуту."

async def generate_post():
    try:
        search = tavily.search(query="latest technology AI news 2025", search_depth="basic")
        news = search['results'][0]['content']
        text = await ask_ai(f"Напиши пост для инженеров на русском про это: {news}")
        await bot.send_message(chat_id="@neuro_engineer_lab", text=text[:4000])
        print("Пост улетел!")
    except Exception as e:
        print(f"Ошибка: {e}")

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    await message.reply("🚀 Генерирую...")
    await generate_post()

if __name__ == '__main__':
    # 1. Запускаем веб-сервер в фоне
    threading.Thread(target=run_web, daemon=True).start()
    # 2. Запускаем бота
    print("Бот погнал!")
    executor.start_polling(dp, skip_updates=True)
