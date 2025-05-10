import asyncio
from apps.assistant.bot.bot import bot, dp
from apps.assistant.bot.handlers import router

async def start_bot():
    dp.include_router(router)
    await dp.start_polling(bot)