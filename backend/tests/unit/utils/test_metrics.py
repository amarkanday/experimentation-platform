"""
Unit tests for the metrics collection utility functions.

These tests verify that performance metrics collection works correctly.
"""

import time
import threading
from unittest.mock import patch, MagicMock, Mock

import pytest
import psutil

from backend.app.utils.metrics import get_memory_usage, get_cpu_usage, MetricsCollector


class TestMetrics:
    @pytest.fixture
    def mock_process(self):
        return Mock(spec=psutil.Process)

    @pytest.fixture
    def mock_psutil(self):
        with patch('psutil.Process') as mock:
            yield mock

    def test_get_memory_usage_success(self, mock_process):
        # Test successful memory usage retrieval
        mock_process.memory_percent.return_value = 42.0

        result = get_memory_usage(mock_process)

        assert result == 42.0
        mock_process.memory_percent.assert_called_once()

    def test_get_memory_usage_error(self, mock_process):
        # Test memory usage retrieval with error
        mock_process.memory_percent.side_effect = psutil.Error("Memory error")

        result = get_memory_usage(mock_process)

        assert result == 0.0

    def test_get_cpu_usage_success(self, mock_process):
        # Test successful CPU usage retrieval
        mock_process.cpu_percent.return_value = 75.0

        result = get_cpu_usage(mock_process)

        assert result == 75.0
        mock_process.cpu_percent.assert_called_once()

    def test_get_cpu_usage_error(self, mock_process):
        # Test CPU usage retrieval with error
        mock_process.cpu_percent.side_effect = psutil.Error("CPU error")

        result = get_cpu_usage(mock_process)

        assert result == 0.0


class TestMetricsCollector:
    """Tests for the MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    @pytest.fixture
    def mock_process(self):
        process = Mock(spec=psutil.Process)
        process.memory_percent.return_value = 50.0
        process.cpu_percent.return_value = 25.0
        return process

    @patch('psutil.Process')
    def test_start_collection(self, mock_psutil, collector, mock_process):
        # Test starting metrics collection
        mock_psutil.return_value = mock_process

        collector.start()

        assert collector.is_running is True
        assert collector.process == mock_process

    def test_stop_collection(self, collector):
        # Test stopping metrics collection
        collector.start()
        collector.stop()

        assert collector.is_running is False
        assert collector.process is None

    @patch('psutil.Process')
    def test_get_metrics(self, mock_psutil, collector, mock_process):
        # Test getting collected metrics
        mock_psutil.return_value = mock_process
        collector.start()

        metrics = collector.get_metrics()

        assert 'memory_usage' in metrics
        assert 'cpu_usage' in metrics
        assert metrics['memory_usage'] == 50.0
        assert metrics['cpu_usage'] == 25.0

    def test_get_metrics_not_started(self, collector):
        # Test getting metrics without starting collection
        metrics = collector.get_metrics()

        assert metrics == {}

    @patch('psutil.Process')
    def test_collect_metrics_thread(self, mock_psutil, collector, mock_process):
        # Test metrics collection in background thread
        mock_psutil.return_value = mock_process
        collector.start()

        # Simulate some time passing
        collector.stop()

        assert len(collector.metrics_history) > 0
        assert 'memory_usage' in collector.metrics_history[0]
        assert 'cpu_usage' in collector.metrics_history[0]

    @patch('psutil.Process')
    def test_metrics_history_limit(self, mock_psutil, collector, mock_process):
        # Test metrics history size limit
        mock_psutil.return_value = mock_process
        collector.max_history_size = 5
        collector.start()

        # Collect more metrics than the limit
        for _ in range(10):
            collector._collect_metrics()

        collector.stop()

        assert len(collector.metrics_history) == 5

    @patch('psutil.Process')
    def test_metrics_average(self, mock_psutil, collector, mock_process):
        # Test calculating metrics averages
        mock_psutil.return_value = mock_process
        collector.start()

        # Collect multiple metrics
        for _ in range(3):
            collector._collect_metrics()

        averages = collector.get_average_metrics()

        assert 'memory_usage' in averages
        assert 'cpu_usage' in averages
        assert averages['memory_usage'] == 50.0
        assert averages['cpu_usage'] == 25.0

    @patch('psutil.Process')
    def test_metrics_peak(self, mock_psutil, collector, mock_process):
        # Test finding peak metrics
        mock_psutil.return_value = mock_process
        collector.start()

        # Collect metrics with varying values
        mock_process.memory_percent.side_effect = [30.0, 50.0, 40.0]
        mock_process.cpu_percent.side_effect = [20.0, 30.0, 25.0]

        for _ in range(3):
            collector._collect_metrics()

        peaks = collector.get_peak_metrics()

        assert peaks['memory_usage'] == 50.0
        assert peaks['cpu_usage'] == 30.0
