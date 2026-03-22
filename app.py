import os
import asyncio
import random
import aiohttp
import socket
import time
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from tavily import TavilyClient

# --- НАСТРОЙКИ (Берутся из Environment Variables на Render) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
CHANNEL_ID = "@neuro_engineer_lab" # Твой канал

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# 1. Функция "Разум" (OpenRouter - Gemma 2)
async def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [
            {"role": "system", "content": "Ты - инженер-радиофизик, автор канала 'Нейро-Инженер'. Пиши посты в научно-популярном стиле, глубоко, но понятно. Используй эмодзи."},
            {"role": "user", "content": prompt}
        ]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            res = await resp.json()
            if 'choices' in res:
                return res['choices'][0]['message']['content']
            else:
                return f"Ошибка AI: {res}"

# 2. Функция "Зрение" (Бесплатная генерация картинок)
def get_image_url(prompt_en):
    seed = random.randint(1, 999999)
    clean_prompt = prompt_en.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{clean_prompt}?seed={seed}&width=1024&height=1024&nologo=true"

# 3. Главная магия: Генерация и публикация поста
async def generate_post():
    print("Ищу новости...")
    search = tavily.search(query="инновации в электронике ИИ физика новости 2025", search_depth="basic")
    news_content = search['results'][0]['content']
    
    print("Пишу текст поста...")
    post_text = await ask_ai(f"Напиши захватывающий пост на основе этой новости: {news_content}. В конце добавь вопрос к аудитории.")
    
    print("Создаю промпт для картинки...")
    img_prompt_raw = await ask_ai(f"Напиши короткий промпт для нейросети на английском языке (ТОЛЬКО промпт!), чтобы нарисовать футуристическую иллюстрацию к этой теме: {news_content}")
    img_prompt_en = img_prompt_raw.split('\n')[0].strip()
    
    photo_url = get_image_url(img_prompt_en)
    
    print("Публикую в канал...")
    await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_url, caption=post_text[:1024], parse_mode="Markdown")

# Команда /post для ручного запуска
@dp.message_handler(commands=['post'])
async def manual_post(message: types.Message):
    await message.reply("🚀 Начинаю генерацию контента для канала...")
    try:
        await generate_post()
        await message.answer("✅ Пост успешно опубликован!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")

# --- ФИНАЛЬНЫЙ БЛОК ЗАПУСКА ---
if __name__ == '__main__':
    print("--- БОТ-АДМИН ЗАПУЩЕН И ГОТОВ К РАБОТЕ ---")
    
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print(f"Сетевая ошибка: {e}. Рестарт через 10 секунд...")
            time.sleep(10)
