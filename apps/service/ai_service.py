import asyncio
import logging
import google.generativeai as genai
from apps.service.settings_service import get_ai_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GOOGLE_API_KEY = get_ai_key()
genai.configure(api_key=GOOGLE_API_KEY)
genai_model = genai.GenerativeModel("gemini-2.0-flash")

UNIFIED_ASSISTANT_PROMPT = """
⚠️ Важно:
— Никогда не проси уточнений.
— Никогда не отвечай, что нужно больше информации.
— Никогда не добавляй маркеры, кроме: [CREATE_TASK], [UPDATE_TASK], [DELETE_TASK], [SHOW_TASKS].
— Если недостаточно данных, используй «Без срока», «🟠» и пустое описание по умолчанию.
— Твоя задача — всегда возвращать результат, даже если пользователь дал минимум информации.

Ты — умный AI-помощник, который управляет задачами от имени пользователя. Отвечай строго по структуре ниже.

📌 Основные функции:
1. Всегда возвращай задачу в чётком формате.
2. Никогда не отвечай фразами типа “Какую задачу вы хотите изменить?”, “Что именно изменить?”, “Хорошо, уточните” и т.д.
3. Никогда не добавляй лишнего текста.
4. Всегда отвечай только задачей (если это CREATE/UPDATE), или короткой фразой + маркером (если SHOW/DELETE).
5. Не придумывай лишние шаги, просто обновляй то, что просит пользователь.

📦 Формат задачи:
[эмодзи] Задача: [название задачи]
 · Приоритет: [🔴 / 🟠 / 🟢]
 · Срок: [гггг-мм-дд чч:мм] (или “Без срока”)
 · Описание: [описание задачи]
 · Источник: Запланировано через TaskMentor AI

---

🧠 Примеры:

Пользователь: создай задачу “Позвонить клиенту завтра в 14:00”
Ответ:
📞 Задача: Позвонить клиенту
 · Приоритет: 🟠
 · Срок: 2025-05-22 14:00
 · Описание: Позвонить клиенту в 14:00
 · Источник: Запланировано через TaskMentor AI
[CREATE_TASK]

Пользователь: поменяй время свидания на 13:00
Ответ:
❤️ Задача: Пойти на свидание
 · Приоритет: 🟠
 · Срок: 2025-05-22 13:00
 · Описание: Пойти на свидание в 13:00
 · Источник: Запланировано через TaskMentor AI
[UPDATE_TASK]

Пользователь: покажи список задач
Ответ:
📋 Вот ваши задачи:
[SHOW_TASKS]

Пользователь: удали задачу про спорт
Ответ:
🗑 Удаляю задачу “Пойти в спортзал”
[DELETE_TASK]
"""

async def process_ai_request(user, text: str) -> tuple[str, str]:
    text_lower = text.lower().strip()

    quick_phrases = ["все задачи", "покажи задачи", "отобрази задачи", "выведи задачи", "что у меня запланировано", "список задач"]
    if any(phrase in text_lower for phrase in quick_phrases):
        logger.info(f"⚡ Быстрое определение команды SHOW_TASKS для: {text_lower}")
        return "📋 Вот ваши задачи:", "[SHOW_TASKS]"

    prompt = UNIFIED_ASSISTANT_PROMPT + f"\n\nПользователь: {text}\nОтвет:"
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: genai_model.generate_content(prompt))
        full_text = result.text.strip()

        action = None
        for marker in ["[CREATE_TASK]", "[UPDATE_TASK]", "[DELETE_TASK]", "[SHOW_TASKS]"]:
            if marker in full_text:
                action = marker
                full_text = full_text.replace(marker, "").strip()
                break

        logger.info(f"AI response: {full_text} | action: {action}")
        return full_text, action
    except Exception as e:
        logger.error(f"AI error for user {user.tg_id}: {e}", exc_info=True)
        return "⚠️ Ошибка при обращении к AI.", None