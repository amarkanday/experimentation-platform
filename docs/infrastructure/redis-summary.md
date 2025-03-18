# ElastiCache Redis Cluster Implementation

## Overview

This document summarizes the implementation of ElastiCache Redis for the experimentation platform using AWS CDK. The Redis cluster provides high-performance caching to optimize database access patterns, improve response times, and reduce load on your primary data stores.

## Key Features

### High Availability & Scalability
- **Multi-AZ Deployment**: Production and staging environments use replicas across multiple availability zones
- **Automatic Failover**: Seamless failover to replicas in case of primary node failure
- **Environment-Based Scaling**: Cluster size and instance types scale based on environment needs
- **Read Replicas**: Read requests can be distributed across replicas for improved performance

### Security
- **KMS Encryption**: Data at rest protected using a dedicated KMS key
- **TLS Encryption**: Data in transit protected using TLS
- **Private Subnet Placement**: Instances deployed in private subnets for network isolation
- **Security Group Restrictions**: Access limited to application tier and bastion hosts
- **Parameter Group Security**: Dangerous commands disabled via parameter group

### Performance Optimization
- **Memory-Optimized Instances**: Production uses r6g.large instances optimized for caching
- **Custom Parameter Group**: Redis parameters tuned for experimentation platform workloads
- **Active Defragmentation**: Automatic memory defragmentation to reduce memory fragmentation
- **Lazy Eviction**: Background eviction processes to maintain performance
- **Redis 7.0**: Latest Redis version with improved performance and features

### Operational Excellence
- **Automated Snapshots**: Daily backups with retention based on environment
- **Maintenance Windows**: Scheduled during off-peak hours
- **Auto-Minor Version Upgrades**: Automatic application of minor version updates
- **SSM Parameter Integration**: Connection details stored in SSM Parameter Store
- **CloudFormation Outputs**: Connection information exported for cross-stack reference

## Implementation Details

### CDK Stack

The ElastiCacheRedisStack includes:

```python
self.redis_cluster = elasticache.CfnReplicationGroup(
    self,
    "RedisCluster",
    engine="redis",
    engine_version="7.0",
    cache_node_type=instance_type,  # Environment-specific
    num_cache_clusters=cluster_size,  # Environment-specific
    automatic_failover_enabled=cluster_size > 1,
    multi_az_enabled=cluster_size > 1,
    at_rest_encryption_enabled=True,
    transit_encryption_enabled=True,
    # ... additional configuration
)
```

### Environment-Based Configuration

The stack dynamically adjusts based on environment:

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| Node Count | 1 | 2 | 3 |
| Instance Type | cache.t4g.medium | cache.m6g.large | cache.r6g.large |
| Multi-AZ | No | Yes | Yes |
| Snapshot Retention | 1 day | 3 days | 7 days |

### Parameter Group Configuration

The Redis parameter group is optimized with:

- `maxmemory-policy`: "volatile-lru" (dev/staging) or "allkeys-lru" (prod)
- `appendonly`: "yes" for durability
- `appendfsync`: "everysec" (prod/staging) or "no" (dev)
- `activedefrag`: "yes" for automatic memory defragmentation
- `lazyfree-lazy-eviction`: "yes" for background evictions

## Redis Access Pattern

A dedicated `RedisAccess` utility provides a simple interface for interacting with Redis:

```python
# Import the utility
from utils.redis_access import redis_access

# Basic key-value operations
redis_access.set("user:123:session", session_data, ttl=3600)
session = redis_access.get("user:123:session")

# Feature flag caching
redis_access.cache_feature_flag("user123", "new-checkout", True, ttl=300)
is_enabled = redis_access.get_cached_feature_flag("user123", "new-checkout")

# Experiment assignment caching
redis_access.cache_experiment_assignment("user123", "button-color", "variant-b", ttl=3600)
variant = redis_access.get_cached_experiment_assignment("user123", "button-color")

# Generic cache pattern with data fetching
user_data = redis_access.cache_get(
    "user:profile:123",
    lambda: fetch_user_from_database(123),
    ttl=600
)
```

## Common Use Cases

1. **Feature Flag Caching**: 
   - Cache feature flag evaluations to avoid repeated rule evaluation
   - Typical TTL: 5-10 minutes

2. **Experiment Assignment Caching**:
   - Cache experiment variant assignments
   - Typical TTL: 30-60 minutes

3. **Session Data Storage**:
   - Store temporary session information
   - Typical TTL: 30-120 minutes

4. **Database Query Results**:
   - Cache expensive database queries
   - Typical TTL: 1-15 minutes depending on data volatility

5. **API Rate Limiting**:
   - Track and limit API usage
   - Typical TTL: Based on rate limit window (1-60 minutes)

## Integration with Application

The Redis stack is integrated with the application through:

1. **App.py Integration**:
   ```python
   # Create the ElastiCache Redis stack
   redis_stack = ElastiCacheRedisStack(
       app,
       f"experimentation-redis-{env_name}",
       vpc=vpc_stack.vpc,
       environment=env_name,
       env=env,
   )
   
   # Add dependency from compute to Redis
   compute_stack.add_dependency(redis_stack)
   ```

2. **Connection Management**:
   - Connection details stored in SSM Parameter Store
   - Automatic failover to read replicas for read operations
   - Connection pooling and health checking

3. **Utils Directory**:
   - `redis_access.py` should be placed in your `utils/` or `lib/` directory
   - Import in Lambda functions and application code as needed

## Best Practices

1. **Use Appropriate TTLs**:
   - Short TTLs for rapidly changing data
   - Longer TTLs for more static data
   - Consider data consistency requirements

2. **Connection Management**:
   - Reuse connections when possible
   - Implement connection retry logic
   - Handle connection failures gracefully

3. **Cache Invalidation**:
   - Design explicit cache invalidation mechanisms
   - Consider using versioned cache keys for complex objects

4. **Key Design**:
   - Use hierarchical key naming (`resource:id:attribute`)
   - Include version information if data format might change
   - Be consistent with key naming patterns

5. **Memory Management**:
   - Monitor memory usage
   - Set reasonable TTLs to prevent memory exhaustion
   - Use Hash data structures for memory efficiency with small objects

## Deployment Instructions

```bash
# Deploy the Redis stack
cdk deploy experimentation-redis-dev

# Deploy all stacks
cdk deploy --all
```

## Security Considerations

1. **No Public Access**: Redis is never exposed to the internet
2. **Encryption**: Data is encrypted both at rest and in transit
3. **Access Control**: Limited to specific security groups
4. **Command Restrictions**: Dangerous commands are disabled
5. **IAM Permissions**: Principle of least privilege for accessing connection information

These security measures ensure that your Redis cluster is protected against unauthorized access and data breaches.
