# Aurora PostgreSQL Cluster for Experimentation Platform

This guide explains the enhanced Aurora PostgreSQL setup for the experimentation platform.

## Key Features

### 1. High Availability & Scalability
- **Multi-AZ Deployment**: Production environments use multiple instances across availability zones
- **Environment-Based Scaling**: Automatically configures different instance types and counts based on environment (dev/staging/prod)
- **Read Replicas**: Separate read endpoint for scaling read operations

### 2. Security
- **Encryption at Rest**: KMS encryption for all data storage
- **Secrets Manager**: Secure handling of database credentials
- **Network Security**: Placement in isolated subnets with restricted security groups
- **SSL Enforcement**: Mandated SSL connections for data in transit

### 3. Performance Optimization
- **Parameter Groups**: Custom parameter groups optimized for the experimentation workload
- **Performance Insights**: Enabled for deep performance analysis
- **Enhanced Monitoring**: 60-second monitoring interval for detailed metrics
- **Environment-Specific Tuning**: Memory parameters optimized for each environment

### 4. Operational Excellence
- **Backup & Recovery**: 7-day backup retention with point-in-time recovery
- **Maintenance Windows**: Configured for minimal impact
- **CloudWatch Logs**: PostgreSQL logs exported to CloudWatch
- **Parameter Store Integration**: Connection details stored for easy access

## Implementation Details

### Aurora PostgreSQL Configuration
```python
self.aurora_cluster = rds.DatabaseCluster(
    self,
    "AuroraCluster",
    engine=rds.DatabaseClusterEngine.aurora_postgres(
        version=rds.AuroraPostgresEngineVersion.VER_15_3
    ),
    credentials=rds.Credentials.from_secret(db_credentials),
    # ... additional configuration ...
)
```

### Environment-Based Settings
The implementation automatically adjusts based on the environment:
- **Production**: r5.large instances, 2+ nodes, isolated subnets, deletion protection
- **Staging**: t3.medium instances, 2 nodes, private subnets
- **Development**: t3.medium instance, 1 node, private subnets

### PostgreSQL Parameter Group Settings
Custom parameters are applied based on best practices:
- Shared buffers, work memory, and cache sized appropriately
- Logging configured for DDL statements and slow queries
- Performance optimization settings for autovacuum and query planning

## Accessing the Database

### From Lambda Functions
Use the included database access pattern f