from django.db import models


class BaseModel(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    class Meta:
        abstract = True


class TelegramGroup(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Название группы')
    chat_id = models.BigIntegerField(unique=True, verbose_name='Chat ID')

    def str(self):
        return self.name

    class Meta:
        verbose_name = 'Telegram-группа'
        verbose_name_plural = 'Telegram-группы'


class YouGileBoard(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Название доски')
    api_key = models.TextField(verbose_name='API Key')
    board_id = models.CharField(max_length=255, verbose_name='Board ID')
    column_id = models.CharField(max_length=255, verbose_name='Column ID')

    def str(self):
        return self.name

    class Meta:
        verbose_name = 'YouGile-доска'
        verbose_name_plural = 'YouGile-доски'


class AssistantKeywords(BaseModel):
    keywords = models.CharField(max_length=255, verbose_name='Ключевые слова')
    description = models.TextField(verbose_name='Описание')

    def str(self):
        return self.keywords

    class Meta:
        verbose_name = 'Ключевые слова'
        verbose_name_plural = 'Ключевые слова'


class AssistantPromt(BaseModel):
    prompt = models.TextField(verbose_name='Промт')

    def str(self):
        return self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt

    class Meta:
        verbose_name = 'Промт'
        verbose_name_plural = 'Промты'


class Secret(BaseModel):
    value_bot = models.TextField(verbose_name='Telegram bot')
    value_ai = models.TextField(verbose_name='AI key')
    value_group = models.TextField(verbose_name='Group')

    yougile_api_key = models.TextField(verbose_name='YouGile API Key')
    yougile_board_id = models.TextField(verbose_name='YouGile Board ID')
    yougile_column_id = models.TextField(verbose_name='YouGile Column ID')

    def str(self):
        return self.value_bot[:12] + "..."

    class Meta:
        verbose_name = 'Секрет'
        verbose_name_plural = 'Секреты'


class AssistantUser(BaseModel):
    tg_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    full_name = models.CharField(max_length=255, verbose_name='Имя')

    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name='Первое сообщение')
    last_message_at = models.DateTimeField(auto_now=True, verbose_name='Последнее сообщение')

    can_submit_tasks = models.BooleanField(default=False, verbose_name='Разрешено создавать задачи')

    telegram_groups = models.ManyToManyField(TelegramGroup, blank=True, verbose_name='Telegram-группы')
    yougile_boards = models.ManyToManyField(YouGileBoard, blank=True, verbose_name='YouGile-доски')

    def str(self):
        return f"{self.full_name} ({self.tg_id})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'