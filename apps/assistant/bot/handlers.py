from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

import os
import tempfile
import re
import time

from apps.assistant.bot.bot import bot, get_or_create_user
from apps.service.ai_service import process_ai_request
from apps.service.whisper_service import transcribe_voice
from apps.service.yougile_service import create_task

router = Router()
pending_tasks = {}

def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать задачу", callback_data="confirm_create")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def parse_task_block(text: str) -> dict:
    title = text.split("\\n")[0].strip()
    description = "\\n".join(text.split("\\n")[1:]).strip()

    deadline_ts = None
    priority = "task-green"

    if "приоритет высокий" in text.lower():
        priority = "task-red"
    elif "приоритет средний" in text.lower():
        priority = "task-yellow"

    match = re.search(r"(\\d{4}-\\d{2}-\\d{2})", text)
    if match:
        try:
            struct_time = time.strptime(match.group(1), "%Y-%m-%d")
            deadline_ts = int(time.mktime(struct_time) * 1000)
        except:
            pass

    return {
        "title": title,
        "description": description,
        "priority": priority,
        "deadline_ts": deadline_ts
    }

@router.message(F.text)
async def handle_text(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на использование бота.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    response_text, action = await process_ai_request(user, message.text)

    if action == "[CREATE_TASK]":
        pending_tasks[user.tg_id] = response_text
        await message.answer(response_text, reply_markup=confirm_keyboard())

    elif action == "[SHOW_TASKS]":
        from apps.service.yougile_service import get_tasks
        tasks = await get_tasks()
        if not tasks:
            await message.answer("📭 Задач не найдено.")
        else:
            text = "📋 <b>Актуальные задачи:</b>\n\n"
            for i, t in enumerate(tasks, 1):
                title = t.get("title", "Без названия")
                color = t.get("color", "")
                text += f"{i}. {title} ({color})\n"
            await message.answer(text)

    else:
        await message.answer(response_text)

@router.message(F.voice)
async def handle_voice(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на использование бота.")
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
        pending_tasks[user.tg_id] = response_text
        await message.answer(response_text, reply_markup=confirm_keyboard())
    else:
        await message.answer(response_text)

@router.callback_query(F.data == "confirm_create")
async def handle_confirm_create(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in pending_tasks:
        await callback.message.answer("⚠️ Нет сохранённой задачи.")
        await callback.answer()
        return

    task_text = pending_tasks.pop(user_id)
    parsed = parse_task_block(task_text)

    success = await create_task(
        title=parsed["title"],
        description=parsed["description"],
        priority=parsed["priority"],
        deadline_ts=parsed["deadline_ts"]
    )

    if success:
        await callback.message.edit_text(f"✅ Задача создана в YouGile:\n\n{parsed['title']}")
    else:
        await callback.message.answer("❌ Не удалось создать задачу в YouGile.")

    await callback.answer("Готово.")
    