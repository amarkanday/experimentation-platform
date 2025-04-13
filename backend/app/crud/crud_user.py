"""
CRUD for user management.

This module provides database operations for User models.
"""

from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from backend.app.crud.base import CRUDBase
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """User CRUD operations."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            db: Database session
            email: Email of the user to get

        Returns:
            The user if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            db: Database session
            username: Username of the user to get

        Returns:
            The user if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            obj_in: Data to create the user with

        Returns:
            The created user
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user.

        Args:
            db: Database session
            db_obj: The user to update
            obj_in: New data to update the user with

        Returns:
            The updated user
        """
        update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email_or_username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            db: Database session
            email_or_username: Email or username of the user
            password: Password to verify

        Returns:
            The authenticated user if credentials are valid, None otherwise
        """
        user = self.get_by_email(db, email=email_or_username)
        if not user:
            user = self.get_by_username(db, username=email_or_username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        Check if a user is active.

        Args:
            user: The user to check

        Returns:
            True if the user is active, False otherwise
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.

        Args:
            user: The user to check

        Returns:
            True if the user is a superuser, False otherwise
        """
        return user.is_superuser


crud_user = CRUDUser(User)
