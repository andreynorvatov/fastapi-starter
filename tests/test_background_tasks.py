import asyncio
import pytest
from src.background_tasks import periodic_task
from src.logger import logger

@pytest.mark.asyncio
async def test_periodic_task_logs_and_sleeps(monkeypatch):
    """
    Test that `periodic_task` logs a message and then sleeps.
    The test patches `logger.info` to capture log messages and patches
    `asyncio.sleep` to raise ``CancelledError`` after the first sleep,
    which stops the infinite loop after a single iteration.
    """
    logged_messages = []

    def fake_info(msg: str):
        logged_messages.append(msg)

    async def fake_sleep(seconds: float):
        # Simulate a quick sleep and then cancel the task to exit the loop.
        raise asyncio.CancelledError

    # Apply patches
    monkeypatch.setattr(logger, "info", fake_info)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    # Run the periodic task; it should raise CancelledError after the first iteration.
    task = asyncio.create_task(periodic_task())
    with pytest.raises(asyncio.CancelledError):
        await task

    # Verify that exactly one log message was emitted.
    assert logged_messages == ["Фоновая задача выполняется"]
