"""
Feature Flag Evaluator for real-time flag evaluation.

Provides core logic for evaluating feature flags with:
- Rollout percentage calculation using consistent hashing
- Targeting rules evaluation
- Variant assignment (if configured)
- Lambda warm-start caching for performance

Following TDD (Test-Driven Development) - GREEN phase: Implementation to pass tests.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from consistent_hash import get_hasher
from models import FeatureFlagConfig, VariantConfig
from utils import get_dynamodb_resource, get_logger, get_env_variable

logger = get_logger(__name__)


class FeatureFlagEvaluator:
    """
    Service for evaluating feature flags.

    Uses consistent hashing for deterministic rollout and variant assignment.
    Implements caching for high-performance evaluation.
    """

    def __init__(self):
        """Initialize the feature flag evaluator."""
        self.hasher = get_hasher()
        self.flags_table_name = get_env_variable(
            'FLAGS_TABLE',
            default='experimently-feature-flags'
        )

        # Cache for flag configurations (Lambda warm-start optimization)
        self._flag_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes in seconds

        # Cache hit rate tracking
        self._cache_hits = 0
        self._cache_misses = 0

    def evaluate(
        self,
        user_id: str,
        flag_config: FeatureFlagConfig,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a feature flag for a user.

        Args:
            user_id: Unique user identifier
            flag_config: Feature flag configuration
            context: Optional user context for targeting rules

        Returns:
            Dict with keys:
                - enabled: bool (whether flag is enabled for user)
                - reason: str (reason for the decision)
                - variant: Optional[str] (variant key if variants configured)

        Raises:
            ValueError: If user_id is None or empty
        """
        # Validate user_id
        if user_id is None:
            raise ValueError("user_id cannot be None")
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")

        # Check if flag is globally disabled
        if not flag_config.enabled:
            return {
                "enabled": False,
                "reason": "flag_disabled",
                "variant": None
            }

        # Evaluate targeting rules if they exist
        if flag_config.targeting_rules:
            if not self.evaluate_targeting_rules(
                flag_config.targeting_rules,
                context
            ):
                return {
                    "enabled": False,
                    "reason": "targeting_rules_not_met",
                    "variant": None
                }

        # Check rollout percentage
        if not self.is_user_in_rollout(user_id, flag_config):
            return {
                "enabled": False,
                "reason": "not_in_rollout",
                "variant": None
            }

        # Flag is enabled - assign variant if configured
        variant = None
        if flag_config.variants:
            variant = self.assign_variant(user_id, flag_config)

        return {
            "enabled": True,
            "reason": "enabled",
            "variant": variant
        }

    def is_user_in_rollout(
        self,
        user_id: str,
        flag_config: FeatureFlagConfig
    ) -> bool:
        """
        Determine if user is in rollout percentage using consistent hashing.

        Args:
            user_id: User identifier
            flag_config: Feature flag configuration

        Returns:
            True if user is in rollout, False otherwise
        """
        rollout_percentage = flag_config.rollout_percentage

        # 0% rollout - no users included
        if rollout_percentage <= 0:
            return False

        # 100% rollout - all users included
        if rollout_percentage >= 100:
            return True

        # Use consistent hashing to determine if user is in rollout
        # Get bucket from 0-99 (100 buckets for percentage)
        bucket = self.hasher.get_bucket(
            user_id=user_id,
            experiment_key=flag_config.key,
            num_buckets=100
        )

        # User is included if their bucket is less than rollout percentage
        return bucket < rollout_percentage

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
        flag_config: FeatureFlagConfig
    ) -> Optional[str]:
        """
        Assign a user to a variant using consistent hashing.

        Args:
            user_id: User identifier
            flag_config: Feature flag configuration with variants

        Returns:
            Variant key if variants configured, None otherwise
        """
        if not flag_config.variants:
            return flag_config.default_variant

        # Convert variants to format expected by hasher
        variants = [
            {
                "key": v.key,
                "allocation": v.allocation
            }
            for v in flag_config.variants
        ]

        # Use consistent hashing to assign variant
        # We use traffic_allocation=1.0 since rollout is already checked
        variant = self.hasher.assign_variant(
            user_id=user_id,
            experiment_key=flag_config.key,
            variants=variants,
            traffic_allocation=1.0,
            salt=None
        )

        return variant if variant else flag_config.default_variant

    def get_flag_config(self, flag_key: str) -> Optional[FeatureFlagConfig]:
        """
        Fetch feature flag configuration from DynamoDB.

        Args:
            flag_key: Unique flag key

        Returns:
            FeatureFlagConfig if found, None otherwise
        """
        try:
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(self.flags_table_name)

            response = table.get_item(
                Key={'key': flag_key}
            )

            if 'Item' not in response:
                logger.warning(f"Feature flag not found: {flag_key}")
                return None

            item = response['Item']

            # Parse variants if present
            variants = None
            if 'variants' in item and item['variants']:
                variants = [
                    VariantConfig(**v) for v in item['variants']
                ]

            # Parse DynamoDB item into FeatureFlagConfig
            config = FeatureFlagConfig(
                flag_id=item['flag_id'],
                key=item['key'],
                enabled=item.get('enabled', False),
                rollout_percentage=item.get('rollout_percentage', 0.0),
                targeting_rules=item.get('targeting_rules'),
                default_variant=item.get('default_variant'),
                variants=variants
            )

            logger.info(f"Retrieved feature flag config: {flag_key}")
            return config

        except Exception as e:
            logger.error(
                f"Failed to get flag config: {str(e)}",
                extra={'flag_key': flag_key}
            )
            return None

    def get_flag_config_cached(self, flag_key: str) -> Optional[FeatureFlagConfig]:
        """
        Fetch feature flag configuration with Lambda warm-start caching.

        Args:
            flag_key: Unique flag key

        Returns:
            FeatureFlagConfig if found, None otherwise
        """
        # Check cache first
        if flag_key in self._flag_cache:
            if self._is_cache_valid(flag_key):
                self._record_cache_hit()
                logger.debug(f"Cache hit for flag: {flag_key}")
                return self._flag_cache[flag_key]['config']
            else:
                # Cache expired, remove it
                del self._flag_cache[flag_key]

        # Cache miss - fetch from DynamoDB
        self._record_cache_miss()
        logger.debug(f"Cache miss for flag: {flag_key}")

        config = self.get_flag_config(flag_key)

        # Cache the result (even if None to avoid repeated lookups)
        self._cache_flag_config(flag_key, config)

        return config

    def _is_cache_valid(self, flag_key: str) -> bool:
        """
        Check if cache entry is still valid based on TTL.

        Args:
            flag_key: Flag key to check

        Returns:
            True if cache entry is valid, False otherwise
        """
        if flag_key not in self._flag_cache:
            return False

        cache_entry = self._flag_cache[flag_key]
        cached_timestamp = cache_entry['timestamp']
        current_timestamp = datetime.now(timezone.utc).timestamp()

        # Check if cache has expired
        return (current_timestamp - cached_timestamp) < self.cache_ttl

    def _cache_flag_config(
        self,
        flag_key: str,
        config: Optional[FeatureFlagConfig]
    ) -> None:
        """
        Store flag config in cache with timestamp.

        Args:
            flag_key: Flag key
            config: Feature flag configuration (can be None)
        """
        self._flag_cache[flag_key] = {
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

    def batch_evaluate(
        self,
        user_id: str,
        flag_keys: list[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate multiple feature flags for a user in a single call.

        This is optimized for SDK use cases where multiple flags need to be
        evaluated at once. Uses cached configurations when available.

        Args:
            user_id: Unique user identifier
            flag_keys: List of flag keys to evaluate
            context: Optional user context for targeting rules

        Returns:
            Dictionary mapping flag_key to evaluation result:
            {
                "flag_key1": {"enabled": True, "reason": "enabled", "variant": "treatment"},
                "flag_key2": {"enabled": False, "reason": "not_in_rollout", "variant": None}
            }

            For flags that don't exist, result will be:
            {"enabled": False, "reason": "flag_not_found", "variant": None}

        Example:
            >>> evaluator = FeatureFlagEvaluator()
            >>> results = evaluator.batch_evaluate(
            ...     user_id="user_123",
            ...     flag_keys=["new_checkout", "dark_mode", "ai_recommendations"]
            ... )
            >>> results["new_checkout"]["enabled"]
            True
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be None or empty")

        if not flag_keys:
            return {}

        results = {}

        for flag_key in flag_keys:
            # Get flag config (with caching)
            flag_config = self.get_flag_config_cached(flag_key)

            if not flag_config:
                # Flag doesn't exist
                results[flag_key] = {
                    "enabled": False,
                    "reason": "flag_not_found",
                    "variant": None
                }
                continue

            # Evaluate flag
            evaluation_result = self.evaluate(
                user_id=user_id,
                flag_config=flag_config,
                context=context
            )

            results[flag_key] = evaluation_result

        return results
