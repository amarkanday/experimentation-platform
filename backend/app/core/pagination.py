"""
Pagination utilities for API endpoints.

This module provides a Paginator class to handle pagination in API responses.
"""
from typing import Dict, Any, List, TypeVar, Generic, Optional

T = TypeVar('T')


class Paginator(Generic[T]):
    """
    A utility class for handling pagination in API endpoints.

    This class provides methods for paginating database queries and
    generating standardized response structures for paginated data.
    """

    def __init__(self, skip: int = 0, limit: int = 100):
        """
        Initialize the paginator with skip and limit parameters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        """
        self.skip = max(0, skip)
        self.limit = max(1, min(limit, 500))  # Ensure limit is between 1 and 500

    def get_pagination_params(self) -> Dict[str, int]:
        """
        Get the pagination parameters as a dictionary.

        Returns:
            Dict with skip and limit parameters
        """
        return {
            "skip": self.skip,
            "limit": self.limit
        }

    def paginate_query(self, query: Any) -> Any:
        """
        Apply pagination to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object

        Returns:
            Query with pagination applied
        """
        return query.offset(self.skip).limit(self.limit)

    def get_paginated_response(self, items: List[T], total: int) -> Dict[str, Any]:
        """
        Create a standardized paginated response.

        Args:
            items: List of items for current page
            total: Total number of items across all pages

        Returns:
            Dict with items, total count, and pagination parameters
        """
        return {
            "items": items,
            "total": total,
            "skip": self.skip,
            "limit": self.limit
        }

    @classmethod
    def from_request(cls, skip: Optional[int] = 0, limit: Optional[int] = 100) -> 'Paginator':
        """
        Create a Paginator instance from request query parameters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Paginator instance
        """
        return cls(skip=skip or 0, limit=limit or 100)
