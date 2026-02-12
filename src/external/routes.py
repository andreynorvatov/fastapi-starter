"""Внешние API интеграции."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from src.http_client import AsyncHTTPClient, ClientConfig

external_router = APIRouter()


class Post(BaseModel):
    """Модель поста из JSONPlaceholder."""
    userId: int
    id: Optional[int] = None
    title: str
    body: str


class PostCreate(BaseModel):
    """Модель для создания поста."""
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    userId: int = Field(..., ge=1)


class PostResponse(BaseModel):
    """Ответ с данными поста."""
    success: bool
    data: Optional[Post] = None
    message: Optional[str] = None


class PostsResponse(BaseModel):
    """Ответ со списком постов."""
    success: bool
    data: List[Post] = []
    total: int = 0
    message: Optional[str] = None


def get_http_client() -> AsyncHTTPClient:
    """
    Зависимость для получения настроенного HTTP клиента.
    
    Returns:
        AsyncHTTPClient: Настроенный клиент для внешних API
    """
    config = ClientConfig(
        timeout=30.0,
        max_connections=100,
        retry_attempts=3,
        retry_backoff_factor=1.0,
        verify_ssl=True,
    )
    
    return AsyncHTTPClient(
        base_url="https://jsonplaceholder.typicode.com",
        config=config,
    )


@external_router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post_from_external_api(
    post_id: int,
    client: AsyncHTTPClient = Depends(get_http_client),
) -> PostResponse:
    """
    Получить пост из внешнего API (JSONPlaceholder).
    
    Args:
        post_id: ID поста для получения
        
    Returns:
        PostResponse: Ответ с данными поста
        
    Raises:
        HTTPException: При ошибке запроса к внешнему API
    """
    try:
        response = await client.get(f"/posts/{post_id}")
        post_data = response.json_data
        
        return PostResponse(
            success=True,
            data=Post(**post_data),
            message="Пост успешно получен"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении поста из внешнего API: {str(e)}"
        )


@external_router.get("/posts", response_model=PostsResponse)
async def get_posts_from_external_api(
    user_id: Optional[int] = None,
    limit: int = 10,
    client: AsyncHTTPClient = Depends(get_http_client),
) -> PostsResponse:
    """
    Получить список постов из внешнего API.
    
    Args:
        user_id: Фильтр по ID пользователя (опционально)
        limit: Количество постов для возврата (по умолчанию 10)
        
    Returns:
        PostsResponse: Ответ со списком постов
    """
    try:
        params = {"_limit": limit}
        if user_id:
            params["userId"] = user_id
            
        response = await client.get("/posts", params=params)
        posts_data = response.json_data
        
        posts = [Post(**post) for post in posts_data]
        
        return PostsResponse(
            success=True,
            data=posts,
            total=len(posts),
            message="Посты успешно получены"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении постов из внешнего API: {str(e)}"
        )


@external_router.post("/posts", response_model=PostResponse)
async def create_post_in_external_api(
    post: PostCreate,
    client: AsyncHTTPClient = Depends(get_http_client),
) -> PostResponse:
    """
    Создать пост во внешнем API.
    
    Args:
        post: Данные для создания поста
        
    Returns:
        PostResponse: Ответ с созданным постом
    """
    try:
        response = await client.post("/posts", json=post.dict())
        post_data = response.json_data
        
        return PostResponse(
            success=True,
            data=Post(**post_data),
            message="Пост успешно создан"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании поста во внешнем API: {str(e)}"
        )


@external_router.delete("/posts/{post_id}", response_model=PostResponse)
async def delete_post_in_external_api(
    post_id: int,
    client: AsyncHTTPClient = Depends(get_http_client),
) -> PostResponse:
    """
    Удалить пост из внешнего API.
    
    Args:
        post_id: ID поста для удаления
        
    Returns:
        PostResponse: Результат удаления
    """
    try:
        response = await client.delete(f"/posts/{post_id}")
        
        # JSONPlaceholder возвращает пустой ответ для DELETE
        # Создаем фиктивные данные для ответа
        deleted_post = Post(
            userId=0,
            id=post_id,
            title="Удален",
            body="Пост был удален"
        )
        
        return PostResponse(
            success=response.status_code == 200,
            data=deleted_post,
            message="Пост успешно удален" if response.status_code == 200 else "Пост не найден"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении поста из внешнего API: {str(e)}"
        )
