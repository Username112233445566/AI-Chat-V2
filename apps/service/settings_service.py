from apps.assistant.models import Secret
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import sync_to_async

def get_secret():
    try:
        return Secret.objects.filter(is_active=True).latest("updated_at")
    except ObjectDoesNotExist:
        raise Exception("❌ Нет активной записи в Secret. Задай её через админку.")

def get_bot_token():
    return get_secret().value_bot.strip()

def get_ai_key():
    return get_secret().value_ai.strip()

def get_default_group_id():
    return get_secret().value_group.strip()

@sync_to_async
def get_default_yougile_data():
    secret = get_secret()
    return {
        "api_key": secret.yougile_api_key.strip(),
        "board_id": secret.yougile_board_id.strip(),
        "column_id": secret.yougile_column_id.strip(),
    }