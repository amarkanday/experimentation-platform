# Database Infrastructure Usage Examples

This guide provides practical code examples for working with the experimentation platform's database infrastructure components.

## Table of Contents
- [Aurora PostgreSQL Examples](#aurora-postgresql-examples)
- [DynamoDB Usage Patterns](#dynamodb-usage-patterns)
- [ElastiCache Redis Caching Strategies](#elasticache-redis-caching-strategies)
- [Best Practices](#best-practices)

## Aurora PostgreSQL Examples

### Connection Management

```python
import os
import json
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager

class PostgresClient:
    def __init__(self, environment=None):
        # Get environment from env var if not provided
        self.environment = environment or os.environ.get('ENVIRONMENT', 'dev')
        self.ssm_client = boto3.client('ssm')
        self.secrets_client = boto3.client('secretsmanager')
        self._connection = None
        
    def _get_connection_params(self):
        """Retrieve database connection parameters from SSM and Secrets Manager"""
        # Get the secret ARN from SSM
        secret_arn_param = f'/experimentation/{self.environment}/database/aurora-secret-arn'
        secret_arn_response = self.ssm_client.get_parameter(Name=secret_arn_param)
        secret_arn = secret_arn_response['Parameter']['Value']
        
        # Get credentials from Secrets Manager
        secret_response = self.secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(secret_response['SecretString'])
        
        return {
            'host': secret['host'],
            'port': secret['port'],
            'dbname': secret['dbname'],
            'user': secret['username'],
            'password': secret['password']
        }
    
    def get_connection(self):
        """Get a database connection, creating a new one if needed"""
        if self._connection is None or self._connection.closed:
            params = self._get_connection_params()
            self._connection = psycopg2.connect(
                **params,
                cursor_factory=RealDictCursor
            )
            self._connection.autocommit = False
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close the database connection"""
        if self._connection is not None and not self._connection.closed:
            self._connection.close()
            self._connection = None

# Create a singleton instance for reuse
pg_client = PostgresClient()
```

### Experiment CRUD Operations

```python
import uuid
from datetime import datetime

def create_experiment(name, description, variations, owner=None):
    """Create a new experiment"""
    experiment_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with pg_client.get_cursor() as cursor:
        # Insert experiment
        cursor.execute("""
            INSERT INTO experiments 
            (id, name, description, status, created_at, updated_at, owner)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (experiment_id, name, description, 'draft', now, now, owner))
        experiment = cursor.fetchone()
        
        # Insert variations
        variation_data = []
        for idx, variation in enumerate(variations):
            variation_id = str(uuid.uuid4())
            variation_data.append((
                variation_id,
                experiment_id,
                variation['name'],
                variation.get('description', ''),
                json.dumps(variation.get('value', {})), 
                variation.get('weight', 1),
                now,
                now
            ))
        
        execute_values(cursor, """
            INSERT INTO variations 
            (id, experiment_id, name, description, value, weight, created_at, updated_at)
            VALUES %s
            RETURNING *
        """, variation_data)
        experiment_variations = cursor.fetchall()
    
    # Add variations to the experiment object
    experiment['variations'] = experiment_variations
    return experiment

def get_experiment(experiment_id):
    """Get experiment by ID with its variations"""
    with pg_client.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM experiments WHERE id = %s
        """, (experiment_id,))
        experiment = cursor.fetchone()
        
        if not experiment:
            return None
        
        cursor.execute("""
            SELECT * FROM variations WHERE experiment_id = %s
        """, (experiment_id,))
        variations = cursor.fetchall()
        
        experiment['variations'] = variations
    
    return experiment

def update_experiment_status(experiment_id, status):
    """Update an experiment's status"""
    now = datetime.utcnow().isoformat()
    
    with pg_client.get_cursor() as cursor:
        cursor.execute("""
            UPDATE experiments 
            SET status = %s, updated_at = %s
            WHERE id = %s
            RETURNING *
        """, (status, now, experiment_id))
        return cursor.fetchone()

def list_active_experiments():
    """Get all active experiments"""
    with pg_client.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM experiments WHERE status = 'active'
        """)
        return cursor.fetchall()
```

### Transaction Example

```python
def transfer_experiment_ownership(experiment_id, new_owner):
    """Transfer experiment ownership with transaction support"""
    now = datetime.utcnow().isoformat()
    
    with pg_client.get_cursor() as cursor:
        # Start a transaction block
        cursor.execute("BEGIN")
        
        try:
            # Update experiment ownership
            cursor.execute("""
                UPDATE experiments 
                SET owner = %s, updated_at = %s
                WHERE id = %s
                RETURNING *
            """, (new_owner, now, experiment_id))
            experiment = cursor.fetchone()
            
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            # Log the ownership change
            cursor.execute("""
                INSERT INTO audit_logs 
                (entity_type, entity_id, action, data, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'experiment', 
                experiment_id, 
                'ownership_change',
                json.dumps({'previous_owner': experiment['owner'], 'new_owner': new_owner}),
                now
            ))
            
            # Commit the transaction
            cursor.execute("COMMIT")
            return experiment
            
        except Exception as e:
            # Rollback the transaction on error
            cursor.execute("ROLLBACK")
            raise e
```

## DynamoDB Usage Patterns

### Initialization and Configuration

```python
import os
import boto3
import uuid
import time
from boto3.dynamodb.conditions import Key, Attr

class DynamoDBClient:
    def __init__(self, environment=None):
        self.environment = environment or os.environ.get('ENVIRONMENT', 'dev')
        self.ssm_client = boto3.client('ssm')
        self.dynamodb = boto3.resource('dynamodb')
        self._table_cache = {}
    
    def _get_table_name(self, table_key):
        """Get table name from SSM Parameter Store"""
        if table_key in self._table_cache:
            return self._table_cache[table_key]
        
        param_name = f'/experimentation/{self.environment}/dynamodb/{table_key}-table'
        try:
            response = self.ssm_client.get_parameter(Name=param_name)
            table_name = response['Parameter']['Value']
            self._table_cache[table_key] = table_name
            return table_name
        except Exception as e:
            # Fallback to standard naming convention
            fallback = f"experimentation-{table_key}-{self.environment}"
            print(f"Warning: Using fallback table name {fallback}: {str(e)}")
            return fallback
    
    def get_table(self, table_key):
        """Get a DynamoDB table resource"""
        table_name = self._get_table_name(table_key)
        return self.dynamodb.Table(table_name)

# Create singleton instance
dynamodb_client = DynamoDBClient()
```

### Assignment Operations

```python
def create_assignment(user_id, experiment_id, variation, ttl_days=30):
    """Create a new user assignment to an experiment variation"""
    assignments_table = dynamodb_client.get_table('assignments')
    
    assignment_id = str(uuid.uuid4())
    timestamp = int(time.time())
    ttl = timestamp + (ttl_days * 24 * 60 * 60)  # Convert days to seconds
    
    item = {
        'id': assignment_id,
        'user_id': user_id,
        'experiment_id': experiment_id,
        'variation': variation,
        'assigned_at': timestamp,
        'ttl': ttl
    }
    
    assignments_table.put_item(Item=item)
    return item

def get_user_assignment(user_id, experiment_id):
    """Get a user's assignment for a specific experiment"""
    assignments_table = dynamodb_client.get_table('assignments')
    
    response = assignments_table.query(
        IndexName='user-experiment-index',
        KeyConditionExpression=Key('user_id').eq(user_id) & Key('experiment_id').eq(experiment_id),
        Limit=1
    )
    
    items = response.get('Items', [])
    return items[0] if items else None

def get_experiment_assignments(experiment_id, limit=100, last_key=None):
    """Get assignments for a specific experiment with pagination"""
    assignments_table = dynamodb_client.get_table('assignments')
    
    query_params = {
        'IndexName': 'experiment-index',
        'KeyConditionExpression': Key('experiment_id').eq(experiment_id),
        'Limit': limit,
        'ScanIndexForward': False  # Get most recent first
    }
    
    # Add pagination token if provided
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = assignments_table.query(**query_params)
    
    return {
        'items': response.get('Items', []),
        'last_key': response.get('LastEvaluatedKey')
    }
```

### Event Tracking

```python
def record_event(user_id, event_type, data, experiment_id=None, ttl_days=90):
    """Record a user event"""
    events_table = dynamodb_client.get_table('events')
    
    event_id = str(uuid.uuid4())
    timestamp = int(time.time())
    ttl = timestamp + (ttl_days * 24 * 60 * 60)
    iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp))
    
    item = {
        'id': event_id,
        'timestamp': iso_timestamp,
        'user_id': user_id,
        'event_type': event_type,
        'data': data,
        'ttl': ttl
    }
    
    if experiment_id:
        item['experiment_id'] = experiment_id
    
    events_table.put_item(Item=item)
    return item

def get_user_events(user_id, event_type=None, start_time=None, end_time=None, limit=50):
    """Get events for a specific user with optional filters"""
    events_table = dynamodb_client.get_table('events')
    
    # Base query on user_id
    key_condition = Key('user_id').eq(user_id)
    
    # Add time range if provided
    if start_time and end_time:
        key_condition = key_condition & Key('timestamp').between(start_time, end_time)
    elif start_time:
        key_condition = key_condition & Key('timestamp').gte(start_time)
    elif end_time:
        key_condition = key_condition & Key('timestamp').lte(end_time)
    
    query_params = {
        'IndexName': 'user-event-index',
        'KeyConditionExpression': key_condition,
        'Limit': limit,
        'ScanIndexForward': False  # Most recent first
    }
    
    # Add filter for event_type if provided
    if event_type:
        query_params['FilterExpression'] = Attr('event_type').eq(event_type)
    
    response = events_table.query(**query_params)
    
    return {
        'items': response.get('Items', []),
        'last_key': response.get('LastEvaluatedKey')
    }
```

### Feature Flag Operations

```python
def create_feature_flag(name, description, rules, status='inactive'):
    """Create a new feature flag"""
    feature_flags_table = dynamodb_client.get_table('feature-flags')
    
    flag_id = str(uuid.uuid4())
    timestamp = int(time.time())
    iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp))
    
    item = {
        'id': flag_id,
        'name': name,
        'description': description,
        'rules': rules,
        'status': status,
        'created_at': iso_timestamp,
        'updated_at': iso_timestamp
    }
    
    feature_flags_table.put_item(Item=item)
    return item

def get_active_feature_flags():
    """Get all active feature flags"""
    feature_flags_table = dynamodb_client.get_table('feature-flags')
    
    response = feature_flags_table.query(
        IndexName='status-index',
        KeyConditionExpression=Key('status').eq('active'),
        ScanIndexForward=False  # Most recent first
    )
    
    return response.get('Items', [])

def update_feature_flag_status(flag_id, status):
    """Update a feature flag's status"""
    feature_flags_table = dynamodb_client.get_table('feature-flags')
    
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(int(time.time())))
    
    response = feature_flags_table.update_item(
        Key={'id': flag_id},
        UpdateExpression='SET #status = :status, updated_at = :updated_at',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':updated_at': timestamp
        },
        ReturnValues='ALL_NEW'
    )
    
    return response.get('Attributes', {})
```

## ElastiCache Redis Caching Strategies

### Connection Setup

```python
import os
import boto3
import redis
import json

class RedisClient:
    def __init__(self, environment=None):
        self.environment = environment or os.environ.get('ENVIRONMENT', 'dev')
        self.ssm_client = boto3.client('ssm')
        self._params_cache = {}
        self._client_cache = {
            'primary': None,
            'reader': None
        }
    
    def _get_parameter(self, param_name):
        """Get a parameter from SSM Parameter Store"""
        if param_name in self._params_cache:
            return self._params_cache[param_name]
        
        try:
            response = self.ssm_client.get_parameter(Name=param_name)
            value = response['Parameter']['Value']
            self._params_cache[param_name] = value
            return value
        except Exception as e:
            print(f"Error getting parameter {param_name}: {e}")
            return None
    
    def get_redis_connection(self, use_reader=False):
        """Get a connection to Redis"""
        cache_key = 'reader' if use_reader else 'primary'
        
        # Check for existing connection
        if self._client_cache[cache_key] is not None:
            try:
                # Check if connection is still alive
                self._client_cache[cache_key].ping()
                return self._client_cache[cache_key]
            except (redis.ConnectionError, redis.TimeoutError):
                # Connection is closed or broken, reconnect
                self._client_cache[cache_key] = None
        
        # Get connection parameters
        endpoint_param = f'/experimentation/{self.environment}/redis/endpoint'
        port_param = f'/experimentation/{self.environment}/redis/port'
        
        # If using reader and available, get reader endpoint
        if use_reader:
            reader_endpoint_param = f'/experimentation/{self.environment}/redis/reader-endpoint'
            reader_endpoint = self._get_parameter(reader_endpoint_param)
            if reader_endpoint:
                endpoint_param = reader_endpoint_param
        
        host = self._get_parameter(endpoint_param)
        port = self._get_parameter(port_param)
        
        if not host or not port:
            raise Exception("Redis connection parameters not found")
        
        # Create Redis client
        client = redis.Redis(
            host=host,
            port=int(port),
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            decode_responses=True  # Return strings instead of bytes
        )
        
        # Store in cache
        self._client_cache[cache_key] = client
        
        return client
    
    def close_connections(self):
        """Close all Redis connections"""
        for client_type, client in self._client_cache.items():
            if client is not None:
                try:
                    client.close()
                except Exception as e:
                    print(f"Error closing Redis {client_type} connection: {e}")
                self._client_cache[client_type] = None

# Create singleton instance
redis_client = RedisClient()
```

### Caching Patterns

```python
def cache_experiment_assignment(user_id, experiment_id, variation, ttl=3600):
    """Cache an experiment assignment"""
    client = redis_client.get_redis_connection()
    key = f"assignment:{user_id}:{experiment_id}"
    return client.set(key, variation, ex=ttl)

def get_cached_experiment_assignment(user_id, experiment_id):
    """Get a cached experiment assignment"""
    client = redis_client.get_redis_connection(use_reader=True)
    key = f"assignment:{user_id}:{experiment_id}"
    return client.get(key)

def cache_feature_flag(user_id, feature_id, value, ttl=300):
    """Cache a feature flag value"""
    client = redis_client.get_redis_connection()
    key = f"feature:{feature_id}:user:{user_id}"
    return client.set(key, str(value).lower(), ex=ttl)

def get_cached_feature_flag(user_id, feature_id):
    """Get a cached feature flag value"""
    client = redis_client.get_redis_connection(use_reader=True)
    key = f"feature:{feature_id}:user:{user_id}"
    value = client.get(key)
    
    if value is None:
        return None
    
    return value == "true"

def cache_get(key, fetch_func, ttl=300):
    """
    Generic cache-aside pattern
    
    Args:
        key: Cache key
        fetch_func: Function to fetch data if not in cache
        ttl: Time-to-live in seconds
        
    Returns:
        The cached or freshly fetched data
    """
    client = redis_client.get_redis_connection(use_reader=True)
    
    # Try to get from cache
    cached = client.get(key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            # If not JSON, return as is
            return cached
    
    # Not in cache, fetch data
    data = fetch_func()
    
    # Store in cache if data is not None
    if data is not None:
        write_client = redis_client.get_redis_connection()
        
        if isinstance(data, (dict, list)):
            write_client.set(key, json.dumps(data), ex=ttl)
        else:
            write_client.set(key, data, ex=ttl)
    
    return data

# Example usage
def get_experiment_with_cache(experiment_id):
    """Get experiment with caching"""
    cache_key = f"experiment:{experiment_id}"
    
    return cache_get(
        cache_key,
        lambda: get_experiment(experiment_id),
        ttl=300  # Cache for 5 minutes
    )
```

### Rate Limiting with Redis

```python
def check_rate_limit(key, max_requests, window_seconds):
    """
    Implement rate limiting using Redis
    
    Args:
        key: The rate limit key (e.g., 'rate:ip:123.45.67.89')
        max_requests: Maximum number of requests allowed in the time window
        window_seconds: Time window in seconds
        
    Returns:
        tuple: (allowed (bool), current_count (int), ttl (int))
    """
    client = redis_client.get_redis_connection()
    
    # Get the current count
    count = client.get(key)
    
    if count is None:
        # First request, set to 1 with expiry
        pipe = client.pipeline()
        pipe.set(key, 1, ex=window_seconds)
        pipe.execute()
        return True, 1, window_seconds
    
    count = int(count)
    
    if count >= max_requests:
        # Rate limit exceeded
        ttl = client.ttl(key)
        return False, count, ttl
    
    # Increment the counter
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    result = pipe.execute()
    
    new_count = result[0]
    ttl = result[1]
    
    return True, new_count, ttl

# Example usage in an API endpoint
def api_request_handler(request):
    client_ip = request.get('client_ip', 'unknown')
    rate_limit_key = f"rate:ip:{client_ip}"
    
    # 100 requests per minute
    allowed, count, ttl = check_rate_limit(rate_limit_key, 100, 60)
    
    if not allowed:
        return {
            'statusCode': 429,
            'body': json.dumps({
                'error': 'Rate limit exceeded',
                'retryAfter': ttl
            }),
            'headers': {
                'Retry-After': str(ttl)
            }
        }
    
    # Process the request normally
    # ...
```

## Best Practices

### Connection Management

1. **Use connection pooling**
   - Reuse database connections when possible
   - Always close connections when done
   - Implement proper error handling

2. **Lambda Handler Pattern**

```python
def lambda_handler(event, context):
    try:
        # Process the event
        result = process_event(event)
        return result
    finally:
        # Always clean up resources
        pg_client.close()
        redis_client.close_connections()
```

### Data Access Patterns

1. **Cache frequently accessed data**
   - Use Redis for caching experiment assignments
   - Cache feature flag evaluations to reduce database load
   - Implement appropriate TTLs based on data volatility

2. **Batch operations when possible**

```python
# DynamoDB batch write example
def batch_create_events(events):
    """Create multiple events in a batch operation"""
    events_table = dynamodb_client.get_table('events')
    
    with events_table.batch_writer() as batch:
        for event in events:
            batch.put_item(Item={
                'id': str(uuid.uuid4()),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
                'user_id': event['user_id'],
                'event_type': event['event_type'],
                'data': event['data'],
                'ttl': int(time.time()) + (90 * 24 * 60 * 60)  # 90 days
            })
```

3. **Use transactions for data consistency**

```python
# DynamoDB transaction example
def update_experiment_with_override(experiment_id, status, user_id=None, variation=None):
    """Update experiment status and optionally add a user override"""
    experiments_table = dynamodb_client.get_table('experiments')
    overrides_table = dynamodb_client.get_table('overrides')
    
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    
    transact_items = [
        {
            'Update': {
                'TableName': experiments_table.name,
                'Key': {'id': experiment_id},
                'UpdateExpression': 'SET #status = :status, updated_at = :updated_at',
                'ExpressionAttributeNames': {'#status': 'status'},
                'ExpressionAttributeValues': {
                    ':status': status,
                    ':updated_at': timestamp
                }
            }
        }
    ]
    
    # Add override if user_id and variation provided
    if user_id and variation:
        override_id = str(uuid.uuid4())
        ttl = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
        
        transact_items.append({
            'Put': {
                'TableName': overrides_table.name,
                'Item': {
                    'id': override_id,
                    'user_id': user_id,
                    'target_id': experiment_id,
                    'type': 'experiment',
                    'value': variation,
                    'created_at': timestamp,
                    'ttl': ttl
                }
            }
        })
    
    # Execute transaction
    dynamodb_client.dynamodb.meta.client.transact_write_items(
        TransactItems=transact_items
    )
    
    return {
        'experiment_id': experiment_id,
        'status': status,
        'override_added': bool(user_id and variation)
    }
```

### Performance Optimization

1. **Use appropriate DynamoDB indexes**
   - Design tables with access patterns in mind
   - Create GSIs for common query patterns
   - Use sparse indexes where appropriate

2. **Implement Redis for hot data**
   - Cache experiment assignments and feature flags
   - Use Redis for rate limiting and session data
   - Implement TTLs to prevent cache bloat

3. **Use efficient PostgreSQL queries**
   - Create appropriate indexes
   - Use prepared statements for repeated queries
   - Implement query optimization for complex joins

### Error Handling and Resilience

1. **Implement retries for transient failures**

```python
def with_retry(func, max_retries=3, base_delay=0.1):
    """Execute a function with retries for transient failures"""
    import random
    import time
    
    retries = 0
    while True:
        try:
            return func()
        except (psycopg2.OperationalError, redis.ConnectionError) as e:
            retries += 1
            if retries >= max_retries:
                raise
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** (retries - 1)) * (0.5 + random.random())
            print(f"Retrying after {delay:.2f}s due to {str(e)}")
            time.sleep(delay)
```

2. **Handle database-specific errors**

```python
try:
    # Database operation
except psycopg2.OperationalError:
    # Connection issues, retry
except psycopg2.IntegrityError:
    # Constraint violation, handle gracefully
except redis.ConnectionError:
    # Redis connection issues, use fallback
```

### Security Best Practices

1. **Always use parameterized queries**
   - Prevent SQL injection attacks
   - Use psycopg2 parameter substitution

2. **Implement least privilege access**
   - Only grant necessary permissions to IAM roles
   - Use resource-based policies when possible

3. **Encrypt sensitive data**
   - Use AWS KMS for encryption keys
   - Encrypt sensitive data before storing
