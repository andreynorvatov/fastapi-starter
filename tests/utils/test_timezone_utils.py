"""
Тесты для утилит работы с таймзонами.

Содержит тесты для:
- get_current_time: получение текущего времени в таймзоне проекта
- localize_datetime: локализация datetime объекта
- convert_to_utc: конвертация в UTC
- convert_from_utc: конвертация из UTC
- convert_to_datetime: парсинг строки в datetime
"""

from datetime import datetime

import pytest
import pytz

from src.utils.timezone_utils import (
    convert_to_datetime,
    convert_to_utc,
    convert_from_utc,
    get_current_time,
    localize_datetime,
    project_timezone,
)


# =============================================================================
# Тесты для get_current_time
# =============================================================================


class TestGetCurrentTime:
    """Тесты для функции get_current_time."""

    def test_get_current_time_returns_datetime(self) -> None:
        """Тест что функция возвращает объект datetime."""
        result = get_current_time()

        assert isinstance(result, datetime)

    def test_get_current_time_has_timezone(self) -> None:
        """Тест что возвращаемое время имеет таймзону."""
        result = get_current_time()

        assert result.tzinfo is not None

    def test_get_current_time_in_project_timezone(self) -> None:
        """Тест что возвращаемое время в таймзоне проекта (Europe/Moscow)."""
        result = get_current_time()

        assert result.tzinfo.zone == "Europe/Moscow"

    def test_get_current_time_is_recent(self) -> None:
        """Тест что возвращаемое время близко к текущему."""
        before = datetime.now(project_timezone)
        result = get_current_time()
        after = datetime.now(project_timezone)

        assert before <= result <= after


# =============================================================================
# Тесты для localize_datetime
# =============================================================================


class TestLocalizeDatetime:
    """Тесты для функции localize_datetime."""

    def test_localize_datetime_adds_timezone(self) -> None:
        """Тест что функция добавляет таймзону к naive datetime."""
        naive_dt = datetime(2025, 6, 15, 12, 30, 45)
        result = localize_datetime(naive_dt)

        assert result.tzinfo is not None
        assert result.tzinfo.zone == "Europe/Moscow"

    def test_localize_datetime_preserves_values(self) -> None:
        """Тест что функция сохраняет значения даты и времени."""
        naive_dt = datetime(2025, 6, 15, 12, 30, 45)
        result = localize_datetime(naive_dt)

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_localize_datetime_with_different_dates(self) -> None:
        """Тест локализации разных дат."""
        test_cases = [
            datetime(2025, 1, 1, 0, 0, 0),
            datetime(2025, 12, 31, 23, 59, 59),
            datetime(2024, 2, 29, 12, 0, 0),  # Високосный год
        ]

        for naive_dt in test_cases:
            result = localize_datetime(naive_dt)
            assert result.tzinfo.zone == "Europe/Moscow"
            assert result.year == naive_dt.year
            assert result.month == naive_dt.month
            assert result.day == naive_dt.day


# =============================================================================
# Тесты для convert_to_utc
# =============================================================================


class TestConvertToUtc:
    """Тесты для функции convert_to_utc."""

    def test_convert_to_utc_from_moscow(self) -> None:
        """Тест конвертации из Москвы в UTC."""
        # 15:00 в Москве = 12:00 UTC
        moscow_time = project_timezone.localize(datetime(2025, 6, 15, 15, 0, 0))
        result = convert_to_utc(moscow_time)

        assert result.tzinfo == pytz.UTC
        assert result.hour == 12
        assert result.minute == 0

    def test_convert_to_utc_preserves_date(self) -> None:
        """Тест что конвертация сохраняет дату (кроме времени)."""
        moscow_time = project_timezone.localize(datetime(2025, 6, 15, 15, 0, 0))
        result = convert_to_utc(moscow_time)

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15

    def test_convert_to_utc_already_utc(self) -> None:
        """Тест конвертации времени уже в UTC."""
        utc_time = pytz.utc.localize(datetime(2025, 6, 15, 12, 0, 0))
        result = convert_to_utc(utc_time)

        assert result.tzinfo == pytz.UTC
        assert result.hour == 12

    def test_convert_to_utc_midnight(self) -> None:
        """Тест конвертации полуночи по Москве."""
        # 00:00 в Москве = 21:00 предыдущего дня UTC
        moscow_time = project_timezone.localize(datetime(2025, 6, 15, 0, 0, 0))
        result = convert_to_utc(moscow_time)

        assert result.tzinfo == pytz.UTC
        assert result.hour == 21
        assert result.day == 14  # Предыдущий день


# =============================================================================
# Тесты для convert_from_utc
# =============================================================================


class TestConvertFromUtc:
    """Тесты для функции convert_from_utc."""

    def test_convert_from_utc_to_moscow(self) -> None:
        """Тест конвертации из UTC в Москву."""
        # 12:00 UTC = 15:00 в Москве
        utc_time = pytz.utc.localize(datetime(2025, 6, 15, 12, 0, 0))
        result = convert_from_utc(utc_time)

        assert result.tzinfo.zone == "Europe/Moscow"
        assert result.hour == 15
        assert result.minute == 0

    def test_convert_from_utc_preserves_date(self) -> None:
        """Тест что конвертация сохраняет дату."""
        utc_time = pytz.utc.localize(datetime(2025, 6, 15, 12, 0, 0))
        result = convert_from_utc(utc_time)

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15

    def test_convert_from_utc_late_evening(self) -> None:
        """Тест конвертации позднего вечера UTC."""
        # 21:00 UTC = 00:00 следующего дня в Москве
        utc_time = pytz.utc.localize(datetime(2025, 6, 15, 21, 0, 0))
        result = convert_from_utc(utc_time)

        assert result.tzinfo.zone == "Europe/Moscow"
        assert result.hour == 0
        assert result.day == 16  # Следующий день


# =============================================================================
# Тесты для convert_to_datetime
# =============================================================================


class TestConvertToDatetime:
    """Тесты для функции convert_to_datetime."""

    def test_convert_to_datetime_default_format(self) -> None:
        """Тест парсинга с форматом по умолчанию."""
        result = convert_to_datetime("2025-06-15 12:30:45")

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_convert_to_datetime_default_timezone(self) -> None:
        """Тест что по умолчанию используется Europe/Moscow."""
        result = convert_to_datetime("2025-06-15 12:30:45")

        assert result.tzinfo.zone == "Europe/Moscow"

    def test_convert_to_datetime_custom_format(self) -> None:
        """Тест парсинга с кастомным форматом."""
        result = convert_to_datetime("15/06/2025", format_string="%d/%m/%Y")

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15

    def test_convert_to_datetime_custom_timezone(self) -> None:
        """Тест парсинга с кастомной таймзоной."""
        result = convert_to_datetime(
            "2025-06-15 12:30:45",
            timezone="America/New_York"
        )

        assert result.tzinfo.zone == "America/New_York"

    def test_convert_to_datetime_iso_format(self) -> None:
        """Тест парсинга ISO формата."""
        result = convert_to_datetime("2025-06-15", format_string="%Y-%m-%d")

        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_convert_to_datetime_with_time_only(self) -> None:
        """Тест парсинга только времени."""
        result = convert_to_datetime("14:30:00", format_string="%H:%M:%S")

        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 0

    def test_convert_to_datetime_invalid_format_raises_error(self) -> None:
        """Тест что неверный формат вызывает ValueError."""
        with pytest.raises(ValueError):
            convert_to_datetime("15-06-2025")  # Формат по умолчанию ожидает YYYY-MM-DD

    def test_convert_to_datetime_invalid_timezone_raises_error(self) -> None:
        """Тест что неверная таймзона вызывает UnknownTimeZoneError."""
        with pytest.raises(pytz.exceptions.UnknownTimeZoneError):
            convert_to_datetime("2025-06-15 12:30:45", timezone="Invalid/Timezone")

    def test_convert_to_datetime_various_formats(self) -> None:
        """Тест парсинга различных форматов дат."""
        test_cases = [
            ("2025.06.15", "%Y.%m.%d", 2025, 6, 15),
            ("15-Jun-2025", "%d-%b-%Y", 2025, 6, 15),
            ("June 15, 2025", "%B %d, %Y", 2025, 6, 15),
        ]

        for date_string, format_string, expected_year, expected_month, expected_day in test_cases:
            result = convert_to_datetime(date_string, format_string=format_string)
            assert result.year == expected_year
            assert result.month == expected_month
            assert result.day == expected_day


# =============================================================================
# Интеграционные тесты
# =============================================================================


class TestTimezoneIntegration:
    """Интеграционные тесты для проверки связки функций."""

    def test_roundtrip_utc_conversion(self) -> None:
        """Тест кругового преобразования UTC -> Moscow -> UTC."""
        original_utc = pytz.utc.localize(datetime(2025, 6, 15, 12, 0, 0))
        
        moscow_time = convert_from_utc(original_utc)
        back_to_utc = convert_to_utc(moscow_time)

        assert back_to_utc.hour == original_utc.hour
        assert back_to_utc.minute == original_utc.minute
        assert back_to_utc.day == original_utc.day

    def test_convert_to_datetime_then_to_utc(self) -> None:
        """Тест парсинга строки и конвертации в UTC."""
        # 15:00 в Москве
        moscow_dt = convert_to_datetime("2025-06-15 15:00:00")
        utc_dt = convert_to_utc(moscow_dt)

        # 15:00 в Москве = 12:00 UTC
        assert utc_dt.hour == 12
        assert utc_dt.tzinfo == pytz.UTC

    def test_full_workflow(self) -> None:
        """Тест полного рабочего процесса с localize_datetime."""
        # 1. Создаем naive datetime и локализуем его
        naive_dt = datetime(2025, 6, 15, 10, 30, 0)
        dt = localize_datetime(naive_dt)
        assert dt.tzinfo.zone == "Europe/Moscow"

        # 2. Конвертируем в UTC
        utc_dt = convert_to_utc(dt)
        assert utc_dt.tzinfo == pytz.UTC
        # Москва UTC+3, поэтому 10:30 MSK = 07:30 UTC
        assert utc_dt.hour == 7
        assert utc_dt.minute == 30

        # 3. Конвертируем обратно - должно получиться исходное время
        back_dt = convert_from_utc(utc_dt)
        assert back_dt.tzinfo.zone == "Europe/Moscow"
        assert back_dt.hour == 10
        assert back_dt.minute == 30
