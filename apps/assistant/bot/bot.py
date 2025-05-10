from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apps.service.settings_service import get_bot_token
from asgiref.sync import sync_to_async
from apps.assistant.models import AssistantUser

BOT_TOKEN = get_bot_token()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

@sync_to_async
def get_or_create_user(tg_id: int, full_name: str) -> AssistantUser:
    """
    Создаёт или возвращает пользователя, обновляя его имя и дату последнего сообщения.
    """
    user, created = AssistantUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={"full_name": full_name}
    )
    user.full_name = full_name
    user.save(update_fields=["full_name", "last_message_at"])
    return user