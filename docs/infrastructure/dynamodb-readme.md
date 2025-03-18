# DynamoDB Tables Configuration for Experimentation Platform

This document explains the DynamoDB table designs used in the experimentation platform and how to work with them effectively.

## Table Design Overview

The experimentation platform uses five primary DynamoDB tables:

1. **Assignments** - Tracks which users are assigned to which experiment variants
2. **Events** - Stores user interaction events for experiment analysis
3. **Experiments** - Contains experiment configurations and metadata
4. **FeatureFlags** - Stores feature flag definitions
5. **Overrides** - Manages user-specific experiment or feature overrides

## Table Schemas and Access Patterns

### Assignments Table

**Primary Purpose**: Track user experiment assignments

**Key Structure**:
- **Partition Key**: `id` (UUID)
- **Global Secondary Indexes**:
  - **user-experiment-index**: `user_id` (partition), `experiment_id` (sort)
  - **experiment-index**: `experiment_id` (partition), `assigned_at` (sort)
  - **user-index**: `user_id` (partition), `assigned_at` (sort)
  - **variation-index**: `variation` (partition), `assigned_at` (sort)

**Common Fields**:
- `id`: Unique identifier (UUID)
- `user_id`: User identifier 
- `experiment_id`: Experiment identifier
- `variation`: Assigned variation ID
- `assigned_at`: Timestamp when assignment was created
- `ttl`: Time-to-live for automatic expiration

**Access Patterns**:
- Get assignment by ID
- Get assignment for specific user and experiment (most common)
- Get all assignments for a user
- Get all users assigned to an experiment
- Get all users assigned to a specific variation

### Events Table

**Primary Purpose**: Track user events for experiment analysis

**Key Structure**:
- **Partition Key**: `id` (UUID)
- **Sort Key**: `timestamp` (ISO 8601 string)
- **Global Secondary Indexes**:
  - **user-event-index**: `user_id` (partition), `timestamp` (sort)
  - **experiment-event-index**: `experiment_id` (partition), `timestamp` (sort)
  - **event-type-index**: `event_type` (partition), `timestamp` (sort)

**Common Fields**:
- `id`: Unique identifier (UUID)
- `user_id`: User identifier
- `timestamp`: ISO 8601 timestamp
- `timestamp_epoch`: Unix timestamp
- `event_type`: Type of event
- `data`: JSON object with event details
- `experiment_id`: Related experiment (if applicable)
- `ttl`: Time-to-live for automatic expiration

**Access Patterns**:
- Get event by ID and timestamp
- Get all events for a user (with optional time range)
- Get all events for an experiment (with optional time range)
- Get all events of a specific type (with optional time range)

### Experiments Table

**Primary Purpose**: Store experiment definitions and metadata

**Key Structure**:
- **Partition Key**: `id` (UUID)
- **Global Secondary Indexes**:
  - **status-index**: `status` (partition), `created_at` (sort)
  - **owner-index**: `owner` (partition), `created_at` (sort)
  - **tag-index**: `tag` (partition), `created_at` (sort)

**Common Fields**:
- `id`: Unique identifier (UUID)
- `name`: Experiment name
- `description`: Experiment description
- `status`: Experiment status (draft, active, paused, completed)
- `variations`: Array of variation objects
- `created_at`: ISO 8601 timestamp
- `updated_at`: ISO 8601 timestamp
- `owner`: User who created the experiment
- `tags`: Array of tags

**Access Patterns**:
- Get experiment by ID
- Get experiments by status
- Get experiments by owner
- Get experiments by tag

### FeatureFlags Table

**Primary Purpose**: Store feature flag definitions

**Key Structure**:
- **Partition Key**: `id` (UUID)
- **Global Secondary Indexes**:
  - **status-index**: `status` (partition), `updated_at` (sort)
  - **tag-index**: `tag` (partition), `updated_at` (sort)

**Common Fields**:
- `id`: Unique identifier (UUID)
- `name`: Feature flag name
- `description`: Feature flag description
- `rules`: JSON object with targeting rules
- `status`: Feature flag status (active, inactive)
- `created_at`: ISO 8601 timestamp
- `updated_at`: ISO 8601 timestamp
- `tags`: Array of tags

**Access Patterns**:
- Get feature flag by ID
- Get all active feature flags
- Get feature flags by tag

### Overrides Table

**Primary Purpose**: Store user-specific overrides for experiments or features

**Key Structure**:
- **Partition Key**: `id` (UUID)
- **Global Secondary Indexes**:
  - **user-index**: `user_id` (partition), `created_at` (sort)
  - **target-index**: `target_id` (partition), `created_at` (sort)
  - **type-index**: `type` (partition), `created_at` (sort)

**Common Fields**:
- `id`: Unique identifier (UUID)
- `user_id`: User identifier
- `target_id`: Experiment ID or feature flag ID
- `type`: Type of override (experiment, feature)
- `value`: Override value
- `created_at`: ISO 8601 timestamp
- `ttl`: Time-to-live for automatic expiration

**Access Patterns**:
- Get override by ID
- Get all overrides for a user
- Get all overrides for a specific experiment or feature

## Billing Mode Configuration

The tables are configured with different billing modes based on the environment:

- **Development/Staging**: On-demand (PAY_PER_REQUEST)
  - Simpler capacity management
  - Cost scales with usage
  - No need to predict traffic patterns

- **Production**: Provisioned with auto-scaling
  - More cost-effective for predictable workloads
  - Auto-scaling based on 70% utilization target
  - Scale in/out cooldown periods to prevent thrashing

## TTL (Time-to-Live) Configuration

Time-to-live is configured for these tables:

- **Assignments**: 30 days by default
- **Events**: 90 days by default
- **Overrides**: 30 days by default

This ensures automatic cleanup of old data, reducing storage costs and improving query performance.

## Data Access Utility

A `DynamoDBAccess` utility class is provided to simplify interaction with the tables:

```python
# Example usage
from db_access import dynamodb_access

# Create an assignment
assignment = dynamodb_access.create_assignment(
    user_id="user123",
    experiment_id="exp456",
    variation="variant_b"
)

# Get a user's assignment for an experiment
assignment = dynamodb_access.get_user_assignment(
    user_id="user123",
    experiment_id="exp456"
)

# Create an event
event = dynamodb_access.create_event(
    user_id="user123",
    event_type="page_view",
    data={"page": "/checkout", "referrer": "/cart"},
    experiment_id="exp456"
)

# Get active experiments
active_experiments = dynamodb_access.get_experiments_by_status("active")
```

## Deployment Instructions

To deploy the DynamoDB tables:

```bash
# Deploy only the DynamoDB stack
cdk deploy experimentation-dynamodb-dev

# Or deploy all stacks
cdk deploy --all
```

## Cost Optimization Tips

1. **Use TTL effectively** - Set appropriate TTL values to automatically expire old data
2. **Choose the right billing mode** - On-demand for unpredictable workloads, provisioned with auto-scaling for predictable ones
3. **Use GSIs efficiently** - Create only necessary indexes and use projection attributes wisely
4. **Monitor usage patterns** - Use CloudWatch metrics to identify hot keys and optimize access patterns
5. **Use batching for write operations** - Use batch operations when writing multiple items to reduce costs

## Best Practices

1. **Keep items small** - DynamoDB charges based on item size; keep items as small as possible
2. **Use consistent naming conventions** - Use consistent attribute names across tables
3. **Design for query patterns** - Design tables and indexes based on query patterns, not data relationships
4. **Use sparse indexes** - For attributes that are only present in some items
5. **Use LSIs sparingly** - Local Secondary Indexes share provisioned throughput with the base table
6. **Avoid scans** - Use query operations wherever possible; avoid table scans
7. **Use pagination** - For large result sets, use pagination with the `Limit` and `LastEvaluatedKey` parameters

## Monitoring and Maintenance

The DynamoDB tables are integrated with CloudWatch for monitoring:

- Consumed capacity units (read/write)
- Throttled requests
- Error rates
- Latency

CloudWatch alarms are configured to alert on:
- High consumption (above 80% of provisioned capacity)
- Throttled requests
- System errors
