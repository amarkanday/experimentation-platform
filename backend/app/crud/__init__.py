"""
CRUD module for database operations.

This module provides standardized Create, Read, Update, Delete operations
for database models, following the repository pattern.
"""

from backend.app.crud.crud_user import crud_user
from backend.app.crud.crud_feature_flag import crud_feature_flag

__all__ = ["crud_user", "crud_feature_flag"]
