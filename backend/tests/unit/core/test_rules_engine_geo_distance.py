"""
Test cases for geo_distance operator in rules engine.

Tests geographic distance calculation functionality for location-based targeting.
"""

import pytest
from backend.app.core.rules_engine import apply_operator
from backend.app.schemas.targeting_rule import OperatorType


class TestGeoDistanceWithinRadius:
    """Test geo distance within radius operator."""

    def test_within_radius_miles(self):
        """Test that location is within specified radius in miles."""
        # San Francisco to Oakland (~12 miles)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},  # San Francisco
            {"lat": 37.8044, "lon": -122.2712, "radius": 15, "unit": "miles"}
        )
        assert result is True

    def test_within_radius_kilometers(self):
        """Test that location is within specified radius in kilometers."""
        # Paris to Versailles (~20 km)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 48.8566, "lon": 2.3522},  # Paris
            {"lat": 48.8049, "lon": 2.1204, "radius": 25, "unit": "km"}
        )
        assert result is True

    def test_not_within_radius(self):
        """Test that location is not within specified radius."""
        # San Francisco to Los Angeles (~380 miles)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},  # San Francisco
            {"lat": 34.0522, "lon": -118.2437, "radius": 100, "unit": "miles"}
        )
        assert result is False

    def test_exactly_on_radius_boundary(self):
        """Test location exactly on radius boundary (should be included)."""
        # This tests the edge case where distance == radius
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 0, "unit": "miles"}
        )
        assert result is True  # Same location, distance = 0

    def test_default_unit_kilometers(self):
        """Test that default unit is kilometers when not specified."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 48.8566, "lon": 2.3522},  # Paris
            {"lat": 48.8049, "lon": 2.1204, "radius": 25}  # No unit specified
        )
        assert result is True  # Default should be km


class TestGeoDistanceComparisons:
    """Test geo distance with different comparison operators."""

    def test_greater_than_distance(self):
        """Test that location is greater than specified distance."""
        # San Francisco to Los Angeles (~380 miles)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 34.0522, "lon": -118.2437, "radius": 100, "unit": "miles", "comparison": "gt"}
        )
        assert result is True

    def test_less_than_distance(self):
        """Test that location is less than specified distance."""
        # San Francisco to Oakland (~12 miles)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.8044, "lon": -122.2712, "radius": 50, "unit": "miles", "comparison": "lt"}
        )
        assert result is True

    def test_not_less_than_when_greater(self):
        """Test that greater distance is not less than."""
        # San Francisco to Los Angeles (~380 miles)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 34.0522, "lon": -118.2437, "radius": 100, "unit": "miles", "comparison": "lt"}
        )
        assert result is False


class TestGeoDistanceFormats:
    """Test different coordinate format inputs."""

    def test_latitude_longitude_keys(self):
        """Test using 'latitude' and 'longitude' keys."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"latitude": 37.7749, "longitude": -122.4194},
            {"latitude": 37.8044, "longitude": -122.2712, "radius": 15, "unit": "miles"}
        )
        assert result is True

    def test_mixed_key_formats(self):
        """Test mixing lat/lon with latitude/longitude."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"latitude": 37.8044, "longitude": -122.2712, "radius": 15, "unit": "miles"}
        )
        assert result is True

    def test_array_format(self):
        """Test using [lat, lon] array format."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            [37.7749, -122.4194],  # [lat, lon]
            {"lat": 37.8044, "lon": -122.2712, "radius": 15, "unit": "miles"}
        )
        assert result is True

    def test_string_coordinates(self):
        """Test that string coordinates are converted to floats."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": "37.7749", "lon": "-122.4194"},
            {"lat": "37.8044", "lon": "-122.2712", "radius": 15, "unit": "miles"}
        )
        assert result is True


class TestGeoDistanceUnits:
    """Test different distance units."""

    def test_miles_unit(self):
        """Test distance calculation with miles."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.8044, "lon": -122.2712, "radius": 15, "unit": "miles"}
        )
        assert result is True

    def test_kilometers_unit(self):
        """Test distance calculation with kilometers."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.8044, "lon": -122.2712, "radius": 24, "unit": "km"}
        )
        assert result is True

    def test_meters_unit(self):
        """Test distance calculation with meters."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7750, "lon": -122.4195, "radius": 200, "unit": "meters"}
        )
        assert result is True

    def test_case_insensitive_units(self):
        """Test that units are case-insensitive."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.8044, "lon": -122.2712, "radius": 15, "unit": "MILES"}
        )
        assert result is True


class TestGeoDistanceEdgeCases:
    """Test edge cases for geo distance operator."""

    def test_same_location(self):
        """Test distance between same location (should be 0)."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 1, "unit": "miles"}
        )
        assert result is True

    def test_north_pole(self):
        """Test coordinates at North Pole."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 90.0, "lon": 0.0},
            {"lat": 89.0, "lon": 0.0, "radius": 200, "unit": "km"}
        )
        assert result is True

    def test_south_pole(self):
        """Test coordinates at South Pole."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": -90.0, "lon": 0.0},
            {"lat": -89.0, "lon": 0.0, "radius": 200, "unit": "km"}
        )
        assert result is True

    def test_antimeridian_crossing(self):
        """Test distance calculation crossing the antimeridian (180°/-180°)."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 0.0, "lon": 179.0},
            {"lat": 0.0, "lon": -179.0, "radius": 500, "unit": "km"}
        )
        assert result is True

    def test_equator_crossing(self):
        """Test distance calculation crossing the equator."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 1.0, "lon": 0.0},
            {"lat": -1.0, "lon": 0.0, "radius": 300, "unit": "km"}
        )
        assert result is True

    def test_very_large_radius(self):
        """Test with very large radius (whole earth)."""
        # Earth's circumference is ~40,075 km
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": -33.8688, "lon": 151.2093, "radius": 50000, "unit": "km"}  # SF to Sydney
        )
        assert result is True


class TestGeoDistanceInvalidInputs:
    """Test geo distance operator with invalid inputs."""

    def test_invalid_actual_value_none(self):
        """Test handling of None actual value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            None,
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_invalid_actual_value_string(self):
        """Test handling of string actual value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            "not a location",
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_missing_latitude_in_actual(self):
        """Test handling of missing latitude in actual value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_missing_longitude_in_actual(self):
        """Test handling of missing longitude in actual value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_missing_latitude_in_expected(self):
        """Test handling of missing latitude in expected value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_missing_longitude_in_expected(self):
        """Test handling of missing longitude in expected value."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_missing_radius(self):
        """Test handling of missing radius."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "unit": "miles"}
        )
        assert result is False

    def test_invalid_latitude_range(self):
        """Test handling of latitude outside valid range (-90 to 90)."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 100.0, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_invalid_longitude_range(self):
        """Test handling of longitude outside valid range (-180 to 180)."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": 200.0},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_invalid_radius_negative(self):
        """Test handling of negative radius."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": -10, "unit": "miles"}
        )
        assert result is False

    def test_invalid_unit(self):
        """Test handling of invalid unit."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "lightyears"}
        )
        assert result is False

    def test_non_numeric_coordinates(self):
        """Test handling of non-numeric coordinates."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": "not a number", "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": 10, "unit": "miles"}
        )
        assert result is False

    def test_non_numeric_radius(self):
        """Test handling of non-numeric radius."""
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 37.7749, "lon": -122.4194},
            {"lat": 37.7749, "lon": -122.4194, "radius": "ten", "unit": "miles"}
        )
        assert result is False


class TestGeoDistanceHaversineAccuracy:
    """Test accuracy of Haversine formula implementation."""

    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (< 10 km)."""
        # Known distance: ~1 km
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 40.7128, "lon": -74.0060},  # New York
            {"lat": 40.7200, "lon": -74.0060, "radius": 1.5, "unit": "km"}
        )
        assert result is True

    def test_medium_distance_accuracy(self):
        """Test accuracy for medium distances (10-1000 km)."""
        # New York to Boston (~300 km)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 40.7128, "lon": -74.0060},  # New York
            {"lat": 42.3601, "lon": -71.0589, "radius": 350, "unit": "km"}
        )
        assert result is True

    def test_long_distance_accuracy(self):
        """Test accuracy for long distances (> 1000 km)."""
        # New York to London (~5,570 km)
        result = apply_operator(
            OperatorType.GEO_DISTANCE,
            {"lat": 40.7128, "lon": -74.0060},  # New York
            {"lat": 51.5074, "lon": -0.1278, "radius": 6000, "unit": "km"}
        )
        assert result is True
