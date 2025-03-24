# Experimentation Platform Models and Migrations

This document describes the data models used in the Experimentation Platform and provides instructions for managing database migrations.

## Data Models

The Experimentation Platform uses SQLAlchemy ORM models organized in a structured, modular architecture.

### Base Models

All models inherit from a common base class that provides standard functionality:

- `BaseModel`: A mixin class providing common columns (`id`, `created_at`, `updated_at`) and utility methods
- `Base`: SQLAlchemy declarative base for all models

### User Management Models

#### User

The User model represents platform users with authentication and permission data.

**Key Fields:**
- `id`: UUID primary key
- `username`: Unique username (required)
- `email`: Unique email address (required)
- `hashed_password`: Securely stored password hash
- `full_name`: User's full name
- `is_active`: Whether the user account is active
- `is_superuser`: Whether the user has superuser privileges
- `last_login`: Timestamp of last login
- `preferences`: JSON field for user preferences

**Relationships:**
- `experiments`: One-to-many relationship to experiments owned by this user
- `feature_flags`: One-to-many relationship to feature flags owned by this user
- `roles`: Many-to-many relationship to Role model

#### Role

The Role model represents user roles for permission grouping.

**Key Fields:**
- `id`: UUID primary key
- `name`: Unique role name (required)
- `description`: Role description

**Relationships:**
- `users`: Many-to-many relationship to User model
- `permissions`: Many-to-many relationship to Permission model

#### Permission

The Permission model defines granular access controls.

**Key Fields:**
- `id`: UUID primary key
- `name`: Unique permission name (required)
- `description`: Permission description
- `resource`: Resource type this permission applies to (e.g., 'experiment', 'feature_flag')
- `action`: Action type (e.g., 'create', 'read', 'update', 'delete')

**Relationships:**
- `roles`: Many-to-many relationship to Role model

### Experiment Models

#### Experiment

The Experiment model represents A/B tests and other experiment types.

**Key Fields:**
- `id`: UUID primary key
- `name`: Experiment name (required)
- `description`: Experiment description
- `hypothesis`: Experiment hypothesis
- `status`: Status enum (DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED)
- `experiment_type`: Type enum (A_B, MULTIVARIATE, SPLIT_URL, BANDIT)
- `owner_id`: Foreign key to User model
- `start_date`: Experiment start date
- `end_date`: Experiment end date
- `targeting_rules`: JSON field for user segmentation rules
- `metrics`: JSON field for metrics configuration
- `tags`: JSON field for categorization

**Relationships:**
- `owner`: Many-to-one relationship to User model
- `variants`: One-to-many relationship to Variant model
- `assignments`: One-to-many relationship to Assignment model
- `events`: One-to-many relationship to Event model
- `metric_definitions`: One-to-many relationship to Metric model

#### Variant

The Variant model represents experiment variations.

**Key Fields:**
- `id`: UUID primary key
- `experiment_id`: Foreign key to Experiment model (required)
- `name`: Variant name (required)
- `description`: Variant description
- `is_control`: Boolean indicating if this is the control variant
- `traffic_allocation`: Percentage of traffic to allocate (0-100)
- `configuration`: JSON field for variant-specific settings

**Relationships:**
- `experiment`: Many-to-one relationship to Experiment model
- `assignments`: One-to-many relationship to Assignment model

#### Metric

The Metric model defines measurements for experiments.

**Key Fields:**
- `id`: UUID primary key
- `name`: Metric name (required)
- `description`: Metric description
- `event_name`: Event name to track (required)
- `metric_type`: Type enum (CONVERSION, REVENUE, COUNT, DURATION, CUSTOM)
- `is_primary`: Boolean indicating if this is the primary metric
- `aggregation_method`: Method for aggregating events (e.g., 'average', 'sum')
- `minimum_sample_size`: Minimum sample size for statistical significance
- `expected_effect`: Expected effect size for power calculations
- `event_value_path`: JSON path to extract value from event payload
- `lower_is_better`: Boolean indicating if lower values are better
- `experiment_id`: Foreign key to Experiment model (required)

**Relationships:**
- `experiment`: Many-to-one relationship to Experiment model

### Assignment Models

#### Assignment

The Assignment model tracks user experiment assignments.

**Key Fields:**
- `id`: UUID primary key
- `experiment_id`: Foreign key to Experiment model (required)
- `variant_id`: Foreign key to Variant model (required)
- `user_id`: External user identifier (required)
- `context`: JSON field for user attributes used for targeting

**Relationships:**
- `experiment`: Many-to-one relationship to Experiment model
- `variant`: Many-to-one relationship to Variant model

### Event Models

#### Event

The Event model records user interactions and metric data.

**Key Fields:**
- `id`: UUID primary key
- `event_type`: Event type identifier (required)
- `user_id`: External user identifier (required)
- `experiment_id`: Foreign key to Experiment model
- `feature_flag_id`: Foreign key to FeatureFlag model
- `variant_id`: Foreign key to Variant model
- `value`: Numeric value if applicable
- `event_metadata`: JSON field for additional data
- `created_at`: String timestamp of event creation (required)

**Relationships:**
- `experiment`: Many-to-one relationship to Experiment model
- `feature_flag`: Many-to-one relationship to FeatureFlag model

### Feature Flag Models

#### FeatureFlag

The FeatureFlag model manages feature toggles.

**Key Fields:**
- `id`: UUID primary key
- `key`: Unique identifier string (required)
- `name`: Feature flag name (required)
- `description`: Feature flag description
- `status`: Status enum (ACTIVE, INACTIVE)
- `owner_id`: Foreign key to User model
- `targeting_rules`: JSON field for flag enablement rules
- `rollout_percentage`: Percentage for gradual rollout (0-100)
- `variants`: JSON field for multivariate flags
- `tags`: JSON field for categorization

**Relationships:**
- `owner`: Many-to-one relationship to User model
- `overrides`: One-to-many relationship to FeatureFlagOverride model
- `events`: One-to-many relationship to Event model

#### FeatureFlagOverride

The FeatureFlagOverride model handles user-specific feature flag settings.

**Key Fields:**
- `id`: UUID primary key
- `feature_flag_id`: Foreign key to FeatureFlag model (required)
- `user_id`: External user identifier (required)
- `value`: JSON value for the override (required)
- `reason`: Optional explanation
- `expires_at`: Optional expiration timestamp

**Relationships:**
- `feature_flag`: Many-to-one relationship to FeatureFlag model

## Database Relationship Configuration

All relationships between models are configured in the `__init__.py` file. This includes bidirectional relationships and association tables:

```python
# Bidirectional relationships
User.experiments = relationship("Experiment", back_populates="owner")
User.feature_flags = relationship("FeatureFlag", back_populates="owner")
User.roles = relationship("Role", secondary=user_role_association, backref="users")

Variant.assignments = relationship("Assignment", back_populates="variant")
Experiment.assignments = relationship(
    "Assignment", back_populates="experiment", cascade="all, delete-orphan"
)
Experiment.events = relationship("Event", back_populates="experiment")

Assignment.experiment = relationship("Experiment", back_populates="assignments")
Assignment.variant = relationship("Variant", back_populates="assignments")
```

## Database Migration Management

The Experimentation Platform uses Alembic for managing database migrations.

### Migration Structure

Migrations are stored in the `backend/migrations` directory with the following structure:

```
backend/migrations/
  ├── env.py                # Environment configuration
  ├── README                # Migration documentation
  ├── script.py.mako        # Migration script template
  └── versions/             # Migration version scripts
      ├── 001_initial.py    # Initial schema
      └── 002_feature_x.py  # Feature-specific migrations
```

### Running Migrations

To apply migrations to your database:

1. **Initialize the database schema** (first time only):
   ```bash
   alembic upgrade head
   ```

2. **Update an existing database**:
   ```bash
   alembic upgrade head
   ```

3. **Downgrade to a previous version**:
   ```bash
   alembic downgrade -1         # Downgrade by one revision
   alembic downgrade <revision> # Downgrade to specific revision
   ```

4. **Check current migration status**:
   ```bash
   alembic current
   ```

5. **View migration history**:
   ```bash
   alembic history
   ```

### Creating New Migrations

When you make changes to the models, you need to create a new migration:

1. **Auto-generate a migration script**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Create an empty migration script**:
   ```bash
   alembic revision -m "Description of changes"
   ```

3. **Review and modify** the generated migration script in `backend/migrations/versions/`

4. **Apply the new migration**:
   ```bash
   alembic upgrade head
   ```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Add meaningful comments** to migration scripts
3. **Test migrations** by upgrading and downgrading
4. **Ensure downgrade operations** are properly implemented
5. **Commit migrations to version control** along with model changes

## Schema Management Guidelines

1. **Create indexes** for frequently queried columns
2. **Use constraints** to enforce data integrity
3. **Add descriptive comments** to models and fields
4. **Use appropriate data types** for each field
5. **Keep migrations small and focused** on specific changes
6. **Run migration tests** before deploying to production

## Troubleshooting

### Common Migration Issues

1. **Migration can't find table**: Ensure the schema is specified correctly
2. **Foreign key constraint error**: Check that referenced tables exist and keys are valid
3. **Column type mismatch**: Ensure column types are compatible when modifying
4. **Missing relationship**: Check for bidirectional relationship setup in `__init__.py`

### Fixing Migration Problems

1. **Edit a generated migration** to fix issues before applying
2. **Create a new migration** to correct problems
3. **Manual database fixes** (use with caution)
   ```sql
   -- Example: Update alembic_version table
   UPDATE experimentation.alembic_version SET version_num = '<correct_version>';
   ```

## Development Database Setup

For development environments:

1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE experimentation_dev;
   CREATE SCHEMA experimentation;
   ```

2. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://username:password@localhost/experimentation_dev"
   ```

3. Apply migrations:
   ```bash
   alembic upgrade head
   ```

4. Verify setup:
   ```bash
   alembic current
   ```
