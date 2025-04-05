import os
import boto3
import redis
import logging
import asyncio
from typing import Any, Dict, Optional, Union
from redis.exceptions import RedisError

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Detect environment variables
AWS_PROFILE = os.getenv("AWS_PROFILE", "experimentation-platform")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Default Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "experimentation-redis")  # Inside Docker
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
USE_AWS_ELASTICACHE = os.getenv("USE_AWS_ELASTICACHE", "false").lower() == "true"

# AWS ElastiCache Configuration (if enabled)
if USE_AWS_ELASTICACHE:
    try:
        ssm_client = boto3.client("ssm", region_name=AWS_REGION)
        redis_endpoint_param = f"/experimentation/{ENVIRONMENT}/redis/endpoint"
        response = ssm_client.get_parameter(Name=redis_endpoint_param)
        REDIS_HOST = response["Parameter"].get("Value", None)
        logger.info(f"Using AWS ElastiCache Redis: {REDIS_HOST}")
    except Exception as e:
        logger.error(f"Error fetching AWS ElastiCache endpoint: {e}")
        logger.info("Falling back to default Redis host")


class RedisAccess:
    """
    Utility class for accessing ElastiCache Redis.
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize the Redis access utility.

        Args:
            environment: Deployment environment (dev, staging, prod).
        """
        self.environment = environment or os.environ.get("ENVIRONMENT", "dev")

        # Ensure correct Boto3 client type hinting
        self.ssm_client: Any = boto3.client("ssm")  # Corrected SSM Client typing

        # Default Redis config
        self.default_config = {
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "decode_responses": True,
        }

        # Connection caching
        self._params_cache: Dict[str, str] = {}
        self._client_cache: Dict[str, Optional[redis.Redis]] = {
            "primary": None,
            "reader": None,
        }

    def _get_parameter(self, param_name: str) -> Optional[str]:
        """
        Get a parameter from AWS SSM Parameter Store.

        Args:
            param_name: The parameter name.

        Returns:
            The parameter value or None if not found.
        """
        if param_name in self._params_cache:
            return self._params_cache[param_name]

        try:
            response = self.ssm_client.get_parameter(Name=param_name)
            parameter = response.get("Parameter", {})
            value = parameter.get("Value", None)  # Ensure safe access to 'Value'

            if value:
                self._params_cache[param_name] = value
            return value

        except Exception as e:
            logger.error(f"Error getting parameter {param_name}: {e}")
            return None

    async def _async_get_parameter(self, param_name: str) -> Optional[str]:
        """
        Async version of `_get_parameter`.

        Args:
            param_name: The parameter name.

        Returns:
            An awaitable string or None if not found.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._get_parameter, param_name
        )  # Corrected for async handling

    def get_redis_connection(self, use_reader: bool = False) -> redis.Redis:
        """
        Get a Redis connection.

        Args:
            use_reader: Whether to use the reader endpoint.

        Returns:
            A Redis connection.
        """
        cache_key = "reader" if use_reader else "primary"

        # Check for cached client first
        client = self._client_cache.get(cache_key)
        if client:
            try:
                client.ping()
                return client
            except (redis.ConnectionError, redis.TimeoutError):
                logger.info("Cached Redis connection is no longer valid. Reconnecting...")
                self._client_cache[cache_key] = None  # Clear broken connection

        # Check if we should use AWS ElastiCache or local Redis
        if USE_AWS_ELASTICACHE:
            # Get connection parameters from SSM
            try:
                endpoint_param = f"/experimentation/{self.environment}/redis/endpoint"
                port_param = f"/experimentation/{self.environment}/redis/port"

                if use_reader:
                    reader_endpoint_param = (
                        f"/experimentation/{self.environment}/redis/reader-endpoint"
                    )
                    reader_endpoint = self._get_parameter(reader_endpoint_param)
                    if reader_endpoint:
                        endpoint_param = reader_endpoint_param

                host = self._get_parameter(endpoint_param)
                port = self._get_parameter(port_param)

                if not host or not port:
                    logger.warning("AWS ElastiCache parameters not found. Falling back to local Redis.")
                    host = REDIS_HOST
                    port = REDIS_PORT
            except Exception as e:
                logger.error(f"Error getting AWS ElastiCache parameters: {e}")
                logger.info("Falling back to local Redis configuration")
                host = REDIS_HOST
                port = REDIS_PORT
        else:
            # Use local Redis configuration from environment variables
            host = REDIS_HOST
            port = REDIS_PORT
            logger.debug(f"Using local Redis at {host}:{port}")

        # Create and cache Redis client
        try:
            if not host:
                raise ValueError("Redis host cannot be None")
            client = redis.Redis(
                host=host,
                port=int(port),
                **self.default_config
            )

            # Test the connection
            client.ping()

            # Cache the working connection
            self._client_cache[cache_key] = client
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {host}:{port}: {e}")
            raise RedisError(f"Unable to establish Redis connection: {e}")

        return client

    def get_reader_connection(self) -> redis.Redis:
        """
        Get a connection to the Redis reader endpoint.

        Returns:
            A Redis connection optimized for read operations.
        """
        return self.get_redis_connection(use_reader=True)

    def get_primary_connection(self) -> redis.Redis:
        """
        Get a connection to the Redis primary endpoint.

        Returns:
            A Redis connection for write operations.
        """
        return self.get_redis_connection(use_reader=False)

    def get(self, key: str) -> Any:
        """
        Get a value from Redis.

        Args:
            key: The key to get

        Returns:
            The value or None if not found
        """
        client = self.get_reader_connection()
        return client.get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a value in Redis.

        Args:
            key: The key to set
            value: The value to set
            ttl: Optional TTL in seconds
            nx: Only set if key does not exist
            xx: Only set if key already exists

        Returns:
            True if successful, False otherwise
        """
        client = self.get_primary_connection()
        return bool(client.set(key, value, ex=ttl, nx=nx, xx=xx))

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: The key to delete

        Returns:
            True if deleted, False if key not found
        """
        client = self.get_primary_connection()
        result = client.delete(key)
        return bool(result) > 0

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        client = self.get_reader_connection()
        return bool(client.exists(key))

    def ttl(self, key: str) -> int:
        """
        Get the TTL of a key.

        Args:
            key: The key to check

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key does not exist
        """
        client = self.get_reader_connection()
        result = client.ttl(key)

        # Handle async result if needed
        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)

        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)

        if not isinstance(result, int):
            raise TypeError(f"Expected an integer result, got {type(result).__name__}")

        return result  # Ensure the result is returned as an integer

    def expire(self, key: str, ttl: int) -> bool:
        """
        Set the TTL of a key.

        Args:
            key: The key to set TTL for
            ttl: TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        client = self.get_primary_connection()
        result = client.expire(key, ttl)

        # Handle async result if needed
        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)

        return bool(result)

    # HASH OPERATIONS

    def hget(self, key: str, field: str) -> Any:
        """
        Get a field from a hash.

        Args:
            key: The hash key
            field: The field to get

        Returns:
            The field value or None if not found
        """
        client = self.get_reader_connection()
        result = client.hget(key, field)

        # Handle async result if needed
        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)

        return result

    def hset(self, key: str, field: str, value: Any) -> bool:
        """
        Set a field in a hash.

        Args:
            key: The hash key
            field: The field to set
            value: The value to set

        Returns:
            True if field was new, False if field was updated

        Raises:
            RedisError: If the Redis operation fails
        """
        try:
            client = self.get_primary_connection()
            result = client.hset(key, field, value)

            # Handle async result if needed
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)

            # Convert result to int then bool, with proper type checking
            if isinstance(result, (int, str)):
                return bool(int(result))
            return False

        except (RedisError, ValueError, TypeError) as e:
            logger.error(f"Error in hset for key={key}, field={field}: {str(e)}")
            raise RedisError(f"Failed to set hash field: {str(e)}")

    def hmset(self, key: str, mapping: Dict[str, Any]) -> bool:
        """
        Set multiple fields in a hash.

        Args:
            key: The hash key
            mapping: Dict of field/value pairs

        Returns:
            True if at least one field was added or updated

        Raises:
            RedisError: If the Redis operation fails
            ValueError: If mapping is empty or invalid
        """
        try:
            if not mapping:
                raise ValueError("Mapping dictionary cannot be empty")

            client = self.get_primary_connection()
            result = client.hset(key, mapping=mapping)

            # Handle async result if needed
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)

            # Convert result to int and check if any fields were set
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)

            if isinstance(result, int):
                return result > 0
            elif isinstance(result, str) and result.isdigit():
                return int(result) > 0
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")

        except (RedisError, ValueError, TypeError) as e:
            logger.error(f"Error in hmset for key={key}: {str(e)}")
            raise RedisError(f"Failed to set hash fields: {str(e)}")

    def hgetall(self, key: str) -> Dict[str, Any]:
        """
        Get all fields from a hash.

        Args:
            key: The hash key

        Returns:
            Dict of field/value pairs. Empty dict if key doesn't exist.

        Raises:
            RedisError: If the Redis operation fails
        """
        try:
            client = self.get_reader_connection()
            result = client.hgetall(key)

            # Handle async result if needed
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)

            # Ensure we always return a dictionary
            if result is None:
                return {}

            # Redis-py already returns a dictionary, but let's ensure type safety
            if not isinstance(result, dict):
                logger.warning(f"Unexpected result type for key {key}: {type(result)}")
                return {}

            return result

        except RedisError as e:
            logger.error(f"Error in hgetall for key={key}: {str(e)}")
            raise RedisError(f"Failed to get hash fields: {str(e)}")

    # APPLICATION SPECIFIC HELPERS

    def cache_get(
        self,
        key: str,
        fetch_func,
        ttl: int = 300,
        use_hash: bool = False,
    ) -> Any:
        """
        Get a value from cache or fetch it if not found.

        Args:
            key: The cache key
            fetch_func: Function to fetch the value if not in cache
            ttl: TTL in seconds
            use_hash: Whether to use a hash for the cache

        Returns:
            The cached or fetched value
        """

        # Check if in cache
        if use_hash:
            result = self.hgetall(key)
            if result:
                return result
        else:
            result = self.get(key)
            if result:
                return result

        # Not in cache, fetch
        result = fetch_func()

        # Store in cache
        if result:
            if use_hash and isinstance(result, dict):
                self.hmset(key, result)
                self.expire(key, ttl)
            else:
                self.set(key, result, ttl=ttl)

        return result

    def cache_feature_flag(
        self, user_id: str, feature_id: str, value: bool, ttl: int = 300
    ) -> bool:
        """
        Cache a feature flag value.

        Args:
            user_id: The user ID
            feature_id: The feature ID
            value: The feature flag value
            ttl: TTL in seconds

        Returns:
            True if successful
        """
        key = f"feature:{feature_id}:user:{user_id}"
        return self.set(key, str(value).lower(), ttl=ttl)

    def get_cached_feature_flag(self, user_id: str, feature_id: str) -> Optional[bool]:
        """
        Get a cached feature flag value.

        Args:
            user_id: The user ID
            feature_id: The feature ID

        Returns:
            The feature flag value or None if not found
        """
        key = f"feature:{feature_id}:user:{user_id}"
        value = self.get(key)

        if value is None:
            return None

        return value == "true"

    def cache_experiment_assignment(
        self, user_id: str, experiment_id: str, variation: str, ttl: int = 3600
    ) -> bool:
        """
        Cache an experiment assignment.

        Args:
            user_id: The user ID
            experiment_id: The experiment ID
            variation: The assigned variation
            ttl: TTL in seconds

        Returns:
            True if successful
        """
        key = f"assignment:{user_id}:{experiment_id}"
        return self.set(key, variation, ttl=ttl)

    def get_cached_experiment_assignment(
        self, user_id: str, experiment_id: str
    ) -> Optional[str]:
        """
        Get a cached experiment assignment.

        Args:
            user_id: The user ID
            experiment_id: The experiment ID

        Returns:
            The assigned variation or None if not found
        """
        key = f"assignment:{user_id}:{experiment_id}"
        return self.get(key)

    def increment_counter(self, key: str, amount: int = 1, ttl: int = 0) -> int:
        """
        Increment a counter in Redis.

        Args:
            key: The counter key
            amount: The amount to increment (default: 1)
            ttl: Optional TTL in seconds (default: 0)

        Returns:
            int: The new counter value

        Raises:
            RedisError: If the Redis operation fails
            ValueError: If amount is not a valid integer
        """
        if not isinstance(amount, int):
            raise ValueError("Amount must be an integer")

        if not isinstance(ttl, int) or ttl < 0:
            raise ValueError("TTL must be a non-negative integer")

        try:
            pipeline = self.get_primary_connection().pipeline()

            # Add increment operation to pipeline
            increment_result = pipeline.incrby(key, amount)

            # Add TTL operation to pipeline if specified
            if ttl > 0:
                pipeline.expire(key, ttl)

            # Execute pipeline
            results = pipeline.execute()

            # First result is from INCRBY
            value = int(results[0])

            # Check if TTL was set successfully
            if ttl > 0 and not results[1]:
                logger.warning(f"Failed to set TTL for key: {key}")

            return value

        except (RedisError, ValueError) as e:
            logger.error(f"Error incrementing counter {key} by {amount}: {str(e)}")
            raise RedisError(f"Failed to increment counter: {str(e)}")

    def close_connections(self):
        """
        Close all Redis connections.
        """
        for client_type, client in self._client_cache.items():
            if client is not None:
                try:
                    client.close()
                except Exception as e:
                    logger.error(f"Error closing Redis {client_type} connection: {e}")
                self._client_cache[client_type] = None


# Create a singleton instance
redis_access = RedisAccess()
