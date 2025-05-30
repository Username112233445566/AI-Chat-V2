from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

import os
import tempfile
import re
import time
from datetime import datetime

from apps.assistant.bot.bot import bot, get_or_create_user
from apps.service.ai_service import process_ai_request
from apps.service.whisper_service import transcribe_voice
from apps.service.yougile_service import create_task, get_tasks, delete_task, update_task

router = Router()
pending_tasks = {}
task_lookup_by_user = {}

def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать задачу", callback_data="confirm_create")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def delete_keyboard(user_id: int):
    tasks = task_lookup_by_user.get(user_id, [])
    buttons = [
        [InlineKeyboardButton(text=t["title"], callback_data=f"delete:{t['id']}")]
        for t in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

def update_keyboard(user_id: int):
    tasks = task_lookup_by_user.get(user_id, [])
    buttons = [
        [InlineKeyboardButton(text=t["title"], callback_data=f"update:{t['id']}")]
        for t in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

def parse_task_block(text: str) -> dict:
    title = ""
    description = ""
    priority = "task-yellow"
    deadline_ts = None

    title_match = re.search(r"Задача:\s*(.+)", text)
    if title_match:
        title = title_match.group(1).strip()

    description_match = re.search(r"Описание:\s*(.+)", text)
    if description_match:
        description = description_match.group(1).strip()

    priority_match = re.search(r"Приоритет:\s*(🔴|🟠|🟢)", text)
    if priority_match:
        color = priority_match.group(1)
        priority = {
            "🔴": "task-red",
            "🟠": "task-yellow",
            "🟢": "task-green"
        }.get(color, "task-yellow")

    deadline_match = re.search(r"Срок:\s*([\d\-:\s]+)", text)
    if deadline_match:
        try:
            dt = datetime.strptime(deadline_match.group(1).strip(), "%Y-%m-%d %H:%M")
            deadline_ts = int(dt.timestamp() * 1000)
        except:
            pass

    return {
        "title": title,
        "description": description,
        "priority": priority,
        "deadline_ts": deadline_ts
    }

def format_task_block(task: dict) -> str:
    emoji = "📌"
    title = task.get("title", "").lower()

    if "спорт" in title or "зал" in title:
        emoji = "🏃"
    elif "свидан" in title:
        emoji = "❤️"
    elif "работ" in title:
        emoji = "💼"

    pri = {
        "task-red": "🔴",
        "task-yellow": "🟠",
        "task-green": "🟢"
    }.get(task.get("priority") or task.get("color", ""), "⚪")

    deadline_ts = task.get("deadline_ts")
    if not deadline_ts and isinstance(task.get("deadline"), dict):
        deadline_ts = task["deadline"].get("deadline")

    deadline = "Без срока"
    if deadline_ts:
        try:
            deadline = datetime.fromtimestamp(deadline_ts / 1000).strftime("%Y-%m-%d %H:%M")
        except:
            pass

    return (
        f"{emoji} Задача: {task.get('title', 'Без названия')}\n"
        f" · Приоритет: {pri}\n"
        f" · Срок: {deadline}\n"
        f" · Описание: {task.get('description', '')}\n"
        f" · Источник: Запланировано через TaskMentor AI"
    )

@router.message(F.text)
async def handle_text(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name or message.from_user.username or "Unknown"
    )

    if not user.can_submit_tasks:
        await message.answer("⛔️ У вас нет прав на использование бота.")
        return

    # Обработка обновления задачи
    if user.tg_id in pending_tasks and isinstance(pending_tasks[user.tg_id], dict) and "update_task_id" in pending_tasks[user.tg_id]:
        update_info = pending_tasks.pop(user.tg_id)
        task_id = update_info["update_task_id"]
        original = update_info["original_task"]

        context = (
            f"Вот текущая задача:\n"
            f"- Название: {original.get('title', '')}\n"
            f"- Описание: {original.get('description', '')}\n"
            f"- Приоритет: {original.get('color', '')}\n"
            f"- Срок: {original.get('deadline', {}).get('deadline', '')}\n\n"
            f"Пользователь хочет внести следующие изменения:\n{message.text.strip()}"
        )

        ai_response, _ = await process_ai_request(user, context)
        parsed = parse_task_block(ai_response)

        success = await update_task(
            task_id=task_id,
            title=parsed["title"],
            description=parsed["description"],
            priority=parsed["priority"],
            deadline_ts=parsed["deadline_ts"]
        )

        if success:
            await message.answer(f"✅ Задача обновлена:\n\n{format_task_block(parsed)}")
        else:
            await message.answer("❌ Не удалось обновить задачу.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    response_text, action = await process_ai_request(user, message.text)

    if action == "[CREATE_TASK]":
        parsed = parse_task_block(response_text)
        pending_tasks[user.tg_id] = parsed
        await message.answer(format_task_block(parsed), reply_markup=confirm_keyboard())

    elif action == "[UPDATE_TASK]":
        tasks = await get_tasks()
        task_lookup_by_user[user.tg_id] = tasks
        if not tasks:
            await message.answer("Нет задач для обновления.")
        else:
            await message.answer("Выберите задачу для редактирования:", reply_markup=update_keyboard(user.tg_id))

    elif action == "[SHOW_TASKS]":
        tasks = await get_tasks()
        if tasks:
            formatted = "\n\n".join([format_task_block(t) for t in tasks])
            await message.answer(f"Конечно, вот ваш список задач:\n\n{formatted}")
        else:
            await message.answer("У вас пока нет задач.")

    elif action == "[DELETE_TASK]":
        tasks = await get_tasks()
        task_lookup_by_user[user.tg_id] = tasks
        if not tasks:
            await message.answer("📭 Нет задач для удаления.")
        else:
            await message.answer("Выберите задачу для удаления:", reply_markup=delete_keyboard(user.tg_id))

    else:
        await message.answer(response_text)

@router.callback_query(F.data == "confirm_create")
async def handle_confirm_create(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in pending_tasks:
        await callback.message.answer("⚠️ Нет сохранённой задачи.")
        await callback.answer()
        return

    parsed = pending_tasks.pop(user_id)
    success = await create_task(
        title=parsed["title"],
        description=parsed["description"],
        priority=parsed["priority"],
        deadline_ts=parsed["deadline_ts"]
    )

    if success:
        await callback.message.edit_text(f"✅ Задача создана:\n\n{format_task_block(parsed)}")
    else:
        await callback.message.answer("❌ Не удалось создать задачу.")

    await callback.answer("Готово.")

@router.callback_query(F.data.startswith("delete:"))
async def confirm_delete(callback: CallbackQuery):
    task_id = callback.data.split(":", 1)[1]
    success = await delete_task(task_id)
    if success:
        await callback.message.edit_text("🗑 Задача удалена.")
    else:
        await callback.message.answer("❌ Не удалось удалить задачу.")
    await callback.answer()

@router.callback_query(F.data.startswith("update:"))
async def start_update(callback: CallbackQuery):
    task_id = callback.data.split(":", 1)[1]
    task = next((t for t in task_lookup_by_user.get(callback.from_user.id, []) if t["id"] == task_id), None)
    if task:
        pending_tasks[callback.from_user.id] = {
            "update_task_id": task_id,
            "original_task": task
        }
        await callback.message.answer("✏️ Введите новый текст для задачи (заголовок, описание, срок, приоритет):")
    await callback.answer()
