import asyncio
import logging
import google.generativeai as genai
from apps.service.settings_service import get_ai_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GOOGLE_API_KEY = get_ai_key()
genai.configure(api_key=GOOGLE_API_KEY)

genai_model = genai.GenerativeModel("gemini-2.0-flash")

async def process_ai_request(user, text: str) -> str:
    prompt = f"Пользователь: {text}\nОтвет:"
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: genai_model.generate_content(prompt))
        return result.text.strip()
    except Exception as e:
        logger.error(f"AI error for user {user.tg_id}: {e}", exc_info=True)
        return "⚠️ Ошибка при обращении к AI."
