from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

import os
import tempfile

from apps.assistant.bot.bot import bot, get_or_create_user
from apps.service.ai_service import process_ai_request
from apps.service.whisper_service import transcribe_voice

router = Router()

def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать задачу", callback_data="confirm_create")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

@router.message(F.text)
async def handle_text(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на использование бота. Обратитесь к администратору.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    response_text, action = await process_ai_request(user, message.text)

    if action == "[CREATE_TASK]":
        await message.answer(response_text, reply_markup=confirm_keyboard())
    elif action == "[UPDATE_TASK]":
        await message.answer("🔧 Запрос на изменение задачи — функция в разработке.")
    elif action == "[DELETE_TASK]":
        await message.answer("🗑 Запрос на удаление задачи — функция в разработке.")
    elif action == "[SHOW_TASKS]":
        await message.answer("📋 Список задач — функция в разработке.")
    else:
        await message.answer(response_text)

@router.message(F.voice)
async def handle_voice(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на использование бота. Обратитесь к администратору.")
        return

    voice = message.voice
    file = await bot.download(voice.file_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
        temp_audio.write(file.getvalue())
        temp_audio_path = temp_audio.name

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    transcribed_text = await transcribe_voice(temp_audio_path)

    os.remove(temp_audio_path)

    if not transcribed_text.strip():
        await message.answer("🛑 Не удалось распознать голосовое сообщение.")
        return

    response_text, action = await process_ai_request(user, transcribed_text)

    if action == "[CREATE_TASK]":
        await message.answer(response_text, reply_markup=confirm_keyboard())
    elif action == "[UPDATE_TASK]":
        await message.answer("🔧 Запрос на изменение задачи — функция в разработке.")
    elif action == "[DELETE_TASK]":
        await message.answer("🗑 Запрос на удаление задачи — функция в разработке.")
    elif action == "[SHOW_TASKS]":
        await message.answer("📋 Список задач — функция в разработке.")
    else:
        await message.answer(response_text)