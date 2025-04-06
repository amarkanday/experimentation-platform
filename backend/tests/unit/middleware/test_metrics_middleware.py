import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from starlette.responses import Response
from backend.app.middleware.metrics_middleware import MetricsMiddleware
from backend.app.utils.aws_client import AWSClient

class TestMetricsMiddleware:
    @pytest.fixture
    def app(self):
        app = FastAPI()
        return app

    @pytest.fixture
    def mock_aws_client(self, mocker):
        mock_client = mocker.Mock(spec=AWSClient)
        mock_client.send_metric.return_value = True
        return mock_client

    @pytest.fixture
    def middleware(self, app, mock_aws_client):
        return MetricsMiddleware(
            app=app,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="TestNamespace"
        )

    @pytest.fixture
    def disabled_middleware(self, app, mock_aws_client):
        return MetricsMiddleware(
            app=app,
            aws_client=mock_aws_client,
            enable_metrics=False
        )

    @pytest.fixture
    def custom_namespace_middleware(self, app, mock_aws_client):
        return MetricsMiddleware(
            app=app,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="CustomNamespace"
        )

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        return request

    @pytest.fixture
    def mock_response(self):
        response = Mock(spec=Response)
        response.status_code = 200
        return response

    @pytest.fixture
    def mock_call_next(self, mock_response):
        async def call_next(request):
            return mock_response
        return call_next

    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_aws_client, mocker):
        """Test that metrics are collected and sent for successful requests."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="TestNamespace"
        )
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 404  # No route defined

        # Verify metrics were sent
        assert mock_aws_client.send_metric.call_count >= 3  # RequestTime, MemoryUsage, CPUUsage
        mock_aws_client.send_metric.assert_any_call(
            namespace="TestNamespace",
            metric_name="RequestTime",
            value=mocker.ANY,
            unit="Milliseconds",
            dimensions={"Path": "/test", "Method": "GET", "StatusCode": "404"}
        )

    @pytest.mark.asyncio
    async def test_request_with_error(self, middleware, mock_aws_client):
        """Test that error metrics are collected and sent."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="TestNamespace"
        )

        @app.get("/error")
        async def error_route():
            raise ValueError("Test error")

        client = TestClient(app)
        with pytest.raises(ValueError):
            response = client.get("/error")

        # Verify error metrics were sent
        assert mock_aws_client.send_metric.call_count >= 2  # Errors and ErrorRequestTime
        mock_aws_client.send_metric.assert_any_call(
            namespace="TestNamespace",
            metric_name="Errors",
            value=1,
            unit="Count",
            dimensions={"Path": "/error", "Method": "GET", "ErrorType": "ValueError"}
        )

    @pytest.mark.asyncio
    async def test_aws_client_error(self, middleware, mock_aws_client):
        """Test handling of AWS client errors."""
        # Set up the mock to raise an exception
        mock_aws_client.send_metric.side_effect = Exception("AWS Error")

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        # Add middleware with error handling
        app.add_middleware(
            MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="TestNamespace"
        )

        # Create test client and make request
        client = TestClient(app)
        response = client.get("/test")

        # Request should succeed despite AWS error
        assert response.status_code == 200
        assert response.json() == {"message": "test"}

        # Verify AWS client was called
        assert mock_aws_client.send_metric.called

        # Verify metrics were attempted to be sent
        calls = mock_aws_client.send_metric.call_args_list
        assert len(calls) > 0
        assert calls[0][1]["namespace"] == "TestNamespace"
        assert calls[0][1]["metric_name"] == "RequestTime"

    @pytest.mark.asyncio
    async def test_metrics_collection_disabled(self, disabled_middleware, mock_aws_client):
        """Test that no metrics are collected when disabled."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=False,
            namespace="TestNamespace"
        )
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 404  # No route defined
        mock_aws_client.send_metric.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_metric_namespace(self, custom_namespace_middleware, mock_aws_client, mocker):
        """Test using a custom metric namespace."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="CustomNamespace"
        )
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 404  # No route defined

        # Verify metrics were sent with custom namespace
        mock_aws_client.send_metric.assert_any_call(
            namespace="CustomNamespace",
            metric_name="RequestTime",
            value=mocker.ANY,
            unit="Milliseconds",
            dimensions={"Path": "/test", "Method": "GET", "StatusCode": "404"}
        )

    @pytest.mark.asyncio
    async def test_test_environment(self, middleware, mock_aws_client):
        """Test metrics collection in test environment."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware,
            aws_client=mock_aws_client,
            enable_metrics=True,
            namespace="TestNamespace"
        )
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 404  # No route defined
        mock_aws_client.send_metric.assert_called()
