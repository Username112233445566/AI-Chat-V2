# .
# ├── apps
# │   ├── assistant
# │   │   ├── admin.py
# │   │   ├── apps.py
# │   │   ├── bot
# │   │   │   ├── bot.py
# from aiogram import Bot
# from aiogram.enums import ParseMode
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from apps.service.settings_service import get_bot_token
# from asgiref.sync import sync_to_async
# from apps.assistant.models import AssistantUser

# BOT_TOKEN = get_bot_token()

# bot = Bot(
#     token=BOT_TOKEN,
#     default=DefaultBotProperties(parse_mode=ParseMode.HTML)
# )

# dp = Dispatcher()

# @sync_to_async
# def get_or_create_user(tg_id: int, full_name: str) -> AssistantUser:
#     """
#     Создаёт или возвращает пользователя, обновляя его имя и дату последнего сообщения.
#     """
#     user, created = AssistantUser.objects.get_or_create(
#         tg_id=tg_id,
#         defaults={"full_name": full_name}
#     )
#     user.full_name = full_name
#     user.save(update_fields=["full_name", "last_message_at"])
#     return user
# │   │   │   ├── handlers.py
# from aiogram import Router, F
# from aiogram.types import Message
# from apps.assistant.bot.bot import bot
# from apps.service.ai_service import process_ai_request
# from apps.assistant.bot.bot import get_or_create_user
# from aiogram.enums import ChatAction

# router = Router()

# @router.message(F.text)
# async def handle_text(message: Message):
#     user = await get_or_create_user(
#         tg_id=message.from_user.id,
#         full_name=message.from_user.full_name or message.from_user.username or "Unknown"
#     )

#     if not user.can_submit_tasks:
#         await message.answer("⛔️ У вас нет прав на создание задач. Обратитесь к администратору.")
#         return

#     await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
#     response = await process_ai_request(user, message.text)
#     await message.answer(response)
# │   │   │   └── start_bot.py
# import asyncio
# from apps.assistant.bot.bot import bot, dp
# from apps.assistant.bot.handlers import router

# async def start_bot():
#     dp.include_router(router)
#     await dp.start_polling(bot)
# │   │   ├── __init__.py
# │   │   ├── management
# │   │   │   └── commands
# │   │   │       └── runbot.py
# from django.core.management.base import BaseCommand
# import asyncio
# from apps.assistant.bot.start_bot import start_bot

# class Command(BaseCommand):
#     help = 'Запуск Telegram-бота'

#     def handle(self, *args, **options):
#         asyncio.run(start_bot())
# │   │   ├── migrations
# │   │   │   ├── 0001_initial.py
# │   │   │   └── __init__.py
# │   │   └── models.py
# from django.db import models


# class BaseModel(models.Model):
#     is_active = models.BooleanField(default=True, verbose_name='Активен')
#     updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

#     class Meta:
#         abstract = True


# class TelegramGroup(BaseModel):
#     name = models.CharField(max_length=255, verbose_name='Название группы')
#     chat_id = models.BigIntegerField(unique=True, verbose_name='Chat ID')

#     def str(self):
#         return self.name

#     class Meta:
#         verbose_name = 'Telegram-группа'
#         verbose_name_plural = 'Telegram-группы'


# class YouGileBoard(BaseModel):
#     name = models.CharField(max_length=255, verbose_name='Название доски')
#     api_key = models.TextField(verbose_name='API Key')
#     board_id = models.CharField(max_length=255, verbose_name='Board ID')
#     column_id = models.CharField(max_length=255, verbose_name='Column ID')

#     def str(self):
#         return self.name

#     class Meta:
#         verbose_name = 'YouGile-доска'
#         verbose_name_plural = 'YouGile-доски'


# class AssistantKeywords(BaseModel):
#     keywords = models.CharField(max_length=255, verbose_name='Ключевые слова')
#     description = models.TextField(verbose_name='Описание')

#     def str(self):
#         return self.keywords

#     class Meta:
#         verbose_name = 'Ключевые слова'
#         verbose_name_plural = 'Ключевые слова'


# class AssistantPromt(BaseModel):
#     prompt = models.TextField(verbose_name='Промт')

#     def str(self):
#         return self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt

#     class Meta:
#         verbose_name = 'Промт'
#         verbose_name_plural = 'Промты'


# class Secret(BaseModel):
#     value_bot = models.TextField(verbose_name='Telegram bot')
#     value_ai = models.TextField(verbose_name='AI key')
#     value_group = models.TextField(verbose_name='Group')

#     yougile_api_key = models.TextField(verbose_name='YouGile API Key')
#     yougile_board_id = models.TextField(verbose_name='YouGile Board ID')
#     yougile_column_id = models.TextField(verbose_name='YouGile Column ID')

#     def str(self):
#         return self.value_bot[:12] + "..."

#     class Meta:
#         verbose_name = 'Секрет'
#         verbose_name_plural = 'Секреты'


# class AssistantUser(BaseModel):
#     tg_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
#     full_name = models.CharField(max_length=255, verbose_name='Имя')

#     first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name='Первое сообщение')
#     last_message_at = models.DateTimeField(auto_now=True, verbose_name='Последнее сообщение')

#     can_submit_tasks = models.BooleanField(default=False, verbose_name='Разрешено создавать задачи')

#     telegram_groups = models.ManyToManyField(TelegramGroup, blank=True, verbose_name='Telegram-группы')
#     yougile_boards = models.ManyToManyField(YouGileBoard, blank=True, verbose_name='YouGile-доски')

#     def str(self):
#         return f"{self.full_name} ({self.tg_id})"

#     class Meta:
#         verbose_name = 'Пользователь'
#         verbose_name_plural = 'Пользователи'
# │   └── service
# │       ├── ai_service.py
# import asyncio
# import logging
# import google.generativeai as genai
# from apps.service.settings_service import get_ai_key

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# GOOGLE_API_KEY = get_ai_key()
# genai.configure(api_key=GOOGLE_API_KEY)

# genai_model = genai.GenerativeModel("gemini-2.0-flash")

# async def process_ai_request(user, text: str) -> str:
#     prompt = f"Пользователь: {text}\nОтвет:"
#     try:
#         loop = asyncio.get_running_loop()
#         result = await loop.run_in_executor(None, lambda: genai_model.generate_content(prompt))
#         return result.text.strip()
#     except Exception as e:
#         logger.error(f"AI error for user {user.tg_id}: {e}", exc_info=True)
#         return "⚠️ Ошибка при обращении к AI."
# │       ├── settings_service.py
# from apps.assistant.models import Secret
# from django.core.exceptions import ObjectDoesNotExist


# def get_secret():
#     try:
#         return Secret.objects.filter(is_active=True).latest("updated_at")
#     except ObjectDoesNotExist:
#         raise Exception("❌ Нет активной записи в Secret. Задай её через админку.")


# def get_bot_token():
#     return get_secret().value_bot.strip()


# def get_ai_key():
#     return get_secret().value_ai.strip()


# def get_default_group_id():
#     return get_secret().value_group.strip()


# def get_default_yougile_data():
#     secret = get_secret()
#     return {
#         "api_key": secret.yougile_api_key.strip(),
#         "board_id": secret.yougile_board_id.strip(),
#         "column_id": secret.yougile_column_id.strip(),
#     }
# │       ├── telegram_service.py
# │       ├── whisper_service.py
# │       └── yougile_service.py
# ├── core
# │   ├── asgi.py
# │   ├── config
# │   │   ├── __init__.py
# │   │   └── settings.py
# │   ├── urls.py
# │   └── wsgi.py
# ├── db.sqlite3
# ├── manage.py