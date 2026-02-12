"""Пример использования эндпоинтов внешних API."""

import asyncio
import json

import httpx


async def test_external_api_endpoints():
    """
    Тестовый скрипт для проверки эндпоинтов внешних API.
    
    Запуск: uv run python examples/external_api_example.py
    
    Примечание: Убедитесь, что сервер FastAPI запущен на http://localhost:8000
    """
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Тестирование эндпоинтов внешних API")
        print("=" * 60)
        
        # 1. GET /external/posts/{id} - получить пост по ID
        print("\n1. GET /external/posts/1 - Получить пост с ID=1")
        try:
            response = await client.get(f"{base_url}/external/posts/1")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 2. GET /external/posts - получить список постов
        print("\n2. GET /external/posts?limit=5 - Получить 5 постов")
        try:
            response = await client.get(f"{base_url}/external/posts", params={"limit": 5})
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Всего получено: {data.get('total')} постов")
                if data.get('data'):
                    first_post = data['data'][0]
                    print(f"Первый пост: {first_post.get('title')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 3. GET /external/posts?user_id=1 - фильтр по пользователю
        print("\n3. GET /external/posts?user_id=1 - Посты пользователя ID=1")
        try:
            response = await client.get(f"{base_url}/external/posts", params={"user_id": 1, "limit": 3})
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Всего получено: {data.get('total')} постов пользователя 1")
        except Exception as e:
            print(f"Error: {e}")
        
        # 4. POST /external/posts - создать новый пост
        print("\n4. POST /external/posts - Создать новый пост")
        try:
            new_post = {
                "title": "Мой тестовый пост",
                "body": "Это тело тестового поста, созданного через API",
                "userId": 1
            }
            response = await client.post(
                f"{base_url}/external/posts",
                json=new_post,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Создан пост с ID: {data.get('data', {}).get('id')}")
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 5. DELETE /external/posts/{id} - удалить пост
        print("\n5. DELETE /external/posts/1 - Удалить пост с ID=1")
        try:
            response = await client.delete(f"{base_url}/external/posts/1")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 60)
        print("Тестирование завершено")
        print("=" * 60)


if __name__ == "__main__":
    print("""
Перед запуском убедитесь, что сервер FastAPI запущен:
    
    uv run python src/main.py
    
Или используйте команду:
    
    ./run_app.sh
    
Затем запустите этот скрипт в другом терминале:
    
    uv run python examples/external_api_example.py
    """)
