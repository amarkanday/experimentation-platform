"""
Scheduler for background tasks.

This module provides scheduling functionality for recurring tasks
such as experiment status updates based on scheduled dates.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.app.db.session import SessionLocal
from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

class ExperimentScheduler:
    """Handles scheduled tasks for experiments."""

    def __init__(self, interval_minutes: int = 15):
        """
        Initialize the experiment scheduler.

        Args:
            interval_minutes: How often to check for experiments that need to be updated (in minutes)
        """
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Experiment scheduler started with {self.interval_minutes} minute interval")

    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Experiment scheduler stopped")

    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                # Process experiments that need status updates
                await self.process_scheduled_experiments()

                # Wait for the next interval
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in experiment scheduler: {str(e)}")
                # Wait a bit before trying again
                await asyncio.sleep(60)

    async def process_scheduled_experiments(self):
        """
        Process experiments that need status updates based on their scheduled dates.

        This checks for:
        1. Experiments in DRAFT or PAUSED status that should be activated
        2. Experiments in ACTIVE status that should be completed
        """
        logger.info("Processing scheduled experiments")

        # Use a new database session for this task
        db = SessionLocal()
        try:
            current_time = datetime.now(timezone.utc)

            # Find experiments to activate (start_date has passed)
            experiments_to_activate = db.query(Experiment).filter(
                and_(
                    Experiment.status.in_([ExperimentStatus.DRAFT, ExperimentStatus.PAUSED]),
                    Experiment.start_date.isnot(None),
                    Experiment.start_date <= current_time
                )
            ).all()

            # Activate experiments
            activated_count = 0
            for experiment in experiments_to_activate:
                try:
                    experiment.status = ExperimentStatus.ACTIVE
                    experiment.updated_at = current_time
                    db.add(experiment)
                    activated_count += 1
                    logger.info(
                        f"Activating experiment: {experiment.id} - {experiment.name} "
                        f"(scheduled start: {experiment.start_date})"
                    )
                except Exception as e:
                    logger.error(f"Error activating experiment {experiment.id}: {str(e)}")

            # Commit all activation changes before checking for experiments to complete
            if activated_count > 0:
                db.commit()

            # Find experiments to complete (end_date has passed)
            experiments_to_complete = db.query(Experiment).filter(
                and_(
                    Experiment.status == ExperimentStatus.ACTIVE,
                    Experiment.end_date.isnot(None),
                    Experiment.end_date <= current_time
                )
            ).all()

            # Complete experiments
            completed_count = 0
            for experiment in experiments_to_complete:
                try:
                    experiment.status = ExperimentStatus.COMPLETED
                    experiment.updated_at = current_time
                    db.add(experiment)
                    completed_count += 1
                    logger.info(
                        f"Completing experiment: {experiment.id} - {experiment.name} "
                        f"(scheduled end: {experiment.end_date})"
                    )
                except Exception as e:
                    logger.error(f"Error completing experiment {experiment.id}: {str(e)}")

            # Commit completion changes
            if completed_count > 0:
                db.commit()

            # Log the results
            if activated_count > 0 or completed_count > 0:
                logger.info(f"Updated {activated_count} experiments to ACTIVE and {completed_count} to COMPLETED")
            else:
                logger.info("No experiments required scheduling updates")

        except Exception as e:
            logger.error(f"Error processing scheduled experiments: {str(e)}")
        finally:
            db.close()

# Create a singleton instance of the scheduler
experiment_scheduler = ExperimentScheduler()
