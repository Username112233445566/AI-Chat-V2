from pathlib import Path
import whisper
import torch
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    logger.info(f"Whisper будет использовать устройство: {device}")
    model = whisper.load_model("base", device=device)
except Exception as e:
    logger.error(f"Ошибка при инициализации Whisper: {e}", exc_info=True)
    model = whisper.load_model("base", device="cpu")

async def transcribe_voice(file_path: str, language: str = None) -> str:
    """
    Асинхронная транскрибация аудиофайла через Whisper (через executor).
    """
    loop = asyncio.get_running_loop()

    try:
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(file_path, language=language)
        )
        return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"Ошибка при транскрибации файла {file_path}: {e}", exc_info=True)
        return ""