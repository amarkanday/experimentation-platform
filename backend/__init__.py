import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, text
import sys
from pathlib import Path
from backend.app.core.config import settings

database_url = os.getenv("DATABASE_URI", str(settings.DATABASE_URI))
