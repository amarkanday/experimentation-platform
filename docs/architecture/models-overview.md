# Experimentation Platform Models Overview

This document provides a comprehensive overview of the data models used in the experimentation platform. It explains the purpose of each model, its relationships, and key fields.

## Core Models

### 1. `Base` and `BaseModel`

**Purpose**: Provide common functionality for all models in the system.

**Key Features**:
- `id` (UUID): Primary key for all models
- `created_at`: Timestamp when the record was created
- `updated_at`: Timestamp when the record was last updated
- `to_dict()`: Method to convert model instances to dictionaries for serialization

## User Management Models

### 2. `User`

**Purpose**: Represent users who can create and manage experiments.

**Key Fields**:
- `username`: Unique username for login
- `email`: Email address for communication
- `hashed_password`: Securely stored password
- `full_name`: User's full name
- `is_active`: Whether the user account is active
- `is_superuser`: Whether the user has administrative privileges
- `last_login`: When the user last logged in
- `preferences`: JSON field for user preferences

**Relationships**:
- `experiments`: One-to-many relationship with experiments created by this user
- `feature_flags`: One-to-many relationship with feature flags created by this user
- `roles`: Many-to-many relationship with roles

### 3. `Role` and `Permission`

**Purpose**: Implement role-based access control (RBAC).

**Key Fields**:
- `Role.name`: Name of the role (e.g., "Admin", "Editor")
- `Permission.name`: Name of the permission
- `Permission.resource`: Resource being protected (e.g., "experiment", "feature_flag")
- `Permission.action`: Action being protected (e.g., "create", "read", "update", "delete")

**Relationships**:
- `roles_users`: Junction table linking roles to users
- `roles_permissions`: Junction table linking roles to permissions

## Experiment Models

### 4. `Experiment`

**Purpose**: Central model representing an A/B test or other experiment type.

**Key Fields**:
- `name`: Human-readable name of the experiment
- `description`: Detailed description of the experiment's purpose
- `hypothesis`: The hypothesis being tested
- `status`: Current status (DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED)
- `experiment_type`: Type of experiment (A_B, MULTIVARIATE, SPLIT_URL, BANDIT)
- `owner_id`: User who created the experiment
- `start_date`: When the experiment started
- `end_date`: When the experiment ended
- `targeting_rules`: JSON field with rules for targeting specific users
- `metrics`: JSON field with metrics being tracked
- `tags`: JSON field with categorization tags

**Relationships**:
- `owner`: Many-to-one relationship with the User who created this experiment
- `variants`: One-to-many relationship with Variant instances
- `assignments`: One-to-many relationship with Assignment instances
- `events`: One-to-many relationship with Event instances
- `metric_definitions`: One-to-many relationship with Metric instances

### 5. `Variant`

**Purpose**: Represent different variations being tested in an experiment.

**Key Fields**:
- `experiment_id`: Foreign key to the experiment
- `name`: Name of the variant
- `description`: Detailed description of the variant
- `is_control`: Whether this is the control/baseline variant
- `traffic_allocation`: Percentage of traffic allocated to this variant (0-100)
- `configuration`: JSON field with variant-specific configuration

**Relationships**:
- `experiment`: Many-to-one relationship with the parent Experiment
- `assignments`: One-to-many relationship with user assignments to this variant

### 6. `Metric`

**Purpose**: Define metrics that measure experiment success.

**Key Fields**:
- `name`: Name of the metric
- `description`: Detailed description of what the metric measures
- `event_name`: Name of the event that triggers this metric
- `metric_type`: Type of metric (CONVERSION, REVENUE, COUNT, DURATION, CUSTOM)
- `is_primary`: Whether this is the primary metric for the experiment
- `aggregation_method`: How to aggregate the metric (e.g., average, sum)
- `minimum_sample_size`: Minimum sample size needed for statistical significance
- `expected_effect`: Expected effect size for power calculations
- `event_value_path`: JSON path to extract value from event payload
- `lower_is_better`: Whether lower values indicate success

**Relationships**:
- `experiment`: Many-to-one relationship with the parent Experiment

## Assignment and Tracking Models

### 7. `Assignment`

**Purpose**: Track which users are assigned to which experiment variants.

**Key Fields**:
- `experiment_id`: Foreign key to the experiment
- `variant_id`: Foreign key to the assigned variant
- `user_id`: External user identifier
- `context`: JSON field with user context at assignment time

**Relationships**:
- `experiment`: Many-to-one relationship with the Experiment
- `variant`: Many-to-one relationship with the assigned Variant

### 8. `Event`

**Purpose**: Track user interactions and metric data for analysis.

**Key Fields**:
- `event_type`: Type of event (e.g., "page_view", "click", "purchase")
- `user_id`: External user identifier
- `experiment_id`: Foreign key to the experiment (optional)
- `feature_flag_id`: Foreign key to the feature flag (optional)
- `variant_id`: Foreign key to the variant (optional)
- `value`: Numeric value for the event (optional)
- `event_metadata`: JSON field with additional event data
- `created_at`: Timestamp when the event occurred

**Relationships**:
- `experiment`: Many-to-one relationship with the related Experiment
- `feature_flag`: Many-to-one relationship with the related FeatureFlag

## Feature Flag Models

### 9. `FeatureFlag`

**Purpose**: Manage feature toggles for controlled rollouts and experimentation.

**Key Fields**:
- `key`: Unique identifier for the feature flag (slug format)
- `name`: Human-readable name of the feature flag
- `description`: Detailed description of the feature flag's purpose
- `status`: Current status (ACTIVE, INACTIVE)
- `owner_id`: User who created the feature flag
- `targeting_rules`: JSON field with rules for enabling the flag for specific users
- `rollout_percentage`: Percentage of users who should see the feature (0-100)
- `variants`: JSON field with variant configurations for multivariate flags
- `tags`: JSON field with categorization tags

**Relationships**:
- `owner`: Many-to-one relationship with the User who created this feature flag
- `overrides`: One-to-many relationship with FeatureFlagOverride instances
- `events`: One-to-many relationship with Event instances

### 10. `FeatureFlagOverride`

**Purpose**: Override feature flag settings for specific users.

**Key Fields**:
- `feature_flag_id`: Foreign key to the feature flag
- `user_id`: External user identifier
- `value`: JSON field with override value
- `reason`: Reason for the override
- `expires_at`: When the override expires (optional)

**Relationships**:
- `feature_flag`: Many-to-one relationship with the parent FeatureFlag

## Data Flow and Relationships

The experimentation platform's data models are interconnected in a way that enables:

1. **Experiment Definition**: Users create experiments with variants and metrics
2. **User Assignment**: Users are assigned to experiment variants
3. **Event Tracking**: User interactions are tracked as events
4. **Analysis**: Events are aggregated to calculate metrics and determine experiment outcomes

### Key Relationship Flows:

1. User → Experiment → Variants → Metrics
2. User → Variant ← Assignment
3. Event → Experiment → Metrics
4. Event → Feature Flag → Overrides

## Database Schema Design

All models are organized within the PostgreSQL `experimentation` schema to isolate them from other application components. Key indexes have been created to optimize common queries:

- Experiment status + dates: For finding active experiments
- Owner + status: For finding a user's active experiments
- Assignment experiment + user: Unique constraint to ensure consistent assignments
- Event user + type: For quickly retrieving specific event types for a user
- Event experiment + type: For fast metric calculations

## Additional Constraints and Validations

Several database constraints ensure data integrity:

- Experiment end date must be after start date
- Variant traffic allocation must be between 0 and 100
- Total variant traffic allocation per experiment must sum to 100
- Metric names must be unique within an experiment
