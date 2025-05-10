from django.core.management.base import BaseCommand
import asyncio
from apps.assistant.bot.start_bot import start_bot

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        asyncio.run(start_bot())