"""
Test cases for time_window operator in rules engine.

Tests time-based targeting functionality for temporal rules.
"""

import pytest
from datetime import datetime, time, timezone
from backend.app.core.rules_engine import apply_operator
from backend.app.schemas.targeting_rule import OperatorType


class TestTimeWindowDayOfWeek:
    """Test time window with day of week targeting."""

    def test_single_day_match(self):
        """Test matching a single day of the week."""
        # Monday = 0, Tuesday = 1, ..., Sunday = 6
        monday = datetime(2024, 1, 1, 10, 0, 0)  # Monday, Jan 1, 2024

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            monday,
            {"days": [0]}  # Monday only
        )
        assert result is True

    def test_single_day_no_match(self):
        """Test not matching a day of the week."""
        monday = datetime(2024, 1, 1, 10, 0, 0)  # Monday

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            monday,
            {"days": [2]}  # Wednesday only
        )
        assert result is False

    def test_multiple_days_match(self):
        """Test matching multiple days (weekdays)."""
        tuesday = datetime(2024, 1, 2, 10, 0, 0)  # Tuesday

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            tuesday,
            {"days": [0, 1, 2, 3, 4]}  # Monday-Friday
        )
        assert result is True

    def test_weekend_match(self):
        """Test matching weekend days."""
        saturday = datetime(2024, 1, 6, 10, 0, 0)  # Saturday

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            saturday,
            {"days": [5, 6]}  # Saturday-Sunday
        )
        assert result is True

    def test_weekend_no_match(self):
        """Test weekday not matching weekend window."""
        monday = datetime(2024, 1, 1, 10, 0, 0)  # Monday

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            monday,
            {"days": [5, 6]}  # Saturday-Sunday
        )
        assert result is False


class TestTimeWindowTimeOfDay:
    """Test time window with time of day targeting."""

    def test_time_range_match(self):
        """Test matching time within range."""
        morning = datetime(2024, 1, 1, 10, 30, 0)  # 10:30 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            morning,
            {"start_time": "09:00", "end_time": "17:00"}  # 9 AM - 5 PM
        )
        assert result is True

    def test_time_range_no_match_before(self):
        """Test time before range."""
        early = datetime(2024, 1, 1, 7, 0, 0)  # 7:00 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            early,
            {"start_time": "09:00", "end_time": "17:00"}
        )
        assert result is False

    def test_time_range_no_match_after(self):
        """Test time after range."""
        late = datetime(2024, 1, 1, 19, 0, 0)  # 7:00 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            late,
            {"start_time": "09:00", "end_time": "17:00"}
        )
        assert result is False

    def test_time_range_exact_start(self):
        """Test time exactly at start of range (inclusive)."""
        exact_start = datetime(2024, 1, 1, 9, 0, 0)  # 9:00 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            exact_start,
            {"start_time": "09:00", "end_time": "17:00"}
        )
        assert result is True

    def test_time_range_exact_end(self):
        """Test time exactly at end of range (inclusive)."""
        exact_end = datetime(2024, 1, 1, 17, 0, 0)  # 5:00 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            exact_end,
            {"start_time": "09:00", "end_time": "17:00"}
        )
        assert result is True

    def test_overnight_time_range(self):
        """Test time range that crosses midnight."""
        evening = datetime(2024, 1, 1, 23, 0, 0)  # 11:00 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            evening,
            {"start_time": "22:00", "end_time": "02:00"}  # 10 PM - 2 AM
        )
        assert result is True

    def test_overnight_time_range_morning(self):
        """Test morning time in overnight range."""
        early_morning = datetime(2024, 1, 1, 1, 0, 0)  # 1:00 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            early_morning,
            {"start_time": "22:00", "end_time": "02:00"}
        )
        assert result is True

    def test_overnight_time_range_no_match(self):
        """Test time not in overnight range."""
        afternoon = datetime(2024, 1, 1, 14, 0, 0)  # 2:00 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            afternoon,
            {"start_time": "22:00", "end_time": "02:00"}
        )
        assert result is False


class TestTimeWindowDateRange:
    """Test time window with date range targeting."""

    def test_date_range_match(self):
        """Test date within range."""
        mid_date = datetime(2024, 6, 15, 10, 0, 0)  # Mid-year

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            mid_date,
            {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert result is True

    def test_date_range_no_match_before(self):
        """Test date before range."""
        early_date = datetime(2023, 12, 31, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            early_date,
            {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert result is False

    def test_date_range_no_match_after(self):
        """Test date after range."""
        late_date = datetime(2025, 1, 1, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            late_date,
            {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert result is False

    def test_date_range_exact_start(self):
        """Test date exactly at start (inclusive)."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            start_date,
            {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert result is True

    def test_date_range_exact_end(self):
        """Test date exactly at end (inclusive)."""
        end_date = datetime(2024, 12, 31, 23, 59, 59)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            end_date,
            {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        assert result is True


class TestTimeWindowCombined:
    """Test time window with combined day and time targeting."""

    def test_weekday_business_hours_match(self):
        """Test matching weekday during business hours."""
        tuesday_morning = datetime(2024, 1, 2, 10, 0, 0)  # Tuesday 10 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            tuesday_morning,
            {
                "days": [0, 1, 2, 3, 4],  # Monday-Friday
                "start_time": "09:00",
                "end_time": "17:00"
            }
        )
        assert result is True

    def test_weekday_outside_business_hours(self):
        """Test weekday outside business hours."""
        tuesday_evening = datetime(2024, 1, 2, 20, 0, 0)  # Tuesday 8 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            tuesday_evening,
            {
                "days": [0, 1, 2, 3, 4],
                "start_time": "09:00",
                "end_time": "17:00"
            }
        )
        assert result is False

    def test_weekend_during_business_hours(self):
        """Test weekend during business hours time."""
        saturday_morning = datetime(2024, 1, 6, 10, 0, 0)  # Saturday 10 AM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            saturday_morning,
            {
                "days": [0, 1, 2, 3, 4],  # Monday-Friday only
                "start_time": "09:00",
                "end_time": "17:00"
            }
        )
        assert result is False

    def test_date_and_time_range_match(self):
        """Test matching specific date range with time window."""
        holiday_afternoon = datetime(2024, 12, 25, 14, 0, 0)  # Christmas 2 PM

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            holiday_afternoon,
            {
                "start_date": "2024-12-20",
                "end_date": "2024-12-31",
                "start_time": "10:00",
                "end_time": "18:00"
            }
        )
        assert result is True


class TestTimeWindowTimezone:
    """Test time window with timezone support."""

    def test_timezone_aware_match(self):
        """Test matching with timezone-aware datetime."""
        utc_time = datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc)  # 3 PM UTC

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            utc_time,
            {
                "start_time": "14:00",
                "end_time": "16:00",
                "timezone": "UTC"
            }
        )
        assert result is True

    def test_timezone_conversion(self):
        """Test timezone conversion in comparison."""
        # 10 AM PST = 6 PM UTC
        pst_time = datetime(2024, 1, 1, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            pst_time,
            {
                "start_time": "09:00",
                "end_time": "17:00",
                "timezone": "America/Los_Angeles"
            }
        )
        assert result is True


class TestTimeWindowFormats:
    """Test different input format handling."""

    def test_iso_string_input(self):
        """Test ISO format string as input."""
        result = apply_operator(
            OperatorType.TIME_WINDOW,
            "2024-01-02T10:00:00",  # Tuesday 10 AM
            {
                "days": [1],  # Tuesday
                "start_time": "09:00",
                "end_time": "17:00"
            }
        )
        assert result is True

    def test_timestamp_input(self):
        """Test Unix timestamp as input."""
        # 2024-01-02 10:00:00 UTC
        timestamp = 1704189600

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            timestamp,
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )
        assert result is True

    def test_current_time_default(self):
        """Test using current time when no value provided."""
        # This will use datetime.now() internally
        result = apply_operator(
            OperatorType.TIME_WINDOW,
            None,  # Should default to current time
            {
                "days": list(range(7))  # All days
            }
        )
        assert result is True


class TestTimeWindowInvalidInputs:
    """Test time window operator with invalid inputs."""

    def test_invalid_day_range(self):
        """Test invalid day number (must be 0-6)."""
        monday = datetime(2024, 1, 1, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            monday,
            {"days": [7, 8]}  # Invalid day numbers
        )
        assert result is False

    def test_invalid_time_format(self):
        """Test invalid time format."""
        morning = datetime(2024, 1, 1, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            morning,
            {"start_time": "9am", "end_time": "5pm"}  # Invalid format
        )
        assert result is False

    def test_invalid_date_format(self):
        """Test invalid date format."""
        mid_date = datetime(2024, 6, 15, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            mid_date,
            {"start_date": "January 1, 2024", "end_date": "December 31, 2024"}
        )
        assert result is False

    def test_end_before_start_time(self):
        """Test end time before start time (should be treated as overnight)."""
        # This should NOT be an error - it's a valid overnight window
        evening = datetime(2024, 1, 1, 23, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            evening,
            {"start_time": "22:00", "end_time": "02:00"}  # Overnight window
        )
        assert result is True

    def test_end_before_start_date(self):
        """Test end date before start date (should be invalid)."""
        mid_date = datetime(2024, 6, 15, 10, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            mid_date,
            {"start_date": "2024-12-31", "end_date": "2024-01-01"}
        )
        assert result is False

    def test_missing_both_time_bounds(self):
        """Test missing both start and end time."""
        morning = datetime(2024, 1, 1, 10, 0, 0)

        # Should match if only days specified (no time restriction)
        result = apply_operator(
            OperatorType.TIME_WINDOW,
            morning,
            {"days": [0]}  # Monday, no time bounds
        )
        assert result is True

    def test_empty_window_config(self):
        """Test empty window configuration."""
        morning = datetime(2024, 1, 1, 10, 0, 0)

        # Empty config should match everything
        result = apply_operator(
            OperatorType.TIME_WINDOW,
            morning,
            {}
        )
        assert result is True

    def test_invalid_actual_value_string(self):
        """Test invalid actual value (not a valid datetime string)."""
        result = apply_operator(
            OperatorType.TIME_WINDOW,
            "not a date",
            {"days": [0]}
        )
        assert result is False

    def test_invalid_timezone(self):
        """Test invalid timezone name."""
        utc_time = datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            utc_time,
            {
                "start_time": "14:00",
                "end_time": "16:00",
                "timezone": "Invalid/Timezone"
            }
        )
        assert result is False


class TestTimeWindowEdgeCases:
    """Test edge cases for time window operator."""

    def test_leap_year_date(self):
        """Test leap year date (Feb 29)."""
        leap_day = datetime(2024, 2, 29, 10, 0, 0)  # 2024 is a leap year

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            leap_day,
            {"start_date": "2024-02-01", "end_date": "2024-03-01"}
        )
        assert result is True

    def test_midnight_boundary(self):
        """Test exactly at midnight."""
        midnight = datetime(2024, 1, 1, 0, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            midnight,
            {"start_time": "00:00", "end_time": "23:59"}
        )
        assert result is True

    def test_end_of_day(self):
        """Test end of day (23:59:59)."""
        end_of_day = datetime(2024, 1, 1, 23, 59, 59)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            end_of_day,
            {"start_time": "00:00", "end_time": "23:59"}
        )
        assert result is True

    def test_new_year_boundary(self):
        """Test New Year's Eve to New Year's Day."""
        new_years_eve = datetime(2023, 12, 31, 23, 0, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            new_years_eve,
            {"start_date": "2023-12-01", "end_date": "2024-01-31"}
        )
        assert result is True

    def test_all_days_all_times(self):
        """Test configuration that matches all times."""
        any_time = datetime(2024, 6, 15, 14, 30, 0)

        result = apply_operator(
            OperatorType.TIME_WINDOW,
            any_time,
            {
                "days": list(range(7)),  # All days
                "start_time": "00:00",
                "end_time": "23:59"
            }
        )
        assert result is True
