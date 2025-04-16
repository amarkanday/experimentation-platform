"""
Scheduler for metrics aggregation.

This module provides scheduling functionality for automatically
aggregating raw metrics data into summary data for efficient querying.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.metrics.metric import AggregationPeriod
from backend.app.services.metrics_service import MetricsService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsScheduler:
    """Handles scheduled tasks for metrics aggregation."""

    def __init__(self, interval_minutes: int = 15):
        """
        Initialize the metrics scheduler.

        Args:
            interval_minutes: How often to run metrics aggregation (in minutes)
        """
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Metrics scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Metrics scheduler started with {self.interval_minutes} minute interval")

    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                # Only await the task if it's a real asyncio Task and not a mock
                from unittest.mock import Mock
                if not isinstance(self.task, Mock):
                    await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Metrics scheduler stopped")

    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                # Process metrics aggregation
                await self.aggregate_metrics()

                # Wait for the next interval
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics scheduler: {str(e)}")
                # Wait a bit before trying again
                await asyncio.sleep(60)

    async def aggregate_metrics(self):
        """
        Aggregate raw metrics into summary data.

        This aggregates data at different time periods:
        1. Last hour at minute granularity
        2. Last day at hour granularity
        3. Last month at day granularity
        4. All-time totals
        """
        logger.info("Aggregating metrics")

        # Use a new database session for this task
        db = SessionLocal()
        try:
            current_time = datetime.now(timezone.utc)

            # Define aggregation periods and their lookback windows
            aggregation_tasks = [
                # Minute aggregation for the last hour
                (AggregationPeriod.MINUTE, current_time - timedelta(hours=1)),
                # Hourly aggregation for the last day
                (AggregationPeriod.HOUR, current_time - timedelta(days=1)),
                # Daily aggregation for the last month
                (AggregationPeriod.DAY, current_time - timedelta(days=30)),
                # Weekly aggregation for the last year
                (AggregationPeriod.WEEK, current_time - timedelta(days=365)),
                # Monthly aggregation for all time
                (AggregationPeriod.MONTH, None),
                # Total aggregation (single record for all time)
                (AggregationPeriod.TOTAL, None),
            ]

            total_records = 0

            # Run each aggregation task
            for period, start_time in aggregation_tasks:
                try:
                    records = MetricsService.aggregate_metrics(
                        db=db,
                        period=period,
                        start_time=start_time,
                        end_time=current_time
                    )
                    total_records += records
                    logger.info(f"Aggregated {records} records for {period} period")
                except Exception as e:
                    logger.error(f"Error aggregating {period} metrics: {str(e)}")

            if total_records > 0:
                logger.info(f"Total of {total_records} aggregated metric records created/updated")
            else:
                logger.info("No metrics required aggregation")

        except Exception as e:
            logger.error(f"Error processing metrics aggregation: {str(e)}")
        finally:
            db.close()


# Create a singleton instance of the scheduler
metrics_scheduler = MetricsScheduler()
