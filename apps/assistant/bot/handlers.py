from aiogram import Router, F
from aiogram.types import Message
from apps.assistant.bot.bot import bot
from apps.service.ai_service import process_ai_request
from apps.assistant.bot.bot import get_or_create_user
from aiogram.enums import ChatAction

router = Router()

@router.message(F.text)
async def handle_text(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на создание задач. Обратитесь к администратору.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    response = await process_ai_request(user, message.text)
    await message.answer(response)