from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel
from sqlalchemy import inspect
from src.database import async_engine
from src.logger import logger
from src.config import settings

router = APIRouter()

templates = Jinja2Templates(directory="src/system/home_page/templates")

async def get_db_schema():
    """Return a list of tables with their column names, types and foreign key relationships using async engine."""
    logger.info("Fetching DB schema using async engine")
    tables = []
    # Use an async connection and run sync inspection functions in the appropriate context
    async with async_engine.connect() as conn:
        # Retrieve table names
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
                # fk is a dict with keys like 'constrained_columns', 'referred_table', 'referred_columns'
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
async def home(request: Request):
    tables = await get_db_schema()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "service_name": settings.PROJECT_NAME, "tables": tables, "settings": settings},
    )
