#!/usr/bin/env python3
import os
import sys
import uuid
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to make the module importable
current_dir = Path(__file__).parent
parent_dir = str(current_dir.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set environment variables for Redis
os.environ["AWS_PROFILE"] = os.environ.get(
    "AWS_PROFILE", "experimentation-platform"
)  # Change "default" if needed
os.environ["AWS_DEFAULT_REGION"] = os.environ.get(
    "AWS_DEFAULT_REGION", "us-west-2"
)  # Change to your region
os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "dev")
os.environ["USE_AWS_ELASTICACHE"] = os.environ.get("USE_AWS_ELASTICACHE", "false")
os.environ["REDIS_HOST"] = os.environ.get("REDIS_HOST", "localhost")
os.environ["REDIS_PORT"] = os.environ.get("REDIS_PORT", "6379")

# Import Redis access utility
try:
    # First try to import from the direct path
    from redis_access_utils import redis_access
    logger.info("Imported redis_access from redis_access_utils")
except ImportError:
    try:
        # Then try to import from the infrastructure path
        from infrastructure.cdk.utils.redis_access_utils import redis_access
        logger.info("Imported redis_access from infrastructure.cdk.utils.redis_access_utils")
    except ImportError:
        try:
            # Fallback to the original path
            from infrastructure.cdk.utils.redis_access_utils import redis_access
            logger.info("Imported redis_access from infrastructure.cdk.utils.redis_access_utils")
        except ImportError:
            logger.error("Could not import redis_access. Please ensure the module is in the path.")
            sys.exit(1)


def test_redis_connection() -> Dict[str, Any]:
    """Test Redis connection and basic operations using the RedisAccess utility"""

    results = {
        "connection": False,
        "basic_operations": {},
        "hash_operations": {},
        "application_helpers": {},
        "performance": {},
        "issues": [],
    }

    # Generate a unique test key prefix to avoid conflicts
    test_prefix = f"test_redis_{uuid.uuid4().hex[:8]}"
    test_keys = []

    try:
        # Step 1: Test basic connection
        logger.info("Testing Redis connection...")
        try:
            # Try to get a connection
            primary_client = redis_access.get_primary_connection()

            # Try a simple ping
            ping_result = primary_client.ping()

            logger.info(f"Redis ping successful: {ping_result}")
            results["connection"] = True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            results["connection"] = False
            results["issues"].append(f"Redis connection failed: {str(e)}")
            # No point continuing if connection failed
            return results

        # Step 2: Test basic key-value operations
        logger.info("Testing basic key-value operations...")
        try:
            # Test SET
            test_key = f"{test_prefix}:basic:string"
            test_keys.append(test_key)
            test_value = f"test_value_{uuid.uuid4().hex[:8]}"

            set_result = redis_access.set(test_key, test_value)
            logger.info(f"SET {test_key} result: {set_result}")

            # Test GET
            get_result = redis_access.get(test_key)
            logger.info(f"GET {test_key} result: {get_result}")

            # Test if GET returns the correct value
            if get_result == test_value:
                logger.info("Basic SET/GET test passed")
                results["basic_operations"]["set_get"] = True
            else:
                logger.error(
                    f"Basic SET/GET test failed: expected '{test_value}', got '{get_result}'"
                )
                results["basic_operations"]["set_get"] = False
                results["issues"].append("Basic SET/GET test failed: value mismatch")

            # Test TTL
            test_key_ttl = f"{test_prefix}:basic:ttl"
            test_keys.append(test_key_ttl)
            ttl_value = 30  # 30 seconds TTL

            redis_access.set(test_key_ttl, "ttl_test", ttl=ttl_value)
            actual_ttl = redis_access.ttl(test_key_ttl)

            # TTL should be approximately the value we set (allow for a little time passage)
            if actual_ttl <= ttl_value and actual_ttl > 0:
                logger.info(
                    f"TTL test passed: TTL set to {ttl_value}, got {actual_ttl}"
                )
                results["basic_operations"]["ttl"] = True
            else:
                logger.error(
                    f"TTL test failed: expected TTL around {ttl_value}, got {actual_ttl}"
                )
                results["basic_operations"]["ttl"] = False
                results["issues"].append(
                    f"TTL test failed: expected ~{ttl_value}, got {actual_ttl}"
                )

            # Test DELETE
            test_key_delete = f"{test_prefix}:basic:delete"
            test_keys.append(test_key_delete)

            redis_access.set(test_key_delete, "delete_me")
            delete_result = redis_access.delete(test_key_delete)
            get_after_delete = redis_access.get(test_key_delete)

            if delete_result and get_after_delete is None:
                logger.info("DELETE test passed")
                results["basic_operations"]["delete"] = True
            else:
                logger.error(
                    f"DELETE test failed: delete_result={delete_result}, get_after_delete={get_after_delete}"
                )
                results["basic_operations"]["delete"] = False
                results["issues"].append("DELETE test failed")

            # Test EXISTS
            test_key_exists = f"{test_prefix}:basic:exists"
            test_keys.append(test_key_exists)

            redis_access.set(test_key_exists, "i_exist")
            exists_result = redis_access.exists(test_key_exists)

            if exists_result:
                logger.info("EXISTS test passed")
                results["basic_operations"]["exists"] = True
            else:
                logger.error("EXISTS test failed")
                results["basic_operations"]["exists"] = False
                results["issues"].append("EXISTS test failed")

        except Exception as e:
            logger.error(f"Error during basic operations test: {str(e)}")
            results["basic_operations"]["error"] = str(e)
            results["issues"].append(f"Basic operations test failed: {str(e)}")

        # Step 3: Test hash operations
        logger.info("Testing hash operations...")
        try:
            # Test HSET
            test_hash_key = f"{test_prefix}:hash"
            test_keys.append(test_hash_key)

            hset_result = redis_access.hset(test_hash_key, "field1", "value1")
            logger.info(f"HSET {test_hash_key} field1 result: {hset_result}")

            # Test HGET
            hget_result = redis_access.hget(test_hash_key, "field1")
            logger.info(f"HGET {test_hash_key} field1 result: {hget_result}")

            # Test if HGET returns the correct value
            if hget_result == "value1":
                logger.info("HSET/HGET test passed")
                results["hash_operations"]["hset_hget"] = True
            else:
                logger.error(
                    f"HSET/HGET test failed: expected 'value1', got '{hget_result}'"
                )
                results["hash_operations"]["hset_hget"] = False
                results["issues"].append("HSET/HGET test failed: value mismatch")

            # Test HMSET (multiple fields)
            mapping = {"field2": "value2", "field3": "value3", "field4": "value4"}

            hmset_result = redis_access.hmset(test_hash_key, mapping)
            logger.info(f"HMSET {test_hash_key} result: {hmset_result}")

            # Test HGETALL
            hgetall_result = redis_access.hgetall(test_hash_key)
            logger.info(f"HGETALL {test_hash_key} result: {hgetall_result}")

            # Check if all fields are in the result
            all_fields_match = all(
                field in hgetall_result and hgetall_result[field] == value
                for field, value in mapping.items()
            )
            # Also check field1 from earlier hset
            field1_match = "field1" in hgetall_result and hgetall_result["field1"] == "value1"
            all_fields_match = all_fields_match and field1_match

            if all_fields_match:
                logger.info("HMSET/HGETALL test passed")
                results["hash_operations"]["hmset_hgetall"] = True
            else:
                logger.error("HMSET/HGETALL test failed: not all fields match")
                results["hash_operations"]["hmset_hgetall"] = False
                results["issues"].append(
                    "HMSET/HGETALL test failed: not all fields match"
                )

        except Exception as e:
            logger.error(f"Error during hash operations test: {str(e)}")
            results["hash_operations"]["error"] = str(e)
            results["issues"].append(f"Hash operations test failed: {str(e)}")

        # Step 4: Test application helpers
        logger.info("Testing application helpers...")
        try:
            # Test feature flag helpers
            test_user_id = f"user_{uuid.uuid4().hex[:8]}"
            test_feature_id = f"feature_{uuid.uuid4().hex[:8]}"

            # Set feature flag
            flag_set_result = redis_access.cache_feature_flag(
                test_user_id, test_feature_id, True
            )
            logger.info(f"Feature flag set result: {flag_set_result}")

            # Get feature flag
            flag_get_result = redis_access.get_cached_feature_flag(
                test_user_id, test_feature_id
            )
            logger.info(f"Feature flag get result: {flag_get_result}")

            if flag_get_result is True:
                logger.info("Feature flag helper test passed")
                results["application_helpers"]["feature_flag"] = True
            else:
                logger.error(
                    f"Feature flag helper test failed: expected True, got {flag_get_result}"
                )
                results["application_helpers"]["feature_flag"] = False
                results["issues"].append("Feature flag helper test failed")

            # Test experiment assignment helpers
            test_experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
            test_variation = "treatment"

            # Set assignment
            assignment_set_result = redis_access.cache_experiment_assignment(
                test_user_id, test_experiment_id, test_variation
            )
            logger.info(f"Experiment assignment set result: {assignment_set_result}")

            # Get assignment
            assignment_get_result = redis_access.get_cached_experiment_assignment(
                test_user_id, test_experiment_id
            )
            logger.info(f"Experiment assignment get result: {assignment_get_result}")

            if assignment_get_result == test_variation:
                logger.info("Experiment assignment helper test passed")
                results["application_helpers"]["experiment_assignment"] = True
            else:
                logger.error(
                    f"Experiment assignment helper test failed: expected '{test_variation}', got '{assignment_get_result}'"
                )
                results["application_helpers"]["experiment_assignment"] = False
                results["issues"].append("Experiment assignment helper test failed")

            # Test counter helper
            test_counter_key = f"{test_prefix}:counter"
            test_keys.append(test_counter_key)

            increment_result = redis_access.increment_counter(test_counter_key)
            logger.info(f"Counter increment result: {increment_result}")

            increment_by_5_result = redis_access.increment_counter(test_counter_key, 5)
            logger.info(f"Counter increment by 5 result: {increment_by_5_result}")

            if increment_result == 1 and increment_by_5_result == 6:
                logger.info("Counter helper test passed")
                results["application_helpers"]["counter"] = True
            else:
                logger.error(
                    f"Counter helper test failed: expected 1 and 6, got {increment_result} and {increment_by_5_result}"
                )
                results["application_helpers"]["counter"] = False
                results["issues"].append("Counter helper test failed")

        except Exception as e:
            logger.error(f"Error during application helpers test: {str(e)}")
            results["application_helpers"]["error"] = str(e)
            results["issues"].append(f"Application helpers test failed: {str(e)}")

        # Step 5: Performance test (optional)
        logger.info("Testing Redis performance...")
        try:
            # Performance test for SET/GET
            batch_size = 100
            perf_key_prefix = f"{test_prefix}:perf"
            perf_keys = [f"{perf_key_prefix}:{i}" for i in range(batch_size)]
            test_keys.extend(perf_keys)

            # Time batch SET
            start_time = time.time()
            for i, key in enumerate(perf_keys):
                redis_access.set(key, f"value_{i}")
            set_duration = time.time() - start_time

            # Time batch GET
            start_time = time.time()
            for key in perf_keys:
                redis_access.get(key)
            get_duration = time.time() - start_time

            # Calculate operations per second
            set_ops_per_sec = batch_size / set_duration
            get_ops_per_sec = batch_size / get_duration

            logger.info(f"SET performance: {set_ops_per_sec:.2f} ops/sec")
            logger.info(f"GET performance: {get_ops_per_sec:.2f} ops/sec")

            results["performance"] = {
                "set_ops_per_sec": set_ops_per_sec,
                "get_ops_per_sec": get_ops_per_sec,
                "batch_size": batch_size,
            }

        except Exception as e:
            logger.error(f"Error during performance test: {str(e)}")
            results["performance"]["error"] = str(e)
            results["issues"].append(f"Performance test failed: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error during Redis tests: {str(e)}")
        results["issues"].append(f"Unexpected error: {str(e)}")
    finally:
        # Clean up test keys
        try:
            if test_keys:
                primary_client = redis_access.get_primary_connection()
                if test_keys:
                    primary_client.delete(*test_keys)
                    logger.info(f"Cleaned up {len(test_keys)} test keys")
        except Exception as e:
            logger.error(f"Error cleaning up test keys: {str(e)}")

        # Close connections
        try:
            redis_access.close_connections()
            logger.info("Closed Redis connections")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {str(e)}")

    # Print summary
    logger.info("Redis Test Summary:")
    if results["connection"]:
        logger.info("✓ Connection: Success")
    else:
        logger.error("✗ Connection: Failed")

    if "basic_operations" in results:
        success_count = sum(
            1 for v in results["basic_operations"].values() if v is True
        )
        total = len(results["basic_operations"])
        if "error" in results["basic_operations"]:
            total -= 1  # Don't count the error entry
        logger.info(f"Basic operations: {success_count}/{total} tests passed")

    if "hash_operations" in results:
        success_count = sum(1 for v in results["hash_operations"].values() if v is True)
        total = len(results["hash_operations"])
        if "error" in results["hash_operations"]:
            total -= 1  # Don't count the error entry
        logger.info(f"Hash operations: {success_count}/{total} tests passed")

    if "application_helpers" in results:
        success_count = sum(
            1 for v in results["application_helpers"].values() if v is True
        )
        total = len(results["application_helpers"])
        if "error" in results["application_helpers"]:
            total -= 1  # Don't count the error entry
        logger.info(f"Application helpers: {success_count}/{total} tests passed")

    if results["issues"]:
        logger.warning("Issues found:")
        for issue in results["issues"]:
            logger.warning(f"- {issue}")
    else:
        logger.info("No issues found! All tests passed.")

    return results


if __name__ == "__main__":
    # Check environment
    aws_profile = os.environ.get("AWS_PROFILE")
    aws_region = os.environ.get("AWS_DEFAULT_REGION")
    environment = os.environ.get("ENVIRONMENT", "dev")
    use_aws = os.environ.get("USE_AWS_ELASTICACHE", "false").lower() == "true"
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = os.environ.get("REDIS_PORT", "6379")

    logger.info("Testing Redis connection with:")
    logger.info(f"  AWS_PROFILE: {aws_profile or 'Not set'}")
    logger.info(f"  AWS_DEFAULT_REGION: {aws_region or 'Not set'}")
    logger.info(f"  ENVIRONMENT: {environment}")
    logger.info(f"  USE_AWS_ELASTICACHE: {use_aws}")
    logger.info(f"  REDIS_HOST: {redis_host}")
    logger.info(f"  REDIS_PORT: {redis_port}")

    # Run the test
    results = test_redis_connection()

    # Save results to a file
    with open("redis_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Test results saved to redis_test_results.json")

    # Exit with error code if issues were found
    if results["issues"]:
        sys.exit(1)
    else:
        sys.exit(0)
