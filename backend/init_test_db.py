import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.db.init_db import init_db

async def main():
    # Set environment variables
    os.environ["POSTGRES_DB"] = "experimentation_test"
    os.environ["POSTGRES_SCHEMA"] = "test_experimentation"
    os.environ["APP_ENV"] = "test"

    # Create async engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/experimentation_test"
    )

    # Initialize database
    await init_db(engine)

if __name__ == "__main__":
    asyncio.run(main())
