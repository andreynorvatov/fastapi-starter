from datetime import datetime

import pytz

project_timezone = pytz.timezone("Europe/Moscow")


def get_current_time() -> datetime:
    return datetime.now(project_timezone)


def localize_datetime(dt: datetime) -> datetime:
    return project_timezone.localize(dt)  # type: ignore


def convert_to_utc(dt: datetime) -> datetime:
    return dt.astimezone(pytz.utc)


def convert_from_utc(dt: datetime) -> datetime:
    return dt.astimezone(project_timezone)


def convert_to_datetime(
    date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S", timezone: str = "Europe/Moscow"
) -> datetime:
    """
    Конвертирует строку в объект datetime с указанным форматом и таймзоной

    :param date_string: Строка с датой и временем
    :param format_string: Формат строки (например, '%Y-%m-%d %H:%M:%S')
    :param timezone: Название таймзоны (например, 'Europe/Moscow')
    :return: Объект datetime с указанной таймзоной

    Примеры форматов:
    %Y - год в формате YYYY
    %m - месяц в формате MM
    %d - день в формате DD
    %H - часы в формате HH
    %M - минуты в формате MM
    %S - секунды в формате SS
    """

    # Сначала конвертируем строку в datetime объект без таймзоны
    dt_object = datetime.strptime(date_string, format_string)

    return dt_object.replace(tzinfo=pytz.timezone(timezone))
