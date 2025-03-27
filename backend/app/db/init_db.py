# backend/app/db/init_db.py
"""
Database initialization functions.

This module handles database table creation and initial data seeding.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.models.user import User, Role, Permission

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_db(engine: AsyncEngine) -> None:
    """
    Initialize database tables and seed initial data.

    Args:
        engine: SQLAlchemy async engine
    """
    try:
        # Create all tables
        async with engine.begin() as conn:
            # Create schema if it doesn't exist
            await conn.execute(
                f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}"
            )

            # Create tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

        # Seed initial data
        await seed_initial_data(engine)

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


async def seed_initial_data(engine: AsyncEngine) -> None:
    """
    Seed initial data like admin user, default roles, etc.

    Args:
        engine: SQLAlchemy async engine
    """
    async with AsyncSession(engine) as session:
        # Create admin role if it doesn't exist
        admin_role = await session.execute(select(Role).where(Role.name == "admin"))
        admin_role = admin_role.scalars().first()

        if not admin_role:
            admin_role = Role(
                name="admin", description="Administrator role with full access"
            )
            session.add(admin_role)
            logger.info("Created admin role")

        # Create super admin user if it doesn't exist
        admin_user = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        admin_user = admin_user.scalars().first()

        if not admin_user:
            admin_user = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                username=settings.FIRST_SUPERUSER_EMAIL.split("@")[0],
                hashed_password=pwd_context.hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)
            logger.info(f"Created superuser: {settings.FIRST_SUPERUSER_EMAIL}")

        # Create basic permissions if they don't exist
        basic_permissions = [
            ("experiment_create", "Create experiments", "experiment", "create"),
            ("experiment_read", "View experiments", "experiment", "read"),
            ("experiment_update", "Update experiments", "experiment", "update"),
            ("experiment_delete", "Delete experiments", "experiment", "delete"),
            ("feature_flag_create", "Create feature flags", "feature_flag", "create"),
            ("feature_flag_read", "View feature flags", "feature_flag", "read"),
            ("feature_flag_update", "Update feature flags", "feature_flag", "update"),
            ("feature_flag_delete", "Delete feature flags", "feature_flag", "delete"),
        ]

        for name, description, resource, action in basic_permissions:
            permission = await session.execute(
                select(Permission).where(Permission.name == name)
            )
            permission = permission.scalars().first()

            if not permission:
                permission = Permission(
                    name=name, description=description, resource=resource, action=action
                )
                session.add(permission)
                logger.debug(f"Created permission: {name}")

        # Commit all changes
        await session.commit()
        logger.info("Initial data seeded successfully")
