import os, asyncio, aiohttp, threading, numpy as np
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from tavily import TavilyClient

app = Flask(__name__)
@app.route('/')
def index(): return "Нейро-Лаборатория активна!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# База знаний
words_db = {
    "банк": np.array([1.0, 0.0]),
    "деньги": np.array([1.2, 0.1]),
    "река": np.array([0.1, 1.5]),
    "вода": np.array([0.0, 1.2])
}

async def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    data = {
        "model": "openchat/openchat-7b:free", # Вернулись к Мистралю
        "messages": [
            {"role": "system", "content": "Ты - ведущий инженер нейросетей. Пиши кратко, технично, с эмодзи на русском."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                res = await resp.json()
                return res['choices'][0]['message']['content']
    except:
        return None

@dp.message_handler(commands=['post'])
async def cmd_post(message: types.Message):
    status_msg = await message.answer("🚀 Начинаю поиск технологий для канала...")
    try:
        # Поиск новости
        search = tavily.search(query="latest AI LLM breakthrough 2025", search_depth="basic")
        news_content = search['results'][0]['content']
        
        # Генерация текста
        ai_text = await ask_ai(f"Сделай пост для Telegram канала про это: {news_content}")
        
        if ai_text:
            # ОТПРАВКА В КАНАЛ (замени на свой ID или юзернейм канала)
            CHANNEL_ID = "@neuro_engineer_lab" 
            await bot.send_message(chat_id=CHANNEL_ID, text=f"📢 **НОВОСТИ ЛАБОРАТОРИИ**\n\n{ai_text}\n\n#AI #Engineering", parse_mode="Markdown")
            await status_msg.edit_text("✅ Пост опубликован в @neuro_engineer_lab!")
        else:
            await status_msg.edit_text("🤖 Нейросеть не ответила, попробуй позже.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")

@dp.message_handler()
async def flexible_attention(message: types.Message):
    text = message.text.lower()
    if "банк" in text:
        # Улучшенный поиск: ищем корни слов
        found_context = None
        if any(x in text for x in ["деньг", "бабл", "купюр"]):
            found_context = "деньги"
        elif any(x in text for x in ["рек", "вод", "берег"]):
            found_context = "река"

        if found_context:
            q_vec = words_db["банк"]
            score = np.dot(q_vec, words_db[found_context])
            res = "ФИНАНСЫ 💰" if found_context == "деньги" else "ПРИРОДА 🌊"
            await message.answer(f"🧠 Внимание сфокусировано на корне '{found_context}'.\nСвязь (Dot Product): {score:.2f}\nКонтекст: {res}")
        else:
            await message.answer("🤖 Вижу 'банк', но не вижу ключевых слов контекста (деньги/река).")

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
