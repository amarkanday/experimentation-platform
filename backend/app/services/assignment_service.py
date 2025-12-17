# Experiment assignment service
# Analysis and reporting service
# backend/app/services/assignment_service.py
import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.models.experiment import Experiment, Variant, ExperimentStatus
from backend.app.models.assignment import Assignment
from backend.app.services.event_service import EventService
from backend.app.services.rules_evaluation_service import RulesEvaluationService
from backend.app.schemas.targeting_rule import TargetingRules

logger = logging.getLogger(__name__)


class AssignmentService:
    """
    Service for managing user assignments to experiment variants.

    This service handles:
    - Assigning users to experiment variants using deterministic hashing
    - Tracking user assignments
    - Retrieving user assignments for experiments
    - Managing sticky assignments
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db
        self.event_service = EventService(db)
        self.rules_evaluation_service = RulesEvaluationService()

    def get_assignment(
        self, user_id: str, experiment_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's assignment for a specific experiment.

        Args:
            user_id: ID of the user
            experiment_id: ID of the experiment

        Returns:
            Dictionary containing the assignment data or None if not found
        """
        assignment = (
            self.db.query(Assignment)
            .filter(
                Assignment.user_id == user_id, Assignment.experiment_id == experiment_id
            )
            .order_by(desc(Assignment.created_at))
            .first()
        )

        if not assignment:
            return None

        # Get variant details
        variant = (
            self.db.query(Variant).filter(Variant.id == assignment.variant_id).first()
        )

        return {
            "id": str(assignment.id),
            "user_id": assignment.user_id,
            "experiment_id": str(assignment.experiment_id),
            "variant_id": str(assignment.variant_id),
            "variant_name": variant.name if variant else None,
            "is_control": variant.is_control if variant else None,
            "created_at": (
                assignment.created_at.isoformat()
                if hasattr(assignment.created_at, "isoformat")
                else assignment.created_at
            ),
            "updated_at": (
                assignment.updated_at.isoformat()
                if hasattr(assignment.updated_at, "isoformat")
                else assignment.updated_at
            ),
        }

    def assign_user(
        self,
        user_id: str,
        experiment_id: Union[str, UUID],
        track_exposure: bool = True,
        override_variant_id: Optional[Union[str, UUID]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assign a user to an experiment variant.

        Args:
            user_id: ID of the user to assign
            experiment_id: ID of the experiment
            track_exposure: Whether to track an exposure event
            override_variant_id: Optional variant ID to force assignment
            context: Optional context data for targeting

        Returns:
            Dictionary containing the assignment data

        Raises:
            ValueError: If the experiment is not active or has issues
        """
        # Get experiment with variants
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Check experiment status
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ValueError(
                f"Cannot assign users to experiment with status: {experiment.status}"
            )

        # Check for existing assignment (sticky assignment)
        existing_assignment = (
            self.db.query(Assignment)
            .filter(
                Assignment.user_id == user_id, Assignment.experiment_id == experiment_id
            )
            .order_by(desc(Assignment.created_at))
            .first()
        )

        if existing_assignment:
            # Return existing assignment
            logger.debug(
                f"Using existing assignment for user {user_id} in experiment {experiment_id}"
            )
            assignment_dict = self.get_assignment(user_id, experiment_id)

            # Optionally track exposure event
            if track_exposure:
                self.event_service.track_exposure(
                    user_id=user_id,
                    experiment_id=str(experiment_id),
                    variant_id=str(existing_assignment.variant_id),
                    properties=context,
                )

            return assignment_dict

        # Determine variant assignment
        if override_variant_id:
            # Use override if provided (useful for forcing assignment or testing)
            variant_id = override_variant_id

            # Verify override variant is valid for this experiment
            variant_valid = any(
                v.id == override_variant_id for v in experiment.variants
            )
            if not variant_valid:
                raise ValueError(
                    f"Override variant {override_variant_id} not valid for experiment {experiment_id}"
                )
        else:
            # Use deterministic hashing to assign variant
            variant_id = self._hash_user_to_variant(user_id, experiment)

        # Create new assignment
        assignment = Assignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        logger.info(
            f"Assigned user {user_id} to variant {variant_id} in experiment {experiment_id}"
        )

        # Track exposure event if requested
        if track_exposure:
            self.event_service.track_exposure(
                user_id=user_id,
                experiment_id=str(experiment_id),
                variant_id=str(variant_id),
                properties=context,
            )

        # Get full assignment details
        return self.get_assignment(user_id, experiment_id)

    def get_user_assignments(
        self, user_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a user.

        Args:
            user_id: ID of the user
            active_only: If True, only return assignments for active experiments

        Returns:
            List of assignment dictionaries
        """
        # Base query
        query = self.db.query(Assignment).filter(Assignment.user_id == user_id)

        if active_only:
            # Join with experiments to filter by status
            query = query.join(
                Experiment, Assignment.experiment_id == Experiment.id
            ).filter(Experiment.status == ExperimentStatus.ACTIVE)

        # Get latest assignment for each experiment
        subq = (
            self.db.query(
                Assignment.experiment_id,
                func.max(Assignment.created_at).label("latest_assignment"),
            )
            .filter(Assignment.user_id == user_id)
            .group_by(Assignment.experiment_id)
            .subquery()
        )

        query = query.join(
            subq,
            and_(
                Assignment.experiment_id == subq.c.experiment_id,
                Assignment.created_at == subq.c.latest_assignment,
            ),
        )

        assignments = query.all()

        # Format results
        results = []
        for assignment in assignments:
            # Get variant details
            variant = (
                self.db.query(Variant)
                .filter(Variant.id == assignment.variant_id)
                .first()
            )

            # Get experiment details
            experiment = (
                self.db.query(Experiment)
                .filter(Experiment.id == assignment.experiment_id)
                .first()
            )

            results.append(
                {
                    "id": str(assignment.id),
                    "user_id": assignment.user_id,
                    "experiment_id": str(assignment.experiment_id),
                    "experiment_name": experiment.name if experiment else None,
                    "variant_id": str(assignment.variant_id),
                    "variant_name": variant.name if variant else None,
                    "is_control": variant.is_control if variant else None,
                    "created_at": (
                        assignment.created_at.isoformat()
                        if hasattr(assignment.created_at, "isoformat")
                        else assignment.created_at
                    ),
                }
            )

        return results

    def bulk_assign_users(
        self,
        user_ids: List[str],
        experiment_id: Union[str, UUID],
        track_exposure: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assign multiple users to an experiment in bulk.

        Args:
            user_ids: List of user IDs to assign
            experiment_id: ID of the experiment
            track_exposure: Whether to track exposure events
            context: Optional context data for targeting

        Returns:
            Dictionary with counts of assignments
        """
        if not user_ids:
            return {"assigned": 0, "skipped": 0, "errors": 0}

        # Get experiment to verify it exists and is active
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Check experiment status
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ValueError(
                f"Cannot assign users to experiment with status: {experiment.status}"
            )

        # Track counts
        assigned = 0
        skipped = 0
        errors = 0

        # Process each user
        for user_id in user_ids:
            try:
                # Check for existing assignment
                existing_assignment = (
                    self.db.query(Assignment)
                    .filter(
                        Assignment.user_id == user_id,
                        Assignment.experiment_id == experiment_id,
                    )
                    .first()
                )

                if existing_assignment:
                    # Skip users who already have an assignment
                    skipped += 1
                    continue

                # Assign user
                variant_id = self._hash_user_to_variant(user_id, experiment)

                # Create new assignment
                assignment = Assignment(
                    user_id=user_id,
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                )

                self.db.add(assignment)
                assigned += 1

                # Track exposure if requested (needs to happen after commit)
                if track_exposure:
                    self.event_service.track_exposure(
                        user_id=user_id,
                        experiment_id=str(experiment_id),
                        variant_id=str(variant_id),
                        properties=context,
                    )

            except Exception as e:
                logger.error(
                    f"Error assigning user {user_id} to experiment {experiment_id}: {str(e)}"
                )
                errors += 1

        # Commit all assignments in a single transaction
        self.db.commit()

        logger.info(
            f"Bulk assigned {assigned} users to experiment {experiment_id} (skipped: {skipped}, errors: {errors})"
        )

        return {"assigned": assigned, "skipped": skipped, "errors": errors}

    def assign_user_with_targeting(
        self,
        user_id: str,
        experiment_id: Union[str, UUID],
        user_context: Dict[str, Any],
        track_exposure: bool = True,
        validate_attributes: bool = True,
    ) -> Dict[str, Any]:
        """
        Assign a user to an experiment variant using targeting rules.

        Args:
            user_id: ID of the user to assign
            experiment_id: ID of the experiment
            user_context: User context for targeting evaluation
            track_exposure: Whether to track an exposure event
            validate_attributes: Whether to validate user attributes

        Returns:
            Dictionary containing the assignment data and targeting info

        Raises:
            ValueError: If the experiment is not active or targeting fails
        """
        # Get experiment with variants
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Check experiment status
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ValueError(
                f"Cannot assign users to experiment with status: {experiment.status}"
            )

        # Ensure user_id is in context
        if 'user_id' not in user_context:
            user_context['user_id'] = user_id

        # Check for existing assignment (sticky assignment)
        existing_assignment = (
            self.db.query(Assignment)
            .filter(
                Assignment.user_id == user_id, Assignment.experiment_id == experiment_id
            )
            .order_by(desc(Assignment.created_at))
            .first()
        )

        if existing_assignment:
            logger.debug(
                f"Using existing assignment for user {user_id} in experiment {experiment_id}"
            )
            assignment_dict = self.get_assignment(user_id, experiment_id)

            # Add targeting info
            assignment_dict.update({
                'targeting_matched': True,
                'targeting_rule_id': 'existing_assignment',
                'user_context_validated': True,
            })

            # Optionally track exposure event
            if track_exposure:
                self.event_service.track_exposure(
                    user_id=user_id,
                    experiment_id=str(experiment_id),
                    variant_id=str(existing_assignment.variant_id),
                    properties=user_context,
                )

            return assignment_dict

        # Evaluate targeting rules if experiment has them
        targeting_result = self._evaluate_experiment_targeting(
            experiment, user_context, validate_attributes
        )

        if not targeting_result['eligible']:
            # User doesn't match targeting criteria
            logger.info(
                f"User {user_id} not eligible for experiment {experiment_id}: {targeting_result['reason']}"
            )
            return {
                'assignment': None,
                'targeting_matched': False,
                'targeting_rule_id': None,
                'reason': targeting_result['reason'],
                'user_context_validated': targeting_result.get('validation_passed', True),
                'evaluation_metrics': targeting_result.get('metrics'),
            }

        # Determine variant assignment
        variant_id = self._hash_user_to_variant(user_id, experiment)

        # Create new assignment
        assignment = Assignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        logger.info(
            f"Assigned user {user_id} to variant {variant_id} in experiment {experiment_id} via targeting"
        )

        # Track exposure event if requested
        if track_exposure:
            # Include targeting information in exposure event
            exposure_properties = user_context.copy()
            exposure_properties.update({
                'targeting_rule_id': targeting_result.get('rule_id'),
                'targeting_matched': True,
            })

            self.event_service.track_exposure(
                user_id=user_id,
                experiment_id=str(experiment_id),
                variant_id=str(variant_id),
                properties=exposure_properties,
            )

        # Get full assignment details and add targeting info
        assignment_dict = self.get_assignment(user_id, experiment_id)
        assignment_dict.update({
            'targeting_matched': True,
            'targeting_rule_id': targeting_result.get('rule_id'),
            'user_context_validated': targeting_result.get('validation_passed', True),
            'evaluation_metrics': targeting_result.get('metrics'),
        })

        return assignment_dict

    def _evaluate_experiment_targeting(
        self, experiment: Experiment, user_context: Dict[str, Any], validate_attributes: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate if a user meets experiment targeting criteria.

        Args:
            experiment: The experiment model
            user_context: User context for evaluation
            validate_attributes: Whether to validate attributes

        Returns:
            Dictionary with targeting evaluation results
        """
        try:
            # Check if experiment has targeting rules
            if not hasattr(experiment, 'targeting_rules') or not experiment.targeting_rules:
                # No targeting rules - allow all users
                return {
                    'eligible': True,
                    'rule_id': None,
                    'reason': 'No targeting rules defined',
                    'validation_passed': True,
                }

            # Parse targeting rules (assuming JSON stored in database)
            if isinstance(experiment.targeting_rules, str):
                targeting_rules_data = json.loads(experiment.targeting_rules)
                targeting_rules = TargetingRules(**targeting_rules_data)
            elif isinstance(experiment.targeting_rules, dict):
                targeting_rules = TargetingRules(**experiment.targeting_rules)
            else:
                # Assume it's already a TargetingRules object
                targeting_rules = experiment.targeting_rules

            # Evaluate rules with validation
            matched_rule, metrics = self.rules_evaluation_service.evaluate_rules_with_validation(
                targeting_rules=targeting_rules,
                user_context=user_context,
                validate_attributes=validate_attributes,
                track_metrics=True,
            )

            if matched_rule:
                return {
                    'eligible': True,
                    'rule_id': matched_rule.id,
                    'reason': f"Matched targeting rule: {matched_rule.name or matched_rule.id}",
                    'validation_passed': metrics.error is None if metrics else True,
                    'metrics': metrics,
                }
            else:
                return {
                    'eligible': False,
                    'rule_id': None,
                    'reason': 'No targeting rules matched',
                    'validation_passed': metrics.error is None if metrics else True,
                    'metrics': metrics,
                }

        except Exception as e:
            logger.error(f"Error evaluating experiment targeting: {str(e)}")
            return {
                'eligible': False,
                'rule_id': None,
                'reason': f'Targeting evaluation error: {str(e)}',
                'validation_passed': False,
            }

    def get_targeting_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for targeting evaluations.

        Returns:
            Dictionary with performance metrics
        """
        return self.rules_evaluation_service.get_performance_stats()

    def clear_targeting_metrics(self):
        """Clear collected targeting metrics."""
        self.rules_evaluation_service.clear_metrics()

    def reassign_user(
        self,
        user_id: str,
        experiment_id: Union[str, UUID],
        variant_id: Optional[Union[str, UUID]] = None,
        track_exposure: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Reassign a user to a new variant in an experiment.

        Args:
            user_id: ID of the user to reassign
            experiment_id: ID of the experiment
            variant_id: Optional variant ID to force assignment
            track_exposure: Whether to track an exposure event
            context: Optional context data

        Returns:
            Dictionary containing the new assignment data
        """
        # Get experiment to verify it exists and is active
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Determine variant assignment
        if variant_id:
            # Verify variant is valid for this experiment
            variant_valid = any(v.id == variant_id for v in experiment.variants)
            if not variant_valid:
                raise ValueError(
                    f"Variant {variant_id} not valid for experiment {experiment_id}"
                )
        else:
            # Use deterministic hashing to reassign variant
            variant_id = self._hash_user_to_variant(user_id, experiment)

        # Create new assignment
        assignment = Assignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        logger.info(
            f"Reassigned user {user_id} to variant {variant_id} in experiment {experiment_id}"
        )

        # Track exposure event if requested
        if track_exposure:
            self.event_service.track_exposure(
                user_id=user_id,
                experiment_id=str(experiment_id),
                variant_id=str(variant_id),
                properties=context,
            )

        # Get full assignment details
        return self.get_assignment(user_id, experiment_id)

    def _hash_user_to_variant(
        self, user_id: str, experiment: Experiment
    ) -> Union[str, UUID]:
        """
        Determine variant assignment using deterministic hashing.

        This ensures that the same user will always be assigned to the same variant
        for a given experiment, based on their user ID and the experiment ID.

        Args:
            user_id: ID of the user to assign
            experiment: Experiment model object with variants

        Returns:
            ID of the assigned variant
        """
        if not experiment.variants:
            raise ValueError(f"Experiment {experiment.id} has no variants")

        # Create a hash using user ID and experiment ID
        hash_input = f"{user_id}:{experiment.id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Get variants with their traffic allocations
        variants = experiment.variants

        # Create cumulative distribution based on traffic allocation
        total = 0
        distribution = []
        for variant in variants:
            total += variant.traffic_allocation
            distribution.append((total, variant.id))

        # Normalize hash to be within range [0, 100)
        bucket = hash_value % 100

        # Find the assigned variant
        for threshold, variant_id in distribution:
            if bucket < threshold:
                return variant_id

        # Fallback to last variant (should not happen if allocations sum to 100)
        return variants[-1].id if variants else None

    def delete_assignments_by_experiment(self, experiment_id: Union[str, UUID]) -> int:
        """
        Delete all assignments for an experiment.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Number of assignments deleted
        """
        # Count assignments before deletion
        count_query = self.db.query(func.count(Assignment.id)).filter(
            Assignment.experiment_id == experiment_id
        )
        count = count_query.scalar() or 0

        # Delete assignments
        delete_query = self.db.query(Assignment).filter(
            Assignment.experiment_id == experiment_id
        )
        delete_query.delete(synchronize_session=False)

        self.db.commit()

        logger.info(f"Deleted {count} assignments for experiment {experiment_id}")
        return count
