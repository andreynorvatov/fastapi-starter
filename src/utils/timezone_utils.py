"""Утилиты для работы с часовыми поясами."""

from datetime import datetime
from zoneinfo import ZoneInfo

# Часовой пояс проекта по умолчанию
PROJECT_TIMEZONE = ZoneInfo("Europe/Moscow")


def get_current_time() -> datetime:
    """Возвращает текущее время в часовом поясе проекта."""
    return datetime.now(PROJECT_TIMEZONE)


def localize_datetime(dt: datetime, timezone: str = "Europe/Moscow") -> datetime:
    """
    Добавляет информацию о часовом поясе к naive datetime.
    
    Args:
        dt: datetime без информации о часовом поясе
        timezone: Название часового пояса
        
    Returns:
        datetime с информацией о часовом поясе
    """
    return dt.replace(tzinfo=ZoneInfo(timezone))


def convert_to_utc(dt: datetime) -> datetime:
    """
    Конвертирует datetime в UTC.
    
    Args:
        dt: datetime с информацией о часовом поясе
        
    Returns:
        datetime в UTC
    """
    return dt.astimezone(ZoneInfo("UTC"))


def convert_from_utc(dt: datetime, target_timezone: str = "Europe/Moscow") -> datetime:
    """
    Конвертирует datetime из UTC в целевой часовой пояс.
    
    Args:
        dt: datetime в UTC
        target_timezone: Целевой часовой пояс
        
    Returns:
        datetime в целевом часовом поясе
    """
    return dt.astimezone(ZoneInfo(target_timezone))


def convert_to_datetime(
    date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S", timezone: str = "Europe/Moscow"
) -> datetime:
    """
    Конвертирует строку в объект datetime с указанным форматом и таймзоной.

    Args:
        date_string: Строка с датой и временем
        format_string: Формат строки (например, '%Y-%m-%d %H:%M:%S')
        timezone: Название таймзоны (например, 'Europe/Moscow')
        
    Returns:
        Объект datetime с указанной таймзоной

    Примеры форматов:
        %Y - год в формате YYYY
        %m - месяц в формате MM
        %d - день в формате DD
        %H - часы в формате HH
        %M - минуты в формате MM
        %S - секунды в формате SS
    """
    dt_object = datetime.strptime(date_string, format_string)
    return dt_object.replace(tzinfo=ZoneInfo(timezone))
