"""
Utilities for collecting performance metrics.

This module provides functions for measuring CPU, memory usage and other
performance metrics.
"""

import os
import time
import resource
import platform
import threading
import psutil
from typing import Dict, Any, Optional


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage of the process in MB.

    Returns:
        Dictionary with memory usage metrics
    """
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        # Convert to MB
        rss_mb = mem_info.rss / (1024 * 1024)
        vms_mb = mem_info.vms / (1024 * 1024)

        return {
            "rss_mb": round(rss_mb, 2),  # Resident Set Size
            "vms_mb": round(vms_mb, 2),  # Virtual Memory Size
            "percent": round(process.memory_percent(), 2)
        }
    except (psutil.Error, Exception):
        # Fallback to resource module if psutil fails
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # Convert to MB (maxrss is in KB on most systems)
            mem_mb = usage.ru_maxrss / 1024
            return {
                "rss_mb": round(mem_mb, 2),
                "vms_mb": 0,
                "percent": 0
            }
        except Exception:
            # Return zeros if all methods fail
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0
            }


def get_cpu_usage() -> float:
    """
    Get current CPU usage of the process.

    Returns:
        CPU usage percentage
    """
    try:
        process = psutil.Process(os.getpid())
        return round(process.cpu_percent(interval=0.1), 2)
    except (psutil.Error, Exception):
        return 0.0


class MetricsCollector:
    """Collector for performance metrics over time."""

    def __init__(self):
        """Initialize the collector."""
        self.start_memory = None
        self.end_memory = None
        self.start_time = None
        self.end_time = None
        self.cpu_usage = 0.0
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._cpu_samples = []

    def start(self):
        """Start collecting metrics."""
        self.start_time = time.time()
        self.start_memory = get_memory_usage()
        self._running = True
        self._cpu_samples = []

        # Start CPU sampling in a background thread
        self._thread = threading.Thread(target=self._sample_cpu)
        self._thread.daemon = True
        self._thread.start()

    def _sample_cpu(self):
        """Sample CPU usage at regular intervals."""
        while self._running:
            try:
                with self._lock:
                    cpu = get_cpu_usage()
                    self._cpu_samples.append(cpu)
                time.sleep(0.5)  # Sample every 500ms
            except Exception:
                pass

    def stop(self):
        """Stop collecting metrics and compute final values."""
        self.end_time = time.time()
        self.end_memory = get_memory_usage()
        self._running = False

        # Wait for the sampling thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        # Calculate average CPU usage
        with self._lock:
            if self._cpu_samples:
                self.cpu_usage = sum(self._cpu_samples) / len(self._cpu_samples)
            else:
                self.cpu_usage = get_cpu_usage()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        Returns:
            Dictionary with collected metrics
        """
        if not self.start_time:
            return {}

        # Calculate process time in milliseconds
        duration_ms = (self.end_time or time.time()) - self.start_time
        duration_ms *= 1000  # Convert to milliseconds

        # Calculate memory change
        memory_change = 0
        total_memory = 0
        memory_usage_start = 0
        memory_usage_end = 0

        if self.start_memory and self.end_memory:
            memory_usage_start = self.start_memory.get("rss_mb", 0)
            memory_usage_end = self.end_memory.get("rss_mb", 0)
            memory_change = memory_usage_end - memory_usage_start
            total_memory = memory_usage_end

        return {
            "duration_ms": round(duration_ms, 2),
            "memory_change_mb": round(memory_change, 2),
            "total_memory_mb": round(total_memory, 2),
            "cpu_percent": round(self.cpu_usage, 2)
        }
