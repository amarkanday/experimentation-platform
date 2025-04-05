import os
from typing import Dict, Optional
import boto3
import redis
import logging
from redis.exceptions import RedisError, ConnectionError

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Detect environment variables
AWS_PROFILE = os.getenv("AWS_PROFILE", "experimentation-platform")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Default Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  # Inside
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
USE_AWS_ELASTICACHE = os.getenv("USE_AWS_ELASTICACHE", "false").lower() == "true"

# AWS ElastiCache Configuration (if enabled)
if USE_AWS_ELASTICACHE:
    try:
        ssm_client = boto3.client("ssm", region_name=AWS_REGION)
        redis_endpoint_param = f"/experimentation/{ENVIRONMENT}/redis/endpoint"
        response = ssm_client.get_parameter(Name=redis_endpoint_param)
        REDIS_HOST = response["Parameter"].get("Value")
        if not REDIS_HOST:
            raise KeyError(
                f"'Value' key not found in the parameter response: {response}"
            )
        logger.info(f"Using AWS ElastiCache Redis: {REDIS_HOST}")
    except Exception as e:
        logger.error(f"Error fetching AWS ElastiCache endpoint: {e}")
        logger.info("Falling back to default Redis host")


class RedisAccess:
    """
    Utility class for accessing Redis (Local or AWS ElastiCache)
    """

    def __init__(self):
        """
        Initialize the Redis connection.
        """
        self.client = redis.Redis(
            host=REDIS_HOST or "localhost",
            port=REDIS_PORT,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

        self.environment = os.getenv("ENVIRONMENT", "dev")

        # Ensure correct Boto3 client type hinting
        if USE_AWS_ELASTICACHE:
            self.ssm_client = boto3.client("ssm", region_name=AWS_REGION)

        # Default Redis config
        self.default_config = {
            "host": REDIS_HOST or "localhost",
            "port": REDIS_PORT,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
        }

        # Connection caching
        self._params_cache: Dict[str, str] = {}
        self._client_cache: Dict[str, Optional[redis.Redis]] = {
            "primary": None,
            "reader": None,
        }

    def test_connection(self):
        """
        Test Redis connection.
        """
        try:
            if self.client.ping():
                logger.info("✅ Redis connection successful!")
                return True
        except ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    def get(self, key: str):
        try:
            return self.client.get(key)
        except RedisError as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = None):
        try:
            return self.client.set(key, value, ex=ttl)
        except RedisError as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    def close(self):
        try:
            self.client.close()
            logger.info("Closed Redis connection")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Create Redis access instance
redis_access = RedisAccess()

# Test connection
if __name__ == "__main__":
    redis_access.test_connection()
