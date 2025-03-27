# Guide to Using the SQLAlchemy Models and Database Migrations

This guide explains how to use the SQLAlchemy models that we've created for the experimentation platform, and how to manage database migrations with Alembic.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Using the SQLAlchemy Models](#using-the-sqlalchemy-models)
3. [Database Migrations with Alembic](#database-migrations-with-alembic)
4. [Working with Experiments](#working-with-experiments)
5. [Working with Feature Flags](#working-with-feature-flags)
6. [Event Tracking](#event-tracking)
7. [Users and Permissions](#users-and-permissions)
8. [Model Relationships](#model-relationships)
9. [Performance Considerations](#performance-considerations)

## Project Structure

The project follows this structure:

```
├── alembic/                    # Migration scripts and configuration
│   ├── versions/               # Generated migration scripts
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako          # Template for migration scripts
├── core/
│   └── config.py               # Application configuration
├── db/
│   └── session.py              # Database session setup
├── models/                     # SQLAlchemy model definitions
│   ├── __init__.py
│   ├── base.py                 # Base model with common fields
│   ├── user.py                 # User and permission models
│   ├── experiment.py           # Experiment and variant models
│   ├── feature_flag.py         # Feature flag models
│   ├── assignment.py           # Experiment assignment models
│   └── event.py                # Event tracking models
└── .env                        # Environment variables
```

## Using the SQLAlchemy Models

### Basic Usage

Here's how to use the models in your application code:

```python
from db.session import SessionLocal
from models import Experiment, Variant, ExperimentStatus

# Create a database session
db = SessionLocal()

try:
    # Query experiments
    active_experiments = db.query(Experiment).filter(
        Experiment.status == ExperimentStatus.ACTIVE
    ).all()
    
    # Create a new experiment
    new_experiment = Experiment(
        name="Homepage Button Color Test",
        description="Testing different button colors on the homepage",
        hypothesis="A green button will have a higher click-through rate than a blue button",
        status=ExperimentStatus.DRAFT,
        owner_id=user_id
    )
    db.add(new_experiment)
    
    # Add variants to the experiment
    control_variant = Variant(
        experiment_id=new_experiment.id,
        name="Control (Blue)",
        description="The current blue button",
        is_control=True,
        traffic_allocation=50,
        configuration={"color": "blue", "hex": "#0066CC"}
    )
    
    treatment_variant = Variant(
        experiment_id=new_experiment.id,
        name="Treatment (Green)",
        description="The new green button",
        is_control=False,
        traffic_allocation=50,
        configuration={"color": "green", "hex": "#00CC66"}
    )
    
    db.add_all([control_variant, treatment_variant])
    db.commit()
    
except Exception as e:
    db.rollback()
    raise e
finally:
    db.close()
```

### With FastAPI Dependency Injection

In a FastAPI application, you can use dependency injection:

```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from models import Experiment

app = FastAPI()

@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment.to_dict()
```

## Database Migrations with Alembic

### Initial Setup

Before using migrations, make sure your database is created:

```bash
# Create the database if it doesn't exist
createdb experimentation
```

Then initialize the database with Alembic:

```bash
# Generate the initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply the migration
alembic upgrade head
```

### Creating New Migrations

Whenever you make changes to the models:

```bash
# Generate a new migration script
alembic revision --autogenerate -m "Description of changes"

# Apply the migration
alembic upgrade head
```

### Migration Commands Reference

```bash
# Upgrade to the latest version
alembic upgrade head

# Downgrade to the previous version
alembic downgrade -1

# Downgrade to a specific version
alembic downgrade <revision>

# Show current version
alembic current

# Show migration history
alembic history
```

## Working with Experiments

### Creating an Experiment

```python
from models import Experiment, Variant, ExperimentStatus, ExperimentType
from uuid import UUID

def create_experiment(db, name, description, hypothesis, owner_id, variants_data):
    """
    Create a new experiment with variants.
    
    Args:
        db: SQLAlchemy session
        name: Experiment name
        description: Experiment description
        hypothesis: Experiment hypothesis
        owner_id: User ID of experiment owner
        variants_data: List of variant configurations
    
    Returns:
        Created experiment object
    """
    # Create experiment
    experiment = Experiment(
        name=name,
        description=description,
        hypothesis=hypothesis,
        status=ExperimentStatus.DRAFT,
        experiment_type=ExperimentType.A_B,
        owner_id=UUID(owner_id) if isinstance(owner_id, str) else owner_id
    )
    db.add(experiment)
    db.flush()  # Flush to get the experiment ID
    
    # Create variants
    variants = []
    for variant_data in variants_data:
        variant = Variant(
            experiment_id=experiment.id,
            name=variant_data["name"],
            description=variant_data.get("description", ""),
            is_control=variant_data.get("is_control", False),
            traffic_allocation=variant_data.get("traffic_allocation", 50),
            configuration=variant_data.get("configuration", {})
        )
        variants.append(variant)
    
    db.ad