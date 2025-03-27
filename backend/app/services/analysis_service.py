# backend/app/services/analysis_service.py
import logging
import math
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import func, and_, or_, desc, text
from sqlalchemy.orm import Session, joinedload

from backend.app.models.experiment import Experiment, Variant, Metric, ExperimentStatus
from backend.app.models.event import Event, EventType
from backend.app.models.assignment import Assignment
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service for analyzing experiment results and calculating statistics.

    This service provides the analytics capabilities of the platform, including:
    - Calculating conversion rates and other metrics
    - Performing statistical tests to determine significance
    - Generating result summaries and reports
    - Computing confidence intervals and effect sizes
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db

    def get_experiment_results(self, experiment_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        Get comprehensive results for an experiment.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Dictionary containing experiment results data
        """
        # Get experiment with variants and metrics
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metrics))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Calculate results for each metric
        metrics_results = []
        for metric in experiment.metrics:
            metric_result = self.calculate_metric_results(experiment, metric)
            metrics_results.append(metric_result)

        # Calculate overall summary statistics
        summary = self.calculate_experiment_summary(experiment)

        # Return formatted results
        return {
            "experiment_id": str(experiment_id),
            "experiment_name": experiment.name,
            "status": (
                experiment.status.value
                if hasattr(experiment.status, "value")
                else experiment.status
            ),
            "start_date": experiment.start_date,
            "end_date": experiment.end_date,
            "metrics_results": metrics_results,
            "summary": summary,
        }

    def calculate_metric_results(
        self, experiment: Experiment, metric: Metric
    ) -> Dict[str, Any]:
        """
        Calculate results for a specific metric in an experiment.

        Args:
            experiment: Experiment model object
            metric: Metric model object

        Returns:
            Dictionary containing metric results
        """
        # Get variant IDs for the experiment
        variant_ids = [str(v.id) for v in experiment.variants]

        # Find control variant
        control_variant = next((v for v in experiment.variants if v.is_control), None)
        if not control_variant:
            raise ValueError(f"Experiment {experiment.id} has no control variant")

        # Get assignment counts per variant
        assignments = {}
        for variant_id in variant_ids:
            count = (
                self.db.query(func.count(Assignment.id))
                .filter(
                    Assignment.experiment_id == experiment.id,
                    Assignment.variant_id == variant_id,
                )
                .scalar()
                or 0
            )
            assignments[variant_id] = count

        # Get conversion counts per variant
        conversions = {}
        for variant_id in variant_ids:
            count = (
                self.db.query(func.count(Event.id))
                .filter(
                    Event.experiment_id == experiment.id,
                    Event.variant_id == variant_id,
                    Event.event_type == EventType.CONVERSION.value,
                    Event.event_name == metric.event_name,
                )
                .scalar()
                or 0
            )
            conversions[variant_id] = count

        # Calculate conversion rates
        rates = {}
        for variant_id in variant_ids:
            if assignments[variant_id] > 0:
                rate = (conversions[variant_id] / assignments[variant_id]) * 100
            else:
                rate = 0
            rates[variant_id] = rate

        # Calculate statistical significance compared to control
        results = []
        control_conversions = conversions[str(control_variant.id)]
        control_non_conversions = (
            assignments[str(control_variant.id)] - control_conversions
        )

        for variant in experiment.variants:
            variant_id = str(variant.id)

            # Skip if it's the control variant
            if variant.is_control:
                p_value = 1.0
                is_significant = False
                relative_improvement = 0
            else:
                # Calculate p-value using Fisher's exact test
                variant_conversions = conversions[variant_id]
                variant_non_conversions = assignments[variant_id] - variant_conversions

                # Create contingency table
                contingency_table = [
                    [variant_conversions, variant_non_conversions],
                    [control_conversions, control_non_conversions],
                ]

                # Run Fisher's exact test
                try:
                    odds_ratio, p_value = stats.fisher_exact(contingency_table)
                    is_significant = p_value < 0.05  # Using 95% confidence level

                    # Calculate relative improvement
                    if rates[str(control_variant.id)] > 0:
                        relative_improvement = (
                            (rates[variant_id] - rates[str(control_variant.id)])
                            / rates[str(control_variant.id)]
                        ) * 100
                    else:
                        relative_improvement = (
                            float("inf") if rates[variant_id] > 0 else 0
                        )
                except Exception as e:
                    logger.error(f"Error calculating statistics: {str(e)}")
                    p_value = None
                    is_significant = False
                    relative_improvement = None

            # Calculate confidence interval using normal approximation
            if assignments[variant_id] > 0:
                proportion = rates[variant_id] / 100  # Convert percentage to proportion
                z = 1.96  # For 95% confidence level

                # Standard error of proportion
                se = math.sqrt(
                    (proportion * (1 - proportion)) / assignments[variant_id]
                )

                # Confidence interval
                ci_lower = max(0, (proportion - z * se) * 100)
                ci_upper = min(100, (proportion + z * se) * 100)
            else:
                ci_lower = 0
                ci_upper = 0

            # Format variant result
            variant_result = {
                "variant_id": variant_id,
                "variant_name": variant.name,
                "is_control": variant.is_control,
                "sample_size": assignments[variant_id],
                "conversions": conversions[variant_id],
                "conversion_rate": rates[variant_id],
                "confidence_interval": [ci_lower, ci_upper],
                "p_value": p_value,
                "is_significant": is_significant,
                "relative_improvement": relative_improvement,
            }

            results.append(variant_result)

        # Format metric result
        return {
            "metric_id": str(metric.id),
            "metric_name": metric.name,
            "event_name": metric.event_name,
            "variant_results": results,
            "total_conversions": sum(conversions.values()),
            "has_significant_results": any(r["is_significant"] for r in results),
            "best_variant": self._find_best_variant(results),
        }

    def calculate_experiment_summary(self, experiment: Experiment) -> Dict[str, Any]:
        """
        Calculate overall summary statistics for an experiment.

        Args:
            experiment: Experiment model object

        Returns:
            Dictionary containing summary statistics
        """
        # Get start and end dates
        start_date = experiment.start_date
        end_date = experiment.end_date or datetime.now(timezone.utc).isoformat()

        # Calculate experiment duration in days
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                duration_days = (end_dt - start_dt).days
            except (ValueError, TypeError):
                duration_days = None
        else:
            duration_days = None

        # Get total number of users in experiment
        total_users = (
            self.db.query(func.count(Assignment.user_id.distinct()))
            .filter(Assignment.experiment_id == experiment.id)
            .scalar()
            or 0
        )

        # Get total number of events
        total_events = (
            self.db.query(func.count(Event.id))
            .filter(Event.experiment_id == experiment.id)
            .scalar()
            or 0
        )

        # Get total conversions
        total_conversions = (
            self.db.query(func.count(Event.id))
            .filter(
                Event.experiment_id == experiment.id,
                Event.event_type == EventType.CONVERSION.value,
            )
            .scalar()
            or 0
        )

        # Return formatted summary
        return {
            "total_users": total_users,
            "total_events": total_events,
            "total_conversions": total_conversions,
            "start_date": start_date,
            "end_date": end_date,
            "duration_days": duration_days,
        }

    def get_daily_results(
        self,
        experiment_id: Union[str, UUID],
        metric_id: Optional[Union[str, UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily results for an experiment or specific metric.

        Args:
            experiment_id: ID of the experiment
            metric_id: Optional ID of the metric to filter by

        Returns:
            List of daily result dictionaries
        """
        # Get experiment with variants and metrics
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metrics))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Determine start and end dates
        if not experiment.start_date:
            return []

        start_dt = datetime.fromisoformat(experiment.start_date.replace("Z", "+00:00"))
        end_dt = (
            datetime.fromisoformat(experiment.end_date.replace("Z", "+00:00"))
            if experiment.end_date
            else datetime.now(timezone.utc)
        )

        # Generate list of dates
        dates = []
        current_dt = start_dt
        while current_dt <= end_dt:
            dates.append(current_dt.strftime("%Y-%m-%d"))
            current_dt += timedelta(days=1)

        # Filter metrics if metric_id is provided
        metrics = [
            m
            for m in experiment.metrics
            if not metric_id or str(m.id) == str(metric_id)
        ]

        if not metrics:
            return []

        # Get daily assignments (can be optimized with a single query)
        daily_assignments = {}
        for date in dates:
            daily_variant_assignments = {}

            # Get counts by variant for this date
            for variant in experiment.variants:
                # Convert date string to datetime range
                date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
                date_end = datetime.fromisoformat(f"{date}T23:59:59+00:00")

                # Query assignments for this variant on this date
                count = (
                    self.db.query(func.count(Assignment.id))
                    .filter(
                        Assignment.experiment_id == experiment.id,
                        Assignment.variant_id == variant.id,
                        Assignment.created_at >= date_start,
                        Assignment.created_at <= date_end,
                    )
                    .scalar()
                    or 0
                )

                daily_variant_assignments[str(variant.id)] = count

            daily_assignments[date] = daily_variant_assignments

        # Get daily conversions by metric and variant
        results = []
        for date in dates:
            date_results = {"date": date, "metrics": []}

            for metric in metrics:
                metric_result = {
                    "metric_id": str(metric.id),
                    "metric_name": metric.name,
                    "variants": [],
                }

                for variant in experiment.variants:
                    # Convert date string to datetime range
                    date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
                    date_end = datetime.fromisoformat(f"{date}T23:59:59+00:00")

                    # Query conversions for this variant and metric on this date
                    conversions = (
                        self.db.query(func.count(Event.id))
                        .filter(
                            Event.experiment_id == experiment.id,
                            Event.variant_id == variant.id,
                            Event.event_type == EventType.CONVERSION.value,
                            Event.event_name == metric.event_name,
                            Event.timestamp >= date_start.isoformat(),
                            Event.timestamp <= date_end.isoformat(),
                        )
                        .scalar()
                        or 0
                    )

                    # Calculate conversion rate
                    assignments = daily_assignments[date][str(variant.id)]
                    rate = (conversions / assignments) * 100 if assignments > 0 else 0

                    variant_result = {
                        "variant_id": str(variant.id),
                        "variant_name": variant.name,
                        "is_control": variant.is_control,
                        "assignments": assignments,
                        "conversions": conversions,
                        "conversion_rate": rate,
                    }

                    metric_result["variants"].append(variant_result)

                date_results["metrics"].append(metric_result)

            results.append(date_results)

        return results

    def _find_best_variant(
        self, variant_results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best performing variant from a list of variant results.

        Args:
            variant_results: List of variant result dictionaries

        Returns:
            Dictionary containing best variant info or None if no clear winner
        """
        # Find control variant
        control = next((v for v in variant_results if v["is_control"]), None)
        if not control:
            return None

        # Find variants with significant improvement over control
        significant_variants = [
            v
            for v in variant_results
            if not v["is_control"]
            and v["is_significant"]
            and v["relative_improvement"] > 0
        ]

        if not significant_variants:
            return None

        # Find variant with highest conversion rate
        best_variant = max(significant_variants, key=lambda v: v["conversion_rate"])

        return {
            "variant_id": best_variant["variant_id"],
            "variant_name": best_variant["variant_name"],
            "improvement": best_variant["relative_improvement"],
            "conversion_rate": best_variant["conversion_rate"],
            "p_value": best_variant["p_value"],
        }

    def get_segmented_results(
        self,
        experiment_id: Union[str, UUID],
        segment_by: str,
        metric_id: Optional[Union[str, UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Get experiment results segmented by a specific property.

        Args:
            experiment_id: ID of the experiment
            segment_by: Property to segment results by (e.g., 'country', 'device')
            metric_id: Optional ID of specific metric to analyze

        Returns:
            Dictionary containing segmented results
        """
        # Get experiment with variants and metrics
        experiment = (
            self.db.query(Experiment)
            .options(joinedload(Experiment.variants), joinedload(Experiment.metrics))
            .filter(Experiment.id == experiment_id)
            .first()
        )

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Filter metrics if metric_id is provided
        metrics = [
            m
            for m in experiment.metrics
            if not metric_id or str(m.id) == str(metric_id)
        ]

        if not metrics:
            return {"segments": []}

        # Get segment values from event properties
        segment_values_query = text(
            f"""
            SELECT DISTINCT jsonb_extract_path_text(properties, :segment_key) as segment_value
            FROM events
            WHERE experiment_id = :experiment_id
            AND properties ? :segment_key
            AND jsonb_extract_path_text(properties, :segment_key) IS NOT NULL
            AND jsonb_extract_path_text(properties, :segment_key) != ''
        """
        )

        segment_values_result = self.db.execute(
            segment_values_query,
            {"segment_key": segment_by, "experiment_id": str(experiment_id)},
        )

        segment_values = [row[0] for row in segment_values_result]

        if not segment_values:
            return {"segments": []}

        # Process each segment
        segments = []
        for segment_value in segment_values:
            segment_result = {"segment_value": segment_value, "metrics": []}

            for metric in metrics:
                metric_result = {
                    "metric_id": str(metric.id),
                    "metric_name": metric.name,
                    "variants": [],
                }

                for variant in experiment.variants:
                    # Get assignments count for this variant in this segment
                    # This is an approximation - ideally would track segment with the assignment
                    segment_assignments_query = text(
                        f"""
                        SELECT COUNT(DISTINCT a.user_id)
                        FROM assignments a
                        JOIN events e ON a.user_id = e.user_id AND a.experiment_id = e.experiment_id
                        WHERE a.experiment_id = :experiment_id
                        AND a.variant_id = :variant_id
                        AND e.properties ? :segment_key
                        AND jsonb_extract_path_text(e.properties, :segment_key) = :segment_value
                    """
                    )

                    assignments = (
                        self.db.execute(
                            segment_assignments_query,
                            {
                                "experiment_id": str(experiment_id),
                                "variant_id": str(variant.id),
                                "segment_key": segment_by,
                                "segment_value": segment_value,
                            },
                        ).scalar()
                        or 0
                    )

                    # Get conversions for this variant and segment
                    segment_conversions_query = text(
                        f"""
                        SELECT COUNT(*)
                        FROM events
                        WHERE experiment_id = :experiment_id
                        AND variant_id = :variant_id
                        AND event_type = :event_type
                        AND event_name = :event_name
                        AND properties ? :segment_key
                        AND jsonb_extract_path_text(properties, :segment_key) = :segment_value
                    """
                    )

                    conversions = (
                        self.db.execute(
                            segment_conversions_query,
                            {
                                "experiment_id": str(experiment_id),
                                "variant_id": str(variant.id),
                                "event_type": EventType.CONVERSION.value,
                                "event_name": metric.event_name,
                                "segment_key": segment_by,
                                "segment_value": segment_value,
                            },
                        ).scalar()
                        or 0
                    )

                    # Calculate conversion rate
                    rate = (conversions / assignments) * 100 if assignments > 0 else 0

                    variant_result = {
                        "variant_id": str(variant.id),
                        "variant_name": variant.name,
                        "is_control": variant.is_control,
                        "sample_size": assignments,
                        "conversions": conversions,
                        "conversion_rate": rate,
                    }

                    metric_result["variants"].append(variant_result)

                segment_result["metrics"].append(metric_result)

            segments.append(segment_result)

        return {"segments": segments}
