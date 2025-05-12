import aiohttp
import logging
from apps.service.settings_service import get_default_yougile_data

logger = logging.getLogger(__name__)

async def create_task(title: str, description: str = "", priority: str = "task-green", deadline_ts: int = None) -> bool:
    """
    Создаёт задачу в YouGile через API. Использует ключи и доску из настроек.
    """
    data = await get_default_yougile_data() 
    api_key = data["api_key"]
    board_id = data["board_id"]
    column_id = data["column_id"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title[:100],
        "description": description,
        "columnId": column_id,
        "archived": False,
        "completed": False,
        "color": priority
    }

    if deadline_ts:
        payload["deadline"] = {
            "deadline": deadline_ts,
            "startDate": deadline_ts,
            "withTime": False,
            "history": [],
            "blockedPoints": [],
            "links": []
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.yougile.com/api-v2/tasks", json=payload, headers=headers) as response:
                response_json = await response.json()
                if response.status in (200, 201) and "id" in response_json:
                    logger.info(f"✅ Задача успешно создана в YouGile: {response_json['id']}")
                    return True
                else:
                    logger.error(f"❌ Ошибка при создании задачи в YouGile: {response.status} {response_json}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при создании задачи в YouGile: {e}", exc_info=True)
        return False
    

async def get_tasks(limit: int = 10, offset: int = 0) -> list[dict]:
    data = await get_default_yougile_data()
    api_key = data["api_key"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.yougile.com/api-v2/task-list?limit={limit}&offset={offset}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response_json = await response.json()
                if response.status == 200 and isinstance(response_json, dict):
                    return response_json.get("content", [])
                else:
                    logger.error(f"Ошибка получения задач: {response.status} — {response_json}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка при получении задач из YouGile: {e}", exc_info=True)
        return []