from __future__ import annotations  # Совместимость с будущей оценкой типов

from loguru import logger  # Удобная библиотека логирования
import sys  # Доступ к stdout

logger.remove()  # Удаляем дефолтные обработчики, чтобы настроить свои
logger.add(sys.stdout, level="INFO", backtrace=False, diagnose=False, enqueue=True)  # Пишем логи в stdout, уровень INFO

__all__ = ["logger"]  # Экспортируем логгер для использования по всему проекту 