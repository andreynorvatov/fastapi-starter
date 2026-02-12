from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR


class AppException(HTTPException):
    """Базовый класс пользовательских исключений приложения.

    Наследуется от FastAPI HTTPException, чтобы автоматически генерировать HTTP‑ответы.
    """
    def __init__(self, status_code: int, detail: str, **kwargs):
        super().__init__(status_code=status_code, detail=detail, **kwargs)


class NotFoundException(AppException):
    """Исключение, генерируемое, когда ресурс не найден (404)."""
    def __init__(self, detail: str = "Ресурс не найден"):
        super().__init__(status_code=HTTP_404_NOT_FOUND, detail=detail)


class ValidationException(AppException):
    """Исключение для ошибок валидации (422)."""
    def __init__(self, detail: str = "Ошибка валидации"):
        super().__init__(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class InternalServerException(AppException):
    """Исключение для внутренних ошибок сервера (500)."""
    def __init__(self, detail: str = "Внутренняя ошибка сервера"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
