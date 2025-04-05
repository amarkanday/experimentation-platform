# scripts/validate_models.py
import sys
import inspect
from sqlalchemy import Column, inspect as sqlalchemy_inspect
from sqlalchemy.orm import DeclarativeBase, declared_attr

# Try to import DeclarativeMeta based on SQLAlchemy version
try:
    # For SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import DeclarativeMeta
except ImportError:
    try:
        # For SQLAlchemy 2.x
        from sqlalchemy.orm.decl_api import DeclarativeMeta
    except ImportError:
        # Fallback for other versions
        DeclarativeMeta = object

# Import all models
from backend.app.models.base import Base
from backend.app.models import *  # Import all models


def validate_models():
    """Validate all SQLAlchemy models."""
    all_models = []

    # Get all model classes
    for name, obj in inspect.getmembers(sys.modules["backend.app.models"]):
        # Check if it's a SQLAlchemy model class
        if isinstance(obj, DeclarativeMeta) or (
            hasattr(obj, "__tablename__") and issubclass(obj, Base)
        ):
            all_models.append(obj)

    print(f"Found {len(all_models)} models to validate")

    for model in all_models:
        print(f"\nValidating model: {model.__name__}")

        # Check tablename
        if not hasattr(model, "__tablename__"):
            print(f"  ERROR: {model.__name__} has no __tablename__ attribute")
        else:
            print(f"  Table name: {model.__tablename__}")

        # Skip inspection for Base class itself
        if model.__name__ == "Base":
            continue

        try:
            # Check columns
            mapper = sqlalchemy_inspect(model)
            print(f"  Columns: {', '.join([c.name for c in mapper.columns])}")

            # Check relationships
            relationships = mapper.relationships.items()
            if relationships:
                print("  Relationships:")
                for name, rel in relationships:
                    print(f"    - {name} → {rel.mapper.class_.__name__}")

            # Check table_args
            if hasattr(model, "__table_args__"):
                print("  Has table_args configuration")

        except Exception as e:
            print(f"  ERROR inspecting model: {str(e)}")

        # Check inheritance from Base
        if not issubclass(model, Base):
            print(f"  ERROR: {model.__name__} does not inherit from Base")

    print("\nValidation complete!")


if __name__ == "__main__":
    validate_models()
