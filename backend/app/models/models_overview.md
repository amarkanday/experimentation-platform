# Experimentation Platform Models

## 1. `base.py`
**Purpose**: Provides a base class for all models.

**Key Features**:
- Defines `Base` using SQLAlchemy's `declarative_base()` to serve as the base for all ORM models.
- Includes a `BaseModel` class with common fields like `id`, `created_at`, and `updated_at`.
- Implements a `to_dict()` method to convert model instances to dictionaries for serialization.

---

## 2. `user.py`
**Purpose**: Defines models for user authentication, roles, and permissions.

**Key Models**:
- `User`: Represents a user with fields like `username`, `email`, `hashed_password`, and relationships to roles, experiments, and feature flags.
- `Role`: Represents a role that groups permissions.
- `Permission`: Represents granular access controls for resources and actions.

**Relationships**:
- Many-to-many relationships between users and roles (`user_role_association`).
- Many-to-many relationships between roles and permissions (`role_permission_association`).

---

## 3. `experiment.py`
**Purpose**: Defines models for managing experiments and their variants.

**Key Models**:
- `Experiment`: Represents an A/B test or other types of experiments with fields like `name`, `status`, `experiment_type`, and relationships to variants, assignments, and events.
- `Variant`: Represents variations within an experiment, with fields like `name`, `traffic_allocation`, and `configuration`.

**Relationships**:
- `Experiment` has many `Variant` objects.
- `Experiment` has many `Assignment` and `Event` objects.

---

## 4. `feature_flag.py`
**Purpose**: Defines models for feature flags and their overrides.

**Key Models**:
- `FeatureFlag`: Represents a feature toggle with fields like `key`, `status`, `rollout_percentage`, and relationships to overrides and events.
- `FeatureFlagOverride`: Represents user-specific overrides for feature flags.

**Relationships**:
- `FeatureFlag` has many `FeatureFlagOverride` and `Event` objects.

---

## 5. `assignment.py`
**Purpose**: Tracks user assignments to experiment variants.

**Key Model**:
- `Assignment`: Represents a user's assignment to a specific experiment and variant, with fields like `experiment_id`, `variant_id`, and `context`.

**Relationships**:
- `Assignment` links `Experiment` and `Variant`.

---

## 6. `event.py`
**Purpose**: Tracks user interactions and metrics related to experiments and feature flags.

**Key Model**:
- `Event`: Represents an event with fields like `event_type`, `user_id`, `experiment_id`, `feature_flag_id`, and `value`.

**Relationships**:
- `Event` links to `Experiment`, `FeatureFlag`, and `Variant`.

---

## 7. `__init__.py`
**Purpose**: Serves as the entry point for importing all models.

**Key Features**:
- Imports all models and their relationships.
- Defines the `__all__` list to make models discoverable by tools like Alembic for database migrations.

---

## 8. `segment.py`
**Purpose**: Placeholder for segmentation models (not implemented in the provided code).

**Potential Use**: Could define models for user segmentation, such as user groups or targeting rules for experiments and feature flags.
