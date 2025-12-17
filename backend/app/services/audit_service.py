"""
Audit Service for comprehensive logging of user actions.

This service provides functionality to log all user actions and changes
in the experimentation platform, creating a comprehensive audit trail
for compliance, debugging, and analysis purposes.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from backend.app.models.audit_log import AuditLog, ActionType, EntityType
from backend.app.models.user import User


logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    async def log_toggle_operation(
        db: Session,
        user_id: UUID,
        user_email: str,
        action_type: str,
        entity_id: UUID,
        entity_name: str,
        old_value: str,
        new_value: str,
        reason: Optional[str] = None,
    ) -> UUID:
        """
        Log a feature flag toggle operation asynchronously.

        Args:
            db: Database session
            user_id: ID of the user performing the action
            user_email: Email of the user performing the action
            action_type: Type of action (e.g., "toggle_enable", "toggle_disable")
            entity_id: ID of the entity being modified
            entity_name: Name of the entity being modified
            old_value: Previous value/status
            new_value: New value/status
            reason: Optional reason for the action

        Returns:
            UUID: ID of the created audit log entry

        Raises:
            Exception: If logging fails
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action_type=action_type,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=entity_id,
                entity_name=entity_name,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                timestamp=datetime.now(timezone.utc),
            )

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            logger.info(
                f"Audit log created: {action_type} on {entity_name} "
                f"by {user_email} ({old_value} -> {new_value})"
            )

            return audit_log.id

        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    async def log_action(
        db: Session,
        user_id: Optional[UUID],
        user_email: str,
        action_type: ActionType,
        entity_type: EntityType,
        entity_id: UUID,
        entity_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> UUID:
        """
        Log any user action asynchronously.

        Args:
            db: Database session
            user_id: ID of the user performing the action (None for system actions)
            user_email: Email of the user performing the action
            action_type: Type of action being performed
            entity_type: Type of entity being modified
            entity_id: ID of the entity being modified
            entity_name: Name of the entity being modified
            old_value: Previous value/status (optional)
            new_value: New value/status (optional)
            reason: Optional reason for the action

        Returns:
            UUID: ID of the created audit log entry

        Raises:
            Exception: If logging fails
        """
        try:
            # Run in background to avoid blocking the main operation
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                AuditService._create_audit_log_sync,
                db,
                user_id,
                user_email,
                action_type,
                entity_type,
                entity_id,
                entity_name,
                old_value,
                new_value,
                reason,
            )

        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Don't re-raise to avoid breaking the main operation
            return None

    @staticmethod
    def _create_audit_log_sync(
        db: Session,
        user_id: Optional[UUID],
        user_email: str,
        action_type: ActionType,
        entity_type: EntityType,
        entity_id: UUID,
        entity_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> UUID:
        """Synchronous audit log creation for use with executor."""
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        logger.info(
            f"Audit log created: {action_type.value} on {entity_name} "
            f"by {user_email} ({old_value} -> {new_value})"
        )

        return audit_log.id

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[UUID] = None,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[UUID] = None,
        action_type: Optional[ActionType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """
        Retrieve audit logs with filtering and pagination.

        Args:
            db: Database session
            user_id: Filter by user ID (optional)
            entity_type: Filter by entity type (optional)
            entity_id: Filter by entity ID (optional)
            action_type: Filter by action type (optional)
            from_date: Filter logs from this date (optional)
            to_date: Filter logs until this date (optional)
            page: Page number (1-based)
            limit: Number of records per page

        Returns:
            Tuple[List[AuditLog], int]: List of audit logs and total count

        Raises:
            ValueError: If pagination parameters are invalid
        """
        if page < 1:
            raise ValueError("Page number must be 1 or greater")
        if limit < 1 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")

        # Build query with filters
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type.value)

        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)

        if action_type:
            query = query.filter(AuditLog.action_type == action_type.value)

        if from_date:
            query = query.filter(AuditLog.timestamp >= from_date)

        if to_date:
            query = query.filter(AuditLog.timestamp <= to_date)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and ordering
        offset = (page - 1) * limit
        audit_logs = (
            query.order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )

        logger.info(
            f"Retrieved {len(audit_logs)} audit logs (page {page}, "
            f"limit {limit}, total {total_count})"
        )

        return audit_logs, total_count

    @staticmethod
    def get_entity_audit_history(
        db: Session,
        entity_type: EntityType,
        entity_id: UUID,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit history for a specific entity.

        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: ID of the entity
            limit: Maximum number of records to return

        Returns:
            List[AuditLog]: List of audit logs for the entity
        """
        audit_logs = (
            db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.entity_type == entity_type.value,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

        logger.info(
            f"Retrieved {len(audit_logs)} audit logs for {entity_type.value} {entity_id}"
        )

        return audit_logs

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user's activity.

        Args:
            db: Database session
            user_id: ID of the user
            from_date: Filter logs from this date (optional)
            to_date: Filter logs until this date (optional)
            limit: Maximum number of records to return

        Returns:
            List[AuditLog]: List of audit logs for the user
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if from_date:
            query = query.filter(AuditLog.timestamp >= from_date)

        if to_date:
            query = query.filter(AuditLog.timestamp <= to_date)

        audit_logs = (
            query.order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

        logger.info(
            f"Retrieved {len(audit_logs)} audit logs for user {user_id}"
        )

        return audit_logs

    @staticmethod
    def get_audit_stats(
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Args:
            db: Database session
            from_date: Filter logs from this date (optional)
            to_date: Filter logs until this date (optional)

        Returns:
            Dict[str, Any]: Statistics about audit logs
        """
        query = db.query(AuditLog)

        if from_date:
            query = query.filter(AuditLog.timestamp >= from_date)

        if to_date:
            query = query.filter(AuditLog.timestamp <= to_date)

        # Total count
        total_logs = query.count()

        # Count by action type
        action_counts = (
            query.with_entities(AuditLog.action_type, func.count(AuditLog.id))
            .group_by(AuditLog.action_type)
            .all()
        )

        # Count by entity type
        entity_counts = (
            query.with_entities(AuditLog.entity_type, func.count(AuditLog.id))
            .group_by(AuditLog.entity_type)
            .all()
        )

        # Most active users
        user_counts = (
            query.with_entities(AuditLog.user_email, func.count(AuditLog.id))
            .group_by(AuditLog.user_email)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(10)
            .all()
        )

        return {
            "total_logs": total_logs,
            "action_counts": dict(action_counts),
            "entity_counts": dict(entity_counts),
            "most_active_users": dict(user_counts),
            "date_range": {
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
            },
        }