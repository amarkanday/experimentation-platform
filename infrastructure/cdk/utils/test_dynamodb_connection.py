import os
import uuid
import time
import logging
import json
import sys
import boto3
from pathlib import Path
from infrastructure.cdk.utils.dynamodb_access_utils import dynamodb_access


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to make the module importable
current_dir = Path(__file__).parent
parent_dir = str(current_dir.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def test_dynamodb_connection():
    """Test DynamoDB connections using the DynamoDBAccess utility"""

    results = {
        "table_exists": {},
        "basic_operations": {},
        "issues": []
    }

    try:
        # Step 1: Check that we can access table names
        for table_key in ["assignments", "events", "experiments", "feature-flags", "overrides"]:
            try:
                table_name = dynamodb_access._get_table_name(table_key)
                logger.info(f"Retrieved table name for {table_key}: {table_name}")
                results["table_exists"][table_key] = True
            except Exception as e:
                logger.error(f"Failed to get table name for {table_key}: {str(e)}")
                results["table_exists"][table_key] = False
                results["issues"].append(f"Table {table_key} not accessible: {str(e)}")

        # Step 2: Test basic operations if the tables exist
        if results["table_exists"].get("experiments", False):
            try:
                # Generate a unique test experiment name
                test_name = f"test_experiment_{uuid.uuid4().hex[:8]}"

                # Create a test experiment
                experiment = dynamodb_access.create_experiment(
                    name=test_name,
                    description="Test experiment for connection verification",
                    variations=[
                        {"name": "control", "description": "Control variation", "allocation": 50},
                        {"name": "treatment", "description": "Treatment variation", "allocation": 50}
                    ],
                    status="draft"
                )

                logger.info(f"Created test experiment: {experiment['id']}")

                # Retrieve the experiment
                retrieved = dynamodb_access.get_experiment(experiment["id"])
                if retrieved and retrieved["name"] == test_name:
                    logger.info("Successfully retrieved experiment")
                    results["basic_operations"]["experiment_create_retrieve"] = True
                else:
                    logger.error("Failed to retrieve experiment correctly")
                    results["basic_operations"]["experiment_create_retrieve"] = False
                    results["issues"].append("Failed to retrieve experiment correctly")

                # Update the experiment status
                updated = dynamodb_access.update_experiment_status(experiment["id"], "paused")
                if updated and updated.get("status") == "paused":
                    logger.info("Successfully updated experiment status")
                    results["basic_operations"]["experiment_update"] = True
                else:
                    logger.error("Failed to update experiment status")
                    results["basic_operations"]["experiment_update"] = False
                    results["issues"].append("Failed to update experiment status")

                # Get experiments by status
                experiments = dynamodb_access.get_experiments_by_status("paused")
                if any(exp["id"] == experiment["id"] for exp in experiments):
                    logger.info("Successfully queried experiments by status")
                    results["basic_operations"]["experiment_query"] = True
                else:
                    logger.error("Failed to query experiments by status")
                    results["basic_operations"]["experiment_query"] = False
                    results["issues"].append("Failed to query experiments by status")

            except Exception as e:
                logger.error(f"Error during experiment operations: {str(e)}")
                results["basic_operations"]["experiments"] = False
                results["issues"].append(f"Experiment operations failed: {str(e)}")

        # Step 3: Test feature flag operations
        if results["table_exists"].get("feature-flags", False):
            try:
                # Generate a unique test feature flag name
                test_flag_name = f"test_flag_{uuid.uuid4().hex[:8]}"

                # Create a test feature flag
                flag = dynamodb_access.create_feature_flag(
                    name=test_flag_name,
                    description="Test feature flag for connection verification",
                    rules={"enabled": True},
                    status="inactive"
                )

                logger.info(f"Created test feature flag: {flag['id']}")

                # Retrieve the feature flag
                retrieved = dynamodb_access.get_feature_flag(flag["id"])
                if retrieved and retrieved["name"] == test_flag_name:
                    logger.info("Successfully retrieved feature flag")
                    results["basic_operations"]["feature_flag_create_retrieve"] = True
                else:
                    logger.error("Failed to retrieve feature flag correctly")
                    results["basic_operations"]["feature_flag_create_retrieve"] = False
                    results["issues"].append("Failed to retrieve feature flag correctly")

                # Update the feature flag status
                updated = dynamodb_access.update_feature_flag_status(flag["id"], "active")
                if updated and updated.get("status") == "active":
                    logger.info("Successfully updated feature flag status")
                    results["basic_operations"]["feature_flag_update"] = True
                else:
                    logger.error("Failed to update feature flag status")
                    results["basic_operations"]["feature_flag_update"] = False
                    results["issues"].append("Failed to update feature flag status")

                # Get active feature flags
                flags = dynamodb_access.get_active_feature_flags()
                if any(f["id"] == flag["id"] for f in flags):
                    logger.info("Successfully queried active feature flags")
                    results["basic_operations"]["feature_flag_query"] = True
                else:
                    logger.error("Failed to query active feature flags")
                    results["basic_operations"]["feature_flag_query"] = False
                    results["issues"].append("Failed to query active feature flags")

            except Exception as e:
                logger.error(f"Error during feature flag operations: {str(e)}")
                results["basic_operations"]["feature_flags"] = False
                results["issues"].append(f"Feature flag operations failed: {str(e)}")

        # Print summary
        logger.info("DynamoDB Connection Test Summary:")
        logger.info(f"Tables accessible: {sum(results['table_exists'].values())}/{len(results['table_exists'])}")
        if results["basic_operations"]:
            successful = sum(1 for v in results["basic_operations"].values() if v is True)
            total = len(results["basic_operations"])
            logger.info(f"Basic operations successful: {successful}/{total}")

        if results["issues"]:
            logger.warning("Issues found:")
            for issue in results["issues"]:
                logger.warning(f"- {issue}")
        else:
            logger.info("No issues found! All tests passed.")

        return results

    except Exception as e:
        logger.error(f"Unexpected error during DynamoDB connection test: {str(e)}")
        results["issues"].append(f"Unexpected error: {str(e)}")
        return results


if __name__ == "__main__":
    # Check environment
    aws_profile = os.environ.get("AWS_PROFILE")
    aws_region = os.environ.get("AWS_DEFAULT_REGION")
    environment = os.environ.get("ENVIRONMENT", "dev")

    logger.info("Testing DynamoDB connection with:")
    logger.info(f"  AWS_PROFILE: {aws_profile or 'Not set'}")
    logger.info(f"  AWS_DEFAULT_REGION: {aws_region or 'Not set'}")
    logger.info(f"  ENVIRONMENT: {environment}")

    # Run the test
    results = test_dynamodb_connection()

    # Save results to a file
    with open("dynamodb_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Test results saved to dynamodb_test_results.json")
