from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.logger import logger
from src.config import settings

router = APIRouter()

templates = Jinja2Templates(directory="src/system/home_page/templates")


async def get_db_schema(session: AsyncSession):
    """Return a list of tables with their column names, types and foreign key relationships using the provided session."""
    logger.info("Fetching DB schema using session")
    tables = []
    # Get the underlying connection from the session
    conn = await session.connection()
    # Use the connection's run_sync to execute inspection functions
    table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    logger.info(f"Found tables: {table_names}")
    for table_name in table_names:
        # Retrieve columns for each table
        columns = await conn.run_sync(
            lambda sync_conn, tn=table_name: inspect(sync_conn).get_columns(tn)
        )
        # Retrieve foreign keys for each table
        foreign_keys = await conn.run_sync(
            lambda sync_conn, tn=table_name: inspect(sync_conn).get_foreign_keys(tn)
        )
        # Transform foreign key info into a simpler structure
        fk_info = []
        for fk in foreign_keys:
            constrained = fk.get('constrained_columns', [])
            referred = fk.get('referred_table')
            referred_cols = fk.get('referred_columns', [])
            for col, ref_col in zip(constrained, referred_cols):
                fk_info.append({
                    "column": col,
                    "referred_table": referred,
                    "referred_column": ref_col,
                })
        tables.append({
            "name": table_name,
            "columns": [(c["name"], str(c["type"]), c.get('comment', '')) for c in columns],
            "foreign_keys": fk_info,
        })
    logger.info(f"DB schema fetched: {tables}")
    return tables


@router.get("/")
async def home(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    tables = await get_db_schema(session)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "service_name": settings.PROJECT_NAME,
            "tables": tables,
            "settings": settings
        },
    )
