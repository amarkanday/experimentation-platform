# Event tracking service
# backend/app/services/event_service.py
import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.models.event import Event, EventType
from backend.app.models.experiment import Experiment, Variant
from backend.app.models.assignment import Assignment
from backend.app.schemas.tracking import EventCreate
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EventService:
    """
    Service for handling experiment events, tracking and processing.

    This service provides functionalities for:
    - Tracking user interactions with experiments
    - Recording conversion events and metrics
    - Storing event data for analysis
    - Managing event queues and processing
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db

    def track_event(self, event_data: EventCreate) -> Dict[str, Any]:
        """
        Track a new event from a user interaction.

        Args:
            event_data: Event data schema with event details

        Returns:
            Dictionary containing the created event data
        """
        # Convert schema to dict
        event_dict = event_data.dict()

        # Add timestamp if not provided
        if "timestamp" not in event_dict or not event_dict["timestamp"]:
            event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Create event object
        event = Event(**event_dict)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.debug(
            f"Tracked event {event.id} of type {event.event_type} for user {event.user_id}"
        )

        # Return as dict for API response
        return {
            "id": str(event.id),
            "user_id": event.user_id,
            "event_type": event.event_type,
            "event_name": event.event_name,
            "experiment_id": str(event.experiment_id) if event.experiment_id else None,
            "variant_id": str(event.variant_id) if event.variant_id else None,
            "timestamp": event.timestamp,
            "properties": event.properties,
        }

    def track_conversion(
        self,
        user_id: str,
        event_name: str,
        experiment_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Track a conversion event for a specific user and experiment.

        Args:
            user_id: ID of the user who converted
            event_name: Name of the conversion event
            experiment_id: Optional ID of the experiment
            properties: Optional additional event properties

        Returns:
            Dictionary containing the created event data
        """
        # If experiment_id is provided, find the variant the user was assigned to
        variant_id = None
        if experiment_id:
            assignment = (
                self.db.query(Assignment)
                .filter(
                    Assignment.user_id == user_id,
                    Assignment.experiment_id == experiment_id,
                )
                .order_by(desc(Assignment.created_at))
                .first()
            )

            if assignment:
                variant_id = assignment.variant_id

        # Create event data
        event_data = EventCreate(
            user_id=user_id,
            event_type=EventType.CONVERSION.value,
            event_name=event_name,
            experiment_id=experiment_id,
            variant_id=variant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            properties=properties or {},
        )

        # Track the event
        return self.track_event(event_data)

    def track_exposure(
        self,
        user_id: str,
        experiment_id: str,
        variant_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Track an exposure event when a user is exposed to a variant.

        Args:
            user_id: ID of the user who was exposed
            experiment_id: ID of the experiment
            variant_id: ID of the variant the user was exposed to
            properties: Optional additional event properties

        Returns:
            Dictionary containing the created event data
        """
        # Create event data
        event_data = EventCreate(
            user_id=user_id,
            event_type=EventType.EXPOSURE.value,
            event_name="variant_exposure",
            experiment_id=experiment_id,
            variant_id=variant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            properties=properties or {},
        )

        # Track the event
        return self.track_event(event_data)

    def get_events_by_experiment(
        self,
        experiment_id: Union[str, UUID],
        event_type: Optional[str] = None,
        event_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific experiment with filtering options.

        Args:
            experiment_id: ID of the experiment
            event_type: Optional filter by event type
            event_name: Optional filter by event name
            start_date: Optional filter for events after this date
            end_date: Optional filter for events before this date
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of event dictionaries
        """
        # Base query
        query = self.db.query(Event).filter(Event.experiment_id == experiment_id)

        # Apply filters
        if event_type:
            query = query.filter(Event.event_type == event_type)

        if event_name:
            query = query.filter(Event.event_name == event_name)

        if start_date:
            query = query.filter(Event.timestamp >= start_date)

        if end_date:
            query = query.filter(Event.timestamp <= end_date)

        # Apply pagination and get results
        events = query.order_by(desc(Event.timestamp)).offset(skip).limit(limit).all()

        # Convert to dict for API response
        return [
            {
                "id": str(event.id),
                "user_id": event.user_id,
                "event_type": event.event_type,
                "event_name": event.event_name,
                "experiment_id": (
                    str(event.experiment_id) if event.experiment_id else None
                ),
                "variant_id": str(event.variant_id) if event.variant_id else None,
                "timestamp": event.timestamp,
                "properties": event.properties,
            }
            for event in events
        ]

    def count_events_by_experiment(
        self,
        experiment_id: Union[str, UUID],
        event_type: Optional[str] = None,
        event_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        """
        Count events for a specific experiment with filtering options.

        Args:
            experiment_id: ID of the experiment
            event_type: Optional filter by event type
            event_name: Optional filter by event name
            start_date: Optional filter for events after this date
            end_date: Optional filter for events before this date

        Returns:
            Count of matching events
        """
        # Base query
        query = self.db.query(func.count(Event.id)).filter(
            Event.experiment_id == experiment_id
        )

        # Apply filters
        if event_type:
            query = query.filter(Event.event_type == event_type)

        if event_name:
            query = query.filter(Event.event_name == event_name)

        if start_date:
            query = query.filter(Event.timestamp >= start_date)

        if end_date:
            query = query.filter(Event.timestamp <= end_date)

        return query.scalar()

    def get_events_by_user(
        self,
        user_id: str,
        experiment_id: Optional[Union[str, UUID]] = None,
        event_type: Optional[str] = None,
        event_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific user with filtering options.

        Args:
            user_id: ID of the user
            experiment_id: Optional filter by experiment
            event_type: Optional filter by event type
            event_name: Optional filter by event name
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of event dictionaries
        """
        # Base query
        query = self.db.query(Event).filter(Event.user_id == user_id)

        # Apply filters
        if experiment_id:
            query = query.filter(Event.experiment_id == experiment_id)

        if event_type:
            query = query.filter(Event.event_type == event_type)

        if event_name:
            query = query.filter(Event.event_name == event_name)

        # Apply pagination and get results
        events = query.order_by(desc(Event.timestamp)).offset(skip).limit(limit).all()

        # Convert to dict for API response
        return [
            {
                "id": str(event.id),
                "user_id": event.user_id,
                "event_type": event.event_type,
                "event_name": event.event_name,
                "experiment_id": (
                    str(event.experiment_id) if event.experiment_id else None
                ),
                "variant_id": str(event.variant_id) if event.variant_id else None,
                "timestamp": event.timestamp,
                "properties": event.properties,
            }
            for event in events
        ]

    def batch_track_events(self, events: List[EventCreate]) -> int:
        """
        Track multiple events in a batch operation.

        Args:
            events: List of event data schemas

        Returns:
            Number of events successfully tracked
        """
        if not events:
            return 0

        # Process each event
        count = 0
        for event_data in events:
            try:
                # Convert schema to dict
                event_dict = event_data.dict()

                # Add timestamp if not provided
                if "timestamp" not in event_dict or not event_dict["timestamp"]:
                    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

                # Create event object
                event = Event(**event_dict)
                self.db.add(event)
                count += 1
            except Exception as e:
                logger.error(f"Error tracking event in batch: {str(e)}")
                # Continue processing other events
                continue

        # Commit all events in a single transaction
        self.db.commit()

        logger.info(f"Batch tracked {count} events")
        return count

    def delete_events_by_experiment(self, experiment_id: Union[str, UUID]) -> int:
        """
        Delete all events associated with an experiment.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Number of events deleted
        """
        # Count events before deletion for return value
        count_query = self.db.query(func.count(Event.id)).filter(
            Event.experiment_id == experiment_id
        )
        count = count_query.scalar() or 0

        # Delete events
        delete_query = self.db.query(Event).filter(Event.experiment_id == experiment_id)
        delete_query.delete(synchronize_session=False)

        self.db.commit()

        logger.info(f"Deleted {count} events for experiment {experiment_id}")
        return count

    def purge_old_events(self, days_to_keep: int = 90) -> int:
        """
        Purge events older than a specified number of days.

        Args:
            days_to_keep: Number of days of events to retain

        Returns:
            Number of events deleted
        """
        # Calculate cutoff date
        cutoff_date = (
            datetime.now(timezone.utc) - timezone.timedelta(days=days_to_keep)
        ).isoformat()

        # Count events before deletion for return value
        count_query = self.db.query(func.count(Event.id)).filter(
            Event.timestamp < cutoff_date
        )
        count = count_query.scalar() or 0

        # Delete events
        delete_query = self.db.query(Event).filter(Event.timestamp < cutoff_date)
        delete_query.delete(synchronize_session=False)

        self.db.commit()

        logger.info(f"Purged {count} events older than {days_to_keep} days")
        return count
