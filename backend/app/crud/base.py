"""
Base CRUD class for all models.

This module provides a generic base class for CRUD operations
that can be extended for specific models.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.app.models.base import Base

# Define a TypeVar for the SQLAlchemy model
ModelType = TypeVar("ModelType", bound=Base)
# Define a TypeVar for the Pydantic create schema
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# Define a TypeVar for the Pydantic update schema
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD base class with default methods to Create, Read, Update, Delete (CRUD).

    **Parameters**
    * `model`: A SQLAlchemy model class
    * `schema`: A Pydantic model (schema) class
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with a model.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            db: Database session
            id: ID of the record to get

        Returns:
            The record if found, None otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        Get a record by arbitrary field values.

        Args:
            db: Database session
            **kwargs: Field names and values to filter by

        Returns:
            The record if found, None otherwise
        """
        query = db.query(self.model)
        for field, value in kwargs.items():
            query = query.filter(getattr(self.model, field) == value)
        return query.first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            search: Optional search term

        Returns:
            List of records
        """
        query = db.query(self.model)

        # Add status filter if provided and model has status attribute
        if status and hasattr(self.model, "status"):
            query = query.filter(self.model.status == status)

        # Add search filter if provided and model has searchable fields
        if search and (hasattr(self.model, "name") or hasattr(self.model, "key")):
            search_pattern = f"%{search}%"
            search_conditions = []

            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(search_pattern))

            if hasattr(self.model, "key"):
                search_conditions.append(self.model.key.ilike(search_pattern))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return query.offset(skip).limit(limit).all()

    def get_multi_by_owner(
        self,
        db: Session,
        *,
        owner_id: Union[UUID, str],
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ModelType]:
        """
        Get multiple records owned by a specific user.

        Args:
            db: Database session
            owner_id: ID of the owner user
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            search: Optional search term

        Returns:
            List of records
        """
        query = db.query(self.model).filter(self.model.owner_id == owner_id)

        # Add status filter if provided and model has status attribute
        if status and hasattr(self.model, "status"):
            query = query.filter(self.model.status == status)

        # Add search filter if provided and model has searchable fields
        if search and (hasattr(self.model, "name") or hasattr(self.model, "key")):
            search_pattern = f"%{search}%"
            search_conditions = []

            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(search_pattern))

            if hasattr(self.model, "key"):
                search_conditions.append(self.model.key.ilike(search_pattern))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, status: Optional[str] = None, search: Optional[str] = None) -> int:
        """
        Count records with optional filtering.

        Args:
            db: Database session
            status: Optional status filter
            search: Optional search term

        Returns:
            Count of records
        """
        query = db.query(func.count(self.model.id))

        # Add status filter if provided and model has status attribute
        if status and hasattr(self.model, "status"):
            query = query.filter(self.model.status == status)

        # Add search filter if provided and model has searchable fields
        if search and (hasattr(self.model, "name") or hasattr(self.model, "key")):
            search_pattern = f"%{search}%"
            search_conditions = []

            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(search_pattern))

            if hasattr(self.model, "key"):
                search_conditions.append(self.model.key.ilike(search_pattern))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return query.scalar() or 0  # Return 0 if None

    def count_by_owner(
        self, db: Session, owner_id: Union[UUID, str], status: Optional[str] = None, search: Optional[str] = None
    ) -> int:
        """
        Count records owned by a specific user.

        Args:
            db: Database session
            owner_id: ID of the owner user
            status: Optional status filter
            search: Optional search term

        Returns:
            Count of records
        """
        query = db.query(func.count(self.model.id)).filter(self.model.owner_id == owner_id)

        # Add status filter if provided and model has status attribute
        if status and hasattr(self.model, "status"):
            query = query.filter(self.model.status == status)

        # Add search filter if provided and model has searchable fields
        if search and (hasattr(self.model, "name") or hasattr(self.model, "key")):
            search_pattern = f"%{search}%"
            search_conditions = []

            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(search_pattern))

            if hasattr(self.model, "key"):
                search_conditions.append(self.model.key.ilike(search_pattern))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return query.scalar() or 0  # Return 0 if None

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            db: Database session
            obj_in: Data to create the record with

        Returns:
            The created record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.

        Args:
            db: Database session
            db_obj: The record to update
            obj_in: New data to update the record with

        Returns:
            The updated record
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        """
        Remove a record.

        Args:
            db: Database session
            id: ID of the record to remove

        Returns:
            The removed record
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
