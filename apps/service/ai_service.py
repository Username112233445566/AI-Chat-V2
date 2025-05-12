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
Ты — умный AI-помощник, который ведёт диалог и управляет задачами от имени пользователя.

Основные функции:
1. Общайся, как обычный чат-бот.
2. Если пользователь явно даёт команду, распознавай намерение и добавляй маркер в ответ.

⚠️ Никогда не показывай маркеры пользователю. Просто добавляй их в самый конец ответа на новой строке.

Командные маркеры:
- Если пользователь явно просит создать задачу (создай, запиши, добавь) → добавь [CREATE_TASK]
- Если изменить задачу → [UPDATE_TASK]
- Если удалить задачу → [DELETE_TASK]
- Если показать задачи (покажи задачи, отобрази список, что у меня запланировано, выведи задачи, все задачи и т.д.) → [SHOW_TASKS]
- Иначе — не добавляй никаких маркеров.

Примеры:
- "Создай задачу: позвонить клиенту" → нормальный ответ + [CREATE_TASK]
- "Удалить задачу с названием Х" → нормальный ответ + [DELETE_TASK]
- "Покажи мне мои задачи" → нормальный ответ + [SHOW_TASKS]
- "Что у меня запланировано?" → нормальный ответ + [SHOW_TASKS]
- "Как дела?" → обычный ответ без маркера
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