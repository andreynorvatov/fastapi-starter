import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

async def event_generator() -> "async generator":
    counter = 0
    while True:
        counter += 1
        yield f"data: Event {counter}\n\n"
        await asyncio.sleep(1)

@router.get("/sse", response_class=StreamingResponse)
async def sse_endpoint():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
