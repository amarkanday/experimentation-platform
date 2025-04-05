import os
import json
import time
import uuid
import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Optional, Any, Union, cast, TYPE_CHECKING

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Type hints that only apply during type checking
if TYPE_CHECKING:
    # Import the types only during type checking to avoid runtime dependency
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_dynamodb.service_resource import Table
    from mypy_boto3_ssm.client import SSMClient
else:
    # Use dummy types during runtime
    DynamoDBServiceResource = object
    Table = object
    SSMClient = object


class DynamoDBAccess:
    """
    Utility class for accessing DynamoDB tables in the experimentation platform.

    Provides methods for working with:
    - Assignments
    - Events
    - Experiments
    - Feature Flags
    - Overrides
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize the DynamoDB access utility.

        Args:
            environment: The deployment environment (dev, staging, prod)
                         If not provided, will be read from ENVIRONMENT env var
        """
        self.environment = environment or os.environ.get("ENVIRONMENT", "dev")
        # Type annotation with cast helps type checker understand the correct type
        self.dynamodb = cast('DynamoDBServiceResource', boto3.resource("dynamodb"))
        self.ssm_client = cast('SSMClient', boto3.client("ssm"))

        # Cache for table names (to avoid repeated SSM calls)
        self._table_cache: Dict[str, str] = {}

    def _get_table_name(self, table_key: str) -> str:
        """
        Get a table name from SSM Parameter Store or cache.

        Args:
            table_key: The table key (assignments, events, etc.)

        Returns:
            The table name
        """
        if table_key in self._table_cache:
            return self._table_cache[table_key]

        param_name = f"/experimentation/{self.environment}/dynamodb/{table_key}-table"
        try:
            response = self.ssm_client.get_parameter(Name=param_name)

            # Safely access nested dictionary keys
            if response and isinstance(response, dict) and "Parameter" in response:
                parameter = response["Parameter"]
                if isinstance(parameter, dict) and "Value" in parameter:
                    table_name = parameter["Value"]
                    self._table_cache[table_key] = table_name
                    return table_name

            # If we reach here, the expected keys weren't found
            logger.warning(f"Parameter {param_name} value not found, using fallback")
            fallback = f"experimentation-{table_key}-{self.environment}"
            self._table_cache[table_key] = fallback
            return fallback

        except Exception as e:
            logger.error(f"Error getting table name for {table_key}: {e}")
            # Fall back to a standard naming convention if SSM param not found
            fallback = f"experimentation-{table_key}-{self.environment}"
            self._table_cache[table_key] = fallback
            return fallback

    def _get_table(self, table_key: str) -> 'Table':
        """Get a DynamoDB table resource"""
        table_name = self._get_table_name(table_key)
        # Use cast to help type checker understand the return type
        return cast('Table', self.dynamodb.Table(table_name))

    # ======= ASSIGNMENTS TABLE METHODS =======

    def create_assignment(
        self, user_id: str, experiment_id: str, variation: str, ttl_days: int = 30
    ) -> Dict[str, Any]:
        """
        Create a new assignment for a user in an experiment.

        Args:
            user_id: The user ID
            experiment_id: The experiment ID
            variation: The assigned variation ID
            ttl_days: Time-to-live in days for this assignment

        Returns:
            The created assignment
        """
        if user_id is None or experiment_id is None or variation is None:
            raise ValueError("user_id, experiment_id, and variation cannot be None")

        table = self._get_table("assignments")
        assignment_id = str(uuid.uuid4())
        timestamp = int(time.time())
        ttl = timestamp + (ttl_days * 24 * 60 * 60)  # Convert days to seconds

        item = {
            "id": assignment_id,
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variation": variation,
            "assigned_at": timestamp,
            "ttl": ttl,
        }

        table.put_item(Item=item)
        return item

    def get_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an assignment by ID.

        Args:
            assignment_id: The assignment ID

        Returns:
            The assignment or None if not found
        """
        if assignment_id is None:
            raise ValueError("assignment_id cannot be None")

        table = self._get_table("assignments")
        response = table.get_item(Key={"id": assignment_id})
        return response.get("Item")

    def get_user_assignment(
        self, user_id: str, experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's assignment for a specific experiment.

        Args:
            user_id: The user ID
            experiment_id: The experiment ID

        Returns:
            The assignment or None if not found
        """
        if user_id is None or experiment_id is None:
            raise ValueError("user_id and experiment_id cannot be None")

        table = self._get_table("assignments")
        response = table.query(
            IndexName="user-experiment-index",
            KeyConditionExpression=Key("user_id").eq(user_id)
            & Key("experiment_id").eq(experiment_id),
            Limit=1,
        )

        items = response.get("Items", [])
        return items[0] if items else None

    def get_user_assignments(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all assignments for a specific user.

        Args:
            user_id: The user ID

        Returns:
            List of assignments for the user
        """
        if user_id is None:
            raise ValueError("user_id cannot be None")

        table = self._get_table("assignments")
        response = table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    def get_experiment_assignments(
        self, experiment_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get assignments for a specific experiment.

        Args:
            experiment_id: The experiment ID
            limit: Maximum number of items to return

        Returns:
            List of assignments for the experiment
        """
        if experiment_id is None:
            raise ValueError("experiment_id cannot be None")

        table = self._get_table("assignments")
        response = table.query(
            IndexName="experiment-index",
            KeyConditionExpression=Key("experiment_id").eq(experiment_id),
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    # ======= EVENTS TABLE METHODS =======

    def create_event(
        self,
        user_id: str,
        event_type: str,
        data: Dict[str, Any],
        experiment_id: Optional[str] = None,
        ttl_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Create a new event.

        Args:
            user_id: The user ID
            event_type: The type of event
            data: The event data
            experiment_id: Optional experiment ID
            ttl_days: Time-to-live in days for this event

        Returns:
            The created event
        """
        if user_id is None or event_type is None:
            raise ValueError("user_id and event_type cannot be None")

        if data is None:
            data = {}

        table = self._get_table("events")
        event_id = str(uuid.uuid4())
        timestamp = int(time.time())
        ttl = timestamp + (ttl_days * 24 * 60 * 60)  # Convert days to seconds
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp))

        item = {
            "id": event_id,
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": timestamp_str,
            "timestamp_epoch": timestamp,
            "data": data,
            "ttl": ttl,
        }

        if experiment_id is not None:
            item["experiment_id"] = experiment_id

        table.put_item(Item=item)
        return item

    def get_event(self, event_id: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Get an event by ID and timestamp.

        Args:
            event_id: The event ID
            timestamp: The event timestamp (ISO format)

        Returns:
            The event or None if not found
        """
        if event_id is None or timestamp is None:
            raise ValueError("event_id and timestamp cannot be None")

        table = self._get_table("events")
        response = table.get_item(Key={"id": event_id, "timestamp": timestamp})
        return response.get("Item")

    def get_user_events(
        self,
        user_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific user.

        Args:
            user_id: The user ID
            start_time: Optional start time filter (ISO format)
            end_time: Optional end time filter (ISO format)
            limit: Maximum number of items to return

        Returns:
            List of events for the user
        """
        if user_id is None:
            raise ValueError("user_id cannot be None")

        table = self._get_table("events")
        key_condition = Key("user_id").eq(user_id)

        if start_time is not None and end_time is not None:
            key_condition = key_condition & Key("timestamp").between(
                start_time, end_time
            )
        elif start_time is not None:
            key_condition = key_condition & Key("timestamp").gte(start_time)
        elif end_time is not None:
            key_condition = key_condition & Key("timestamp").lte(end_time)

        response = table.query(
            IndexName="user-event-index",
            KeyConditionExpression=key_condition,
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    def get_experiment_events(
        self,
        experiment_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific experiment.

        Args:
            experiment_id: The experiment ID
            start_time: Optional start time filter (ISO format)
            end_time: Optional end time filter (ISO format)
            limit: Maximum number of items to return

        Returns:
            List of events for the experiment
        """
        if experiment_id is None:
            raise ValueError("experiment_id cannot be None")

        table = self._get_table("events")
        key_condition = Key("experiment_id").eq(experiment_id)

        if start_time is not None and end_time is not None:
            key_condition = key_condition & Key("timestamp").between(
                start_time, end_time
            )
        elif start_time is not None:
            key_condition = key_condition & Key("timestamp").gte(start_time)
        elif end_time is not None:
            key_condition = key_condition & Key("timestamp").lte(end_time)

        response = table.query(
            IndexName="experiment-event-index",
            KeyConditionExpression=key_condition,
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    # ======= EXPERIMENTS TABLE METHODS =======

    def create_experiment(
        self,
        name: str,
        description: str,
        variations: List[Dict[str, Any]],
        owner: Optional[str] = None,
        status: str = "draft",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new experiment.

        Args:
            name: The experiment name
            description: The experiment description
            variations: List of experiment variations
            owner: The owner of the experiment
            status: The experiment status (draft, running, paused, completed)
            tags: List of tags for the experiment

        Returns:
            The created experiment
        """
        if name is None or description is None:
            raise ValueError("name and description cannot be None")

        if variations is None:
            raise ValueError("variations cannot be None")

        table = self._get_table("experiments")
        experiment_id = str(uuid.uuid4())
        timestamp = int(time.time())
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp))

        item = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "variations": variations,
            "status": status,
            "created_at": timestamp_str,
            "updated_at": timestamp_str,
        }

        if owner is not None:
            item["owner"] = owner

        if tags is not None:
            item["tags"] = tags
            # Add a tag attribute for each tag for GSI querying
            for tag in tags:
                if tag is not None:
                    item["tag"] = tag  # Last tag wins for GSI

        table.put_item(Item=item)
        return item

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an experiment by ID.

        Args:
            experiment_id: The experiment ID

        Returns:
            The experiment or None if not found
        """
        if experiment_id is None:
            raise ValueError("experiment_id cannot be None")

        table = self._get_table("experiments")
        response = table.get_item(Key={"id": experiment_id})
        return response.get("Item")

    def update_experiment_status(
        self, experiment_id: str, status: str
    ) -> Dict[str, Any]:
        """
        Update an experiment's status.

        Args:
            experiment_id: The experiment ID
            status: The new status

        Returns:
            The updated experiment
        """
        if experiment_id is None or status is None:
            raise ValueError("experiment_id and status cannot be None")

        table = self._get_table("experiments")
        timestamp = time.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(int(time.time()))
        )

        response = table.update_item(
            Key={"id": experiment_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status, ":updated_at": timestamp},
            ReturnValues="ALL_NEW",
        )

        return response.get("Attributes", {})

    def get_experiments_by_status(
        self, status: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get experiments by status.

        Args:
            status: The status to filter by
            limit: Maximum number of items to return

        Returns:
            List of experiments with the specified status
        """
        if status is None:
            raise ValueError("status cannot be None")

        table = self._get_table("experiments")
        response = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq(status),
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    def get_experiments_by_owner(
        self, owner: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get experiments by owner.

        Args:
            owner: The owner to filter by
            limit: Maximum number of items to return

        Returns:
            List of experiments with the specified owner
        """
        if owner is None:
            raise ValueError("owner cannot be None")

        table = self._get_table("experiments")
        response = table.query(
            IndexName="owner-index",
            KeyConditionExpression=Key("owner").eq(owner),
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    # ======= FEATURE FLAGS TABLE METHODS =======

    def create_feature_flag(
        self,
        name: str,
        description: str,
        rules: Dict[str, Any],
        status: str = "inactive",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new feature flag.

        Args:
            name: The feature flag name
            description: The feature flag description
            rules: The rules for the feature flag
            status: The feature flag status (active, inactive)
            tags: List of tags for the feature flag

        Returns:
            The created feature flag
        """
        if name is None or description is None or rules is None:
            raise ValueError("name, description, and rules cannot be None")

        table = self._get_table("feature-flags")
        flag_id = str(uuid.uuid4())
        timestamp = int(time.time())
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp))

        item = {
            "id": flag_id,
            "name": name,
            "description": description,
            "rules": rules,
            "status": status,
            "created_at": timestamp_str,
            "updated_at": timestamp_str,
        }

        if tags is not None:
            item["tags"] = tags
            # Add a tag attribute for each tag for GSI querying
            for tag in tags:
                if tag is not None:
                    item["tag"] = tag  # Last tag wins for GSI

        table.put_item(Item=item)
        return item

    def get_feature_flag(self, flag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a feature flag by ID.

        Args:
            flag_id: The feature flag ID

        Returns:
            The feature flag or None if not found
        """
        if flag_id is None:
            raise ValueError("flag_id cannot be None")

        table = self._get_table("feature-flags")
        response = table.get_item(Key={"id": flag_id})
        return response.get("Item")

    def update_feature_flag_status(self, flag_id: str, status: str) -> Dict[str, Any]:
        """
        Update a feature flag's status.

        Args:
            flag_id: The feature flag ID
            status: The new status

        Returns:
            The updated feature flag
        """
        if flag_id is None or status is None:
            raise ValueError("flag_id and status cannot be None")

        table = self._get_table("feature-flags")
        timestamp = time.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(int(time.time()))
        )

        response = table.update_item(
            Key={"id": flag_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status, ":updated_at": timestamp},
            ReturnValues="ALL_NEW",
        )

        return response.get("Attributes", {})

    def get_active_feature_flags(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active feature flags.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of active feature flags
        """
        table = self._get_table("feature-flags")
        response = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq("active"),
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    # ======= OVERRIDES TABLE METHODS =======

    def create_override(
        self, user_id: str, target_id: str, override_type: str, value: Any, ttl_days: int = 30
    ) -> Dict[str, Any]:
        """
        Create a new override for a user.

        Args:
            user_id: The user ID
            target_id: The experiment or feature flag ID being overridden
            override_type: The type of override (experiment, feature)
            value: The override value
            ttl_days: Time-to-live in days for this override

        Returns:
            The created override
        """
        if user_id is None or target_id is None or override_type is None:
            raise ValueError("user_id, target_id, and override_type cannot be None")

        table = self._get_table("overrides")
        override_id = str(uuid.uuid4())
        timestamp = int(time.time())
        ttl = timestamp + (ttl_days * 24 * 60 * 60)  # Convert days to seconds
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp))

        item = {
            "id": override_id,
            "user_id": user_id,
            "target_id": target_id,
            "type": override_type,
            "value": value,
            "created_at": timestamp_str,
            "ttl": ttl,
        }

        table.put_item(Item=item)
        return item

    def get_override(self, override_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an override by ID.

        Args:
            override_id: The override ID

        Returns:
            The override or None if not found
        """
        if override_id is None:
            raise ValueError("override_id cannot be None")

        table = self._get_table("overrides")
        response = table.get_item(Key={"id": override_id})
        return response.get("Item")

    def get_user_overrides(
        self, user_id: str, override_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get overrides for a specific user.

        Args:
            user_id: The user ID
            override_type: Optional type filter (experiment, feature)

        Returns:
            List of overrides for the user
        """
        if user_id is None:
            raise ValueError("user_id cannot be None")

        table = self._get_table("overrides")
        response = table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,  # Most recent first
        )

        items = response.get("Items", [])

        # Filter by type if specified
        if override_type is not None and items:
            items = [item for item in items if item.get("type") == override_type]

        return items

    def get_target_overrides(
        self, target_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get overrides for a specific target (experiment or feature flag).

        Args:
            target_id: The target ID
            limit: Maximum number of items to return

        Returns:
            List of overrides for the target
        """
        if target_id is None:
            raise ValueError("target_id cannot be None")

        table = self._get_table("overrides")
        response = table.query(
            IndexName="target-index",
            KeyConditionExpression=Key("target_id").eq(target_id),
            Limit=limit,
            ScanIndexForward=False,  # Most recent first
        )

        return response.get("Items", [])

    def delete_override(self, override_id: str) -> bool:
        """
        Delete an override.

        Args:
            override_id: The override ID

        Returns:
            True if successful, False otherwise
        """
        if override_id is None:
            raise ValueError("override_id cannot be None")

        try:
            table = self._get_table("overrides")
            table.delete_item(Key={"id": override_id})
            return True
        except Exception as e:
            logger.error(f"Error deleting override {override_id}: {e}")
            return False


# Create a singleton instance
dynamodb_access = DynamoDBAccess()
