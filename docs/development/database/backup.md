# Database Backup Schedules and Retention Policies

This document outlines the backup schedules and retention policies for all database resources in the experimentation platform infrastructure.

## Overview

The experimentation platform uses three primary database technologies:
- **Aurora PostgreSQL**: For relational data storage
- **DynamoDB**: For NoSQL data storage
- **ElastiCache Redis**: For caching and ephemeral data

Each database resource has its own backup mechanism and retention policy that is configured appropriately based on environment (development, staging, production).

## Aurora PostgreSQL

### Backup Mechanism

Aurora PostgreSQL uses automated backups that include:
1. **Daily Snapshots**: Full database snapshots taken daily during the backup window
2. **Continuous Backup**: Transaction logs are backed up continuously, enabling point-in-time recovery
3. **Manual Snapshots**: In addition to automated backups, manual snapshots are taken before major changes

### Backup Windows

| Environment | Backup Window (UTC) | Maintenance Window (UTC) |
|-------------|---------------------|--------------------------|
| Development | 02:00-03:00         | Sun 04:00-05:00          |
| Staging     | 02:00-03:00         | Sun 04:00-05:00          |
| Production  | 02:00-03:00         | Sun 04:00-05:00          |

### Retention Policy

| Environment | Automated Backup Retention | Point-in-Time Recovery | Manual Snapshot Retention |
|-------------|----------------------------|------------------------|---------------------------|
| Development | 7 days                     | Up to 7 days           | Until manually deleted    |
| Staging     | 7 days                     | Up to 7 days           | Until manually deleted    |
| Production  | 7 days                     | Up to 7 days           | Until manually deleted    |

### Implementation

The retention policy is defined in the Aurora cluster configuration:

```python
self.aurora_cluster = rds.DatabaseCluster(
    # ... other configuration ...
    backup_retention=Duration.days(7),
    preferred_backup_window="02:00-03:00",  # UTC
    preferred_maintenance_window="sun:04:00-sun:05:00",  # UTC
    # ... other configuration ...
)
```

### Disaster Recovery

In case of database failure:
1. Aurora will automatically fail over to a replica in multi-AZ deployments (staging and production)
2. For complete cluster failure, recovery can be performed from the most recent automated backup
3. Point-in-time recovery can be used to restore to any point within the retention period

## DynamoDB Tables

### Backup Mechanism

DynamoDB uses two types of backups:
1. **Point-in-Time Recovery (PITR)**: Continuous backups allowing restoration to any point within the last 35 days
2. **On-Demand Backups**: Manual or scheduled backups retained until explicitly deleted

### Backup Configuration

| Environment | PITR Enabled | Backup Frequency  |
|-------------|--------------|-------------------|
| Development | Yes          | On-demand only    |
| Staging     | Yes          | On-demand only    |
| Production  | Yes          | Daily + On-demand |

### Retention Policy

| Environment | PITR Retention | On-Demand Backup Retention |
|-------------|----------------|----------------------------|
| Development | 35 days        | Until manually deleted     |
| Staging     | 35 days        | Until manually deleted     |
| Production  | 35 days        | 90 days (then archived)    |

### Implementation

Point-in-time recovery is enabled in the table configuration:

```python
table = dynamodb.Table(
    # ... other configuration ...
    point_in_time_recovery=True,
    # ... other configuration ...
)
```

### Disaster Recovery

In case of data loss:
1. For accidental writes/deletes: Use PITR to restore to a point before the incident
2. For table deletion: Restore from the most recent on-demand backup
3. For region-wide issues: Cross-region backups can be restored in another region

## ElastiCache Redis

### Backup Mechanism

ElastiCache Redis uses snapshot-based backups:
1. **Automatic Snapshots**: Taken daily during the configured backup window
2. **Manual Snapshots**: Can be taken at any time

### Backup Windows

| Environment | Backup Window (UTC) | Maintenance Window (UTC) |
|-------------|---------------------|--------------------------|
| Development | 02:00-03:00         | Sun 04:00-05:00          |
| Staging     | 02:00-03:00         | Sun 04:00-05:00          |
| Production  | 02:00-03:00         | Sun 04:00-05:00          |

### Retention Policy

| Environment | Snapshot Retention |
|-------------|-------------------|
| Development | 1 day             |
| Staging     | 3 days            |
| Production  | 7 days            |

### Implementation

The snapshot retention is configured based on environment:

```python
def _get_snapshot_retention_for_env(self, environment: str) -> int:
    """
    Get the appropriate Redis snapshot retention period based on environment.
    """
    if environment == "prod":
        return 7  # 7 days retention in production
    elif environment == "staging":
        return 3  # 3 days retention in staging
    else:  # dev, test, etc.
        return 1  # 1 day retention in dev/test
```

And applied in the Redis cluster configuration:

```python
self.redis_cluster = elasticache.CfnReplicationGroup(
    # ... other configuration ...
    snapshot_retention_limit=self._get_snapshot_retention_for_env(environment),
    snapshot_window="02:00-03:00",  # UTC
    # ... other configuration ...
)
```

### Disaster Recovery

In case of Redis failure:
1. For multi-node deployments (staging and production), automatic failover will occur
2. For complete cluster failure, restore from the most recent snapshot
3. Since Redis is primarily used for caching, some data loss may be acceptable as the data can be rebuilt from primary sources

## Additional Information

### Encryption

All backups are encrypted:
- **Aurora PostgreSQL**: Backups are encrypted using the same KMS key as the database
- **DynamoDB**: Backups are encrypted by default using AWS managed keys
- **ElastiCache Redis**: Snapshots are encrypted if the cluster has encryption at rest enabled

### Monitoring

Backup success/failure is monitored through:
- CloudWatch alarms for failed backup events
- SNS notifications for critical backup failures
- Automated weekly backup verification

### Backup Testing

Regular backup testing is performed following this schedule:
- **Development**: Quarterly
- **Staging**: Monthly
- **Production**: Monthly

### Compliance

The backup and retention policies are designed to meet:
- General data protection requirements
- Disaster recovery best practices
- Industry standard RPO (Recovery Point Objective) and RTO (Recovery Time Objective) guidelines

## Backup Management Responsibilities

| Task                         | Responsible Team    | Frequency         |
|------------------------------|---------------------|-------------------|
| Monitor backup jobs          | DevOps              | Daily             |
| Test recovery procedures     | DevOps, Engineering | Monthly           |
| Review retention policies    | Engineering, DevOps | Quarterly         |
| Update backup documentation  | Engineering         | As needed         |
