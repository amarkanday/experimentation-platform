"""
Unit tests for the metrics collection utility functions.

These tests verify that performance metrics collection works correctly.
"""

import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from backend.app.utils.metrics import get_memory_usage, get_cpu_usage, MetricsCollector


class TestMetricsFunctions:
    """Tests for individual metrics functions."""

    @patch("psutil.Process")
    def test_get_memory_usage(self, mock_process):
        """Test memory usage collection."""
        # Setup mock
        mock_instance = MagicMock()
        mock_process.return_value = mock_instance

        # Mock memory info
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024  # 100 MB
        mock_mem_info.vms = 200 * 1024 * 1024  # 200 MB
        mock_instance.memory_info.return_value = mock_mem_info
        mock_instance.memory_percent.return_value = 5.5

        # Call function
        result = get_memory_usage()

        # Check results
        assert "rss_mb" in result
        assert "vms_mb" in result
        assert "percent" in result
        assert result["rss_mb"] == 100.0
        assert result["vms_mb"] == 200.0
        assert result["percent"] == 5.5

    @patch("psutil.Process")
    def test_get_memory_usage_fallback(self, mock_process):
        """Test memory usage fallback when psutil fails."""
        # Make psutil raise an exception
        mock_process.side_effect = Exception("Psutil error")

        # Mock resource module
        with patch("resource.getrusage") as mock_getrusage:
            mock_usage = MagicMock()
            mock_usage.ru_maxrss = 150 * 1024  # 150 MB (in KB)
            mock_getrusage.return_value = mock_usage

            # Call function
            result = get_memory_usage()

            # Check results
            assert "rss_mb" in result
            assert result["rss_mb"] == 150.0
            assert result["vms_mb"] == 0
            assert result["percent"] == 0

    @patch("psutil.Process")
    def test_get_cpu_usage(self, mock_process):
        """Test CPU usage collection."""
        # Setup mock
        mock_instance = MagicMock()
        mock_process.return_value = mock_instance
        mock_instance.cpu_percent.return_value = 12.5

        # Call function
        result = get_cpu_usage()

        # Check result
        assert result == 12.5

    @patch("psutil.Process")
    def test_get_cpu_usage_error(self, mock_process):
        """Test CPU usage when psutil fails."""
        # Make psutil raise an exception
        mock_process.side_effect = Exception("Psutil error")

        # Call function
        result = get_cpu_usage()

        # Should return 0 on error
        assert result == 0.0


class TestMetricsCollector:
    """Tests for the MetricsCollector class."""

    @patch("backend.app.utils.metrics.get_memory_usage")
    @patch("backend.app.utils.metrics.get_cpu_usage")
    def test_metrics_collection(self, mock_cpu, mock_memory):
        """Test basic metrics collection functionality."""
        # Setup mocks
        memory_start = {"rss_mb": 100.0, "vms_mb": 200.0, "percent": 5.0}
        memory_end = {"rss_mb": 110.0, "vms_mb": 210.0, "percent": 5.5}

        mock_memory.side_effect = [memory_start, memory_end]
        mock_cpu.return_value = 15.0

        # Create collector and start/stop
        collector = MetricsCollector()
        collector.start()

        # Add some CPU samples directly (bypassing the sampling thread)
        collector._cpu_samples = [10.0, 15.0, 20.0]

        # Stop collection
        collector.stop()

        # Get metrics
        metrics = collector.get_metrics()

        # Check metrics
        assert "duration_ms" in metrics
        assert "memory_change_mb" in metrics
        assert "total_memory_mb" in metrics
        assert "cpu_percent" in metrics

        assert metrics["memory_change_mb"] == 10.0
        assert metrics["total_memory_mb"] == 110.0
        assert metrics["cpu_percent"] == 15.0  # Average of samples

    def test_metrics_collector_threading(self):
        """Test that the metrics collector handles threading correctly."""
        with patch("backend.app.utils.metrics.get_cpu_usage") as mock_cpu:
            # Setup CPU mock to return increasing values
            mock_cpu.side_effect = [5.0, 10.0, 15.0, 20.0, 25.0]

            # Create collector and start
            collector = MetricsCollector()
            collector.start()

            # Wait for a bit to allow samples to be collected
            time.sleep(0.2)

            # Stop collection
            collector.stop()

            # Check that CPU samples were collected
            assert len(collector._cpu_samples) > 0

            # Get metrics
            metrics = collector.get_metrics()

            # Check metrics
            assert "cpu_percent" in metrics
            assert metrics["cpu_percent"] > 0

    def test_get_metrics_without_start(self):
        """Test getting metrics without starting collection."""
        collector = MetricsCollector()
        metrics = collector.get_metrics()

        # Should return empty dict
        assert metrics == {}

    @patch("backend.app.utils.metrics.get_memory_usage")
    def test_memory_change_calculation(self, mock_memory):
        """Test that memory change is calculated correctly."""
        # Setup mocks with different memory values
        memory_start = {"rss_mb": 100.0, "vms_mb": 200.0, "percent": 5.0}
        memory_end = {"rss_mb": 90.0, "vms_mb": 190.0, "percent": 4.5}  # Memory decreased

        mock_memory.side_effect = [memory_start, memory_end]

        # Create collector and start/stop
        collector = MetricsCollector()
        collector.start()
        collector.stop()

        # Get metrics
        metrics = collector.get_metrics()

        # Check memory change calculation
        assert metrics["memory_change_mb"] == -10.0  # Negative change
        assert metrics["total_memory_mb"] == 90.0
