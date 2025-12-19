"""
Assignment Service for experiment variant assignments.

Provides core logic for assigning users to experiment variants using consistent hashing.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from consistent_hash import get_hasher
from models import ExperimentConfig, ExperimentStatus, Assignment
from utils import get_dynamodb_resource, get_logger, get_env_variable

logger = get_logger(__name__)


class AssignmentService:
    """
    Service for managing experiment variant assignments.

    Uses consistent hashing to ensure deterministic, stable assignments.
    """

    def __init__(self):
        """Initialize the assignment service."""
        self.hasher = get_hasher()
        self.experiments_table_name = get_env_variable(
            'EXPERIMENTS_TABLE',
            default='experimently-experiments'
        )

        # Cache for experiment configurations (Lambda warm-start optimization)
        self._experiment_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes in seconds

        # Cache hit rate tracking
        self._cache_hits = 0
        self._cache_misses = 0

    def evaluate_targeting_rules(
        self,
        targeting_rules: Optional[list],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Evaluate targeting rules against user context.

        Args:
            targeting_rules: List of targeting rule dictionaries
            context: User context attributes

        Returns:
            True if user matches all rules (AND logic), False otherwise
        """
        # No rules means all users qualify
        if not targeting_rules:
            return True

        # No context means user doesn't match
        if not context:
            return False

        # Evaluate each rule (AND logic - all must match)
        for rule in targeting_rules:
            attribute = rule.get('attribute')
            operator = rule.get('operator')
            value = rule.get('value')

            # Get user's attribute value from context
            user_value = context.get(attribute)

            # Missing attribute means no match
            if user_value is None:
                return False

            # Evaluate based on operator
            if operator == 'equals':
                if user_value != value:
                    return False
            elif operator == 'in':
                if user_value not in value:
                    return False
            elif operator == 'greater_than':
                if user_value <= value:
                    return False
            elif operator == 'less_than':
                if user_value >= value:
                    return False
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False

        # All rules matched
        return True

    def assign_variant(
        self,
        user_id: str,
        experiment_config: ExperimentConfig,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Assign a user to a variant using consistent hashing.

        Args:
            user_id: Unique user identifier
            experiment_config: Experiment configuration
            context: Optional user context for targeting rules

        Returns:
            Variant key if user is assigned, None if excluded by traffic allocation
        """
        # Validate experiment config
        if not self.validate_experiment_config(experiment_config):
            logger.warning(
                f"Invalid experiment config",
                extra={
                    'experiment_id': experiment_config.experiment_id,
                    'status': experiment_config.status
                }
            )
            return None

        # Check targeting rules if they exist
        if experiment_config.targeting_rules:
            if not self.evaluate_targeting_rules(
                experiment_config.targeting_rules,
                context
            ):
                logger.info(
                    f"User excluded by targeting rules",
                    extra={
                        'user_id': user_id,
                        'experiment_id': experiment_config.experiment_id
                    }
                )
                return None

        # Convert variants to format expected by hasher
        variants = [
            {
                "key": v.key,
                "allocation": v.allocation
            }
            for v in experiment_config.variants
        ]

        # Use consistent hashing to assign variant
        variant = self.hasher.assign_variant(
            user_id=user_id,
            experiment_key=experiment_config.key,
            variants=variants,
            traffic_allocation=experiment_config.traffic_allocation,
            salt=experiment_config.salt
        )

        if variant:
            logger.info(
                f"Assigned user to variant",
                extra={
                    'user_id': user_id,
                    'experiment_id': experiment_config.experiment_id,
                    'variant': variant
                }
            )

        return variant

    def validate_experiment_config(self, experiment_config: ExperimentConfig) -> bool:
        """
        Validate that experiment configuration is ready for assignments.

        Args:
            experiment_config: Experiment configuration to validate

        Returns:
            True if valid and ACTIVE, False otherwise
        """
        # Only ACTIVE experiments can receive assignments
        if experiment_config.status != ExperimentStatus.ACTIVE:
            return False

        # Validate variants exist
        if not experiment_config.variants or len(experiment_config.variants) < 2:
            return False

        return True

    def get_experiment_config(self, experiment_key: str) -> Optional[ExperimentConfig]:
        """
        Fetch experiment configuration from DynamoDB.

        Args:
            experiment_key: Unique experiment key

        Returns:
            ExperimentConfig if found, None otherwise
        """
        try:
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(self.experiments_table_name)

            response = table.get_item(
                Key={'key': experiment_key}
            )

            if 'Item' not in response:
                logger.warning(f"Experiment not found: {experiment_key}")
                return None

            item = response['Item']

            # Parse DynamoDB item into ExperimentConfig
            config = ExperimentConfig(
                experiment_id=item['experiment_id'],
                key=item['key'],
                status=ExperimentStatus(item['status']),
                variants=item['variants'],
                traffic_allocation=item.get('traffic_allocation', 1.0),
                targeting_rules=item.get('targeting_rules'),
                salt=item.get('salt')
            )

            logger.info(f"Retrieved experiment config: {experiment_key}")
            return config

        except Exception as e:
            logger.error(
                f"Failed to get experiment config: {str(e)}",
                extra={'experiment_key': experiment_key}
            )
            return None

    def get_experiment_config_cached(self, experiment_key: str) -> Optional[ExperimentConfig]:
        """
        Fetch experiment configuration with Lambda warm-start caching.

        Args:
            experiment_key: Unique experiment key

        Returns:
            ExperimentConfig if found, None otherwise
        """
        # Check cache first
        if experiment_key in self._experiment_cache:
            if self._is_cache_valid(experiment_key):
                self._record_cache_hit()
                logger.debug(f"Cache hit for experiment: {experiment_key}")
                return self._experiment_cache[experiment_key]['config']
            else:
                # Cache expired, remove it
                del self._experiment_cache[experiment_key]

        # Cache miss - fetch from DynamoDB
        self._record_cache_miss()
        logger.debug(f"Cache miss for experiment: {experiment_key}")

        config = self.get_experiment_config(experiment_key)

        # Cache the result (even if None to avoid repeated lookups)
        self._cache_experiment_config(experiment_key, config)

        return config

    def _is_cache_valid(self, experiment_key: str) -> bool:
        """
        Check if cache entry is still valid based on TTL.

        Args:
            experiment_key: Experiment key to check

        Returns:
            True if cache entry is valid, False otherwise
        """
        if experiment_key not in self._experiment_cache:
            return False

        cache_entry = self._experiment_cache[experiment_key]
        cached_timestamp = cache_entry['timestamp']
        current_timestamp = datetime.now(timezone.utc).timestamp()

        # Check if cache has expired
        return (current_timestamp - cached_timestamp) < self.cache_ttl

    def _cache_experiment_config(
        self,
        experiment_key: str,
        config: Optional[ExperimentConfig]
    ) -> None:
        """
        Store experiment config in cache with timestamp.

        Args:
            experiment_key: Experiment key
            config: Experiment configuration (can be None)
        """
        self._experiment_cache[experiment_key] = {
            'config': config,
            'timestamp': datetime.now(timezone.utc).timestamp()
        }

    def _record_cache_hit(self) -> None:
        """Record a cache hit for metrics tracking."""
        self._cache_hits += 1

    def _record_cache_miss(self) -> None:
        """Record a cache miss for metrics tracking."""
        self._cache_misses += 1

    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate percentage.

        Returns:
            Hit rate as a decimal (0.0 to 1.0)
        """
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return 0.0
        return self._cache_hits / total_requests

    def create_assignment(
        self,
        user_id: str,
        experiment_config: ExperimentConfig,
        variant: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Assignment:
        """
        Create an Assignment object.

        Args:
            user_id: User identifier
            experiment_config: Experiment configuration
            variant: Assigned variant key
            context: Optional user context

        Returns:
            Assignment object
        """
        assignment_id = f"assign_{uuid.uuid4().hex[:12]}"

        assignment = Assignment(
            assignment_id=assignment_id,
            user_id=user_id,
            experiment_id=experiment_config.experiment_id,
            experiment_key=experiment_config.key,
            variant=variant,
            timestamp=datetime.now(timezone.utc),
            context=context
        )

        return assignment

    def store_assignment(self, assignment: Assignment) -> bool:
        """
        Store assignment in DynamoDB.

        Args:
            assignment: Assignment object to store

        Returns:
            True if successful, False otherwise
        """
        from utils import put_dynamodb_item

        assignments_table_name = get_env_variable(
            'ASSIGNMENTS_TABLE',
            default='experimently-assignments'
        )

        # Calculate TTL (90 days from now)
        ttl = int((datetime.now(timezone.utc).timestamp()) + (90 * 24 * 60 * 60))

        # Prepare item for DynamoDB
        item = {
            'user_id': assignment.user_id,
            'experiment_id': assignment.experiment_id,
            'assignment_id': assignment.assignment_id,
            'experiment_key': assignment.experiment_key,
            'variant': assignment.variant,
            'timestamp': assignment.timestamp.isoformat(),
            'ttl': ttl
        }

        if assignment.context:
            item['context'] = assignment.context

        # Use condition expression to prevent overwriting existing assignments
        condition = "attribute_not_exists(user_id) AND attribute_not_exists(experiment_id)"

        success = put_dynamodb_item(
            table_name=assignments_table_name,
            item=item,
            condition_expression=condition
        )

        if success:
            logger.info(
                f"Stored assignment",
                extra={
                    'user_id': assignment.user_id,
                    'experiment_id': assignment.experiment_id,
                    'variant': assignment.variant
                }
            )

        return success

    def get_assignment(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[Assignment]:
        """
        Retrieve existing assignment from DynamoDB.

        Args:
            user_id: User identifier
            experiment_id: Experiment identifier

        Returns:
            Assignment if found, None otherwise
        """
        from utils import get_dynamodb_item

        assignments_table_name = get_env_variable(
            'ASSIGNMENTS_TABLE',
            default='experimently-assignments'
        )

        try:
            item = get_dynamodb_item(
                table_name=assignments_table_name,
                key={
                    'user_id': user_id,
                    'experiment_id': experiment_id
                }
            )

            if not item:
                return None

            # Parse item into Assignment object
            assignment = Assignment(
                assignment_id=item['assignment_id'],
                user_id=item['user_id'],
                experiment_id=item['experiment_id'],
                experiment_key=item['experiment_key'],
                variant=item['variant'],
                timestamp=datetime.fromisoformat(item['timestamp']),
                context=item.get('context')
            )

            logger.info(
                f"Retrieved existing assignment",
                extra={
                    'user_id': user_id,
                    'experiment_id': experiment_id,
                    'variant': assignment.variant
                }
            )

            return assignment

        except Exception as e:
            logger.error(
                f"Failed to get assignment: {str(e)}",
                extra={
                    'user_id': user_id,
                    'experiment_id': experiment_id
                }
            )
            return None

    def get_or_create_assignment(
        self,
        user_id: str,
        experiment_config: ExperimentConfig,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Assignment]:
        """
        Get existing assignment or create new one if doesn't exist.

        Args:
            user_id: User identifier
            experiment_config: Experiment configuration
            context: Optional user context

        Returns:
            Assignment if user is assigned, None if excluded
        """
        # Check for existing assignment
        existing = self.get_assignment(user_id, experiment_config.experiment_id)
        if existing:
            return existing

        # Create new assignment
        variant = self.assign_variant(user_id, experiment_config, context)

        # User excluded by traffic allocation
        if variant is None:
            return None

        # Create assignment object
        assignment = self.create_assignment(
            user_id=user_id,
            experiment_config=experiment_config,
            variant=variant,
            context=context
        )

        # Store in DynamoDB
        self.store_assignment(assignment)

        return assignment
