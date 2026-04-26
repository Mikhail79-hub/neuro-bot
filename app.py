import os, asyncio, random, aiohttp, threading, numpy as np
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from tavily import TavilyClient

# --- ВЕБ-ЗАГЛУШКА ДЛЯ RENDER ---
app = Flask(__name__)
@app.route('/')
def index(): return "Нейро-Инженер Жив и на связи!"

def run_web():
    # Render сам подставит нужный порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Локальная база векторов для урока (работает БЕЗ интернета и API)
words_db = {
    "банк": np.array([1.0, 0.0]),
    "деньги": np.array([1.2, 0.1]),
    "река": np.array([0.1, 1.5]),
    "вода": np.array([0.0, 1.2])
}

# --- ЛОГИКА НЕЙРОСЕТИ ---
async def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "HTTP-Referer": "https://render.com",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemma-7b-it:free", # Поменял на более стабильную модель
        "messages": [
            {"role": "system", "content": "Ты - Нейро-Инженер. Пиши на русском с эмодзи."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=25) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    return res['choices'][0]['message']['content']
                else:
                    return f"🤖 Нейросеть занята (код {resp.status}). Попробуй через минуту!"
    except Exception as e:
        return "🤖 Ошибка связи. Но я (код бота) всё еще жив!"

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    text = (
        "🚀 **Привет, Инженер!**\n\n"
        "Я работаю в облаке 24/7. Вот что я могу:\n"
        "1️⃣ /post — Найти новости и сделать AI-пост.\n"
        "2️⃣ /attention — Запустить урок про 'Внимание' нейросетей.\n"
        "3️⃣ Напиши мне про 'банк', и я угадаю контекст сам!"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(commands=['attention'])
async def cmd_attn(message: types.Message):
    await message.answer("🧠 **Урок про Attention:**\nНапиши фразу, где есть слово 'банк' и что-то еще (например, 'деньги' или 'вода'). Я покажу, как работает фокус внимания!")

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    await message.reply("🛰 Ищу новости и генерирую пост...")
    try:
        search = tavily.search(query="latest AI technology news 2025", search_depth="basic")
        news = search['results'][0]['content']
        text = await ask_ai(f"Сделай краткий инженерный разбор новости: {news}")
        await message.answer(text)
    except:
        await message.answer("❌ Не удалось получить новости.")

# Глобальный обработчик для урока
@dp.message_handler()
async def logic_handler(message: types.Message):
    text = message.text.lower()
    if "банк" in text:
        words = [w for w in text.split() if w in words_db and w != "банк"]
        if words:
            # Считаем скалярное произведение (наше 'внимание')
            q_vec = words_db["банк"]
            best_word = max(words, key=lambda w: np.dot(q_vec, words_db[w]))
            
            if best_word == "деньги":
                await message.answer("🤖 Моё внимание: **ДЕНЬГИ**. Контекст: Финансы! 💰")
            else:
                await message.answer("🤖 Моё внимание: **РЕКА/ВОДА**. Контекст: Природа! 🌊")
        else:
            await message.answer("🤖 Слово 'банк' вижу, а контекст (деньги или река) — нет.")

# --- ЗАПУСК ---
if __name__ == '__main__':
    # 1. Поток для веб-сервера (чтобы Render не убил бота)
    threading.Thread(target=run_web, daemon=True).start()
    # 2. Основной цикл бота
    print("Бот погнал!")
    executor.start_polling(dp, skip_updates=True)
