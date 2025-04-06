import os
import time
import logging
from typing import Dict, Any, Callable, Awaitable, Optional

try:
    import psutil
    import fastapi
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError:
    # For linting purposes, define placeholder types if imports fail
    BaseHTTPMiddleware = object
    class Request: pass
    class Response: pass
    psutil = None

from backend.app.utils.aws_client import AWSClient
from backend.app.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting and sending performance metrics to CloudWatch.
    Captures request latency, CPU and memory usage for monitoring.
    """

    def __init__(
        self,
        app: fastapi.FastAPI,
        aws_client: Optional[AWSClient] = None,
        enable_metrics: bool = True,
        namespace: str = "API",
    ):
        super().__init__(app)
        self.aws_client = aws_client
        self.enable_metrics = enable_metrics
        self.namespace = namespace
        self.is_test_env = os.environ.get("TESTING", "false").lower() == "true"

        if enable_metrics and not aws_client:
            logger.info("Metrics collection enabled without CloudWatch")
        elif enable_metrics:
            logger.info("Metrics collection enabled with CloudWatch integration")
        else:
            logger.info("Metrics collection disabled")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enable_metrics:
            return await call_next(request)

        metrics_collector = MetricsCollector()
        metrics_collector.start()

        try:
            response = await call_next(request)
            metrics = metrics_collector.get_metrics()
            if self.aws_client:
                await self._send_request_metrics(request, response, metrics)
            return response
        except Exception as error:
            metrics = metrics_collector.get_metrics()
            if self.aws_client:
                await self._send_error_metrics(request, error, metrics)
            raise
        finally:
            metrics_collector.stop()

    async def _send_request_metrics(
        self, request: Request, response: Response, metrics: dict
    ) -> None:
        if not self.aws_client or not self.enable_metrics:
            return

        dimensions = {
            "Path": str(request.url.path),
            "Method": request.method,
            "StatusCode": str(response.status_code),
        }

        try:
            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="RequestTime",
                value=metrics.get("duration_ms", 0),
                unit="Milliseconds",
                dimensions=dimensions,
            )

            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="MemoryUsage",
                value=metrics.get("memory_usage", 0),
                unit="Percent",
                dimensions=dimensions,
            )

            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="CPUUsage",
                value=metrics.get("cpu_usage", 0),
                unit="Percent",
                dimensions=dimensions,
            )
        except Exception as e:
            logger.warning(f"Failed to send request metrics to CloudWatch: {e}")

    async def _send_error_metrics(
        self, request: Request, error: Exception, metrics: dict
    ) -> None:
        if not self.aws_client or not self.enable_metrics:
            return

        dimensions = {
            "Path": str(request.url.path),
            "Method": request.method,
            "ErrorType": error.__class__.__name__,
        }

        try:
            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="Errors",
                value=1,
                unit="Count",
                dimensions=dimensions,
            )

            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="ErrorRequestTime",
                value=metrics.get("duration_ms", 0),
                unit="Milliseconds",
                dimensions=dimensions,
            )
        except Exception as e:
            logger.warning(f"Failed to send error metrics to CloudWatch: {e}")

    def _log_metrics(
        self,
        path: str,
        request_time_ms: float,
        memory_usage: Optional[float],
        cpu_usage: Optional[float],
        memory_change: float,
        cpu_change: float
    ) -> None:
        """Log metrics locally."""
        metrics = {
            "endpoint": path,
            "latency_ms": request_time_ms,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "memory_change": memory_change,
            "cpu_change": cpu_change
        }
        logger.info(f"Request metrics: {metrics}")
