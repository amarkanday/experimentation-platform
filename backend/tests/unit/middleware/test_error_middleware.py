import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request
from starlette.responses import Response
from backend.app.middleware.error_middleware import ErrorMiddleware
from backend.app.utils.aws_client import AWSClient
import mock

class TestErrorMiddleware:
    @pytest.fixture
    def app(self):
        return FastAPI()

    @pytest.fixture
    def mock_aws_client(self, mocker):
        mock_client = mocker.Mock(spec=AWSClient)
        mock_client.send_metric.return_value = True
        return mock_client

    @pytest.fixture
    def middleware(self, app, mock_aws_client):
        return ErrorMiddleware(app, aws_client=mock_aws_client)

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

    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request, mock_response, mock_aws_client):
        # Test successful request handling
        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        mock_aws_client.send_metric.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_with_error(self, middleware, mock_request, mock_aws_client):
        # Test request handling with error
        mock_aws_client.send_metric.return_value = True
        error_message = "Test error"

        async def raise_error(request):
            raise Exception(error_message)

        with pytest.raises(Exception) as exc_info:
            await middleware.dispatch(mock_request, raise_error)

        assert str(exc_info.value) == error_message
        mock_aws_client.send_metric.assert_called_once()
        assert mock_aws_client.send_metric.call_args[1]['metric_name'] == 'ErrorCount'

    @pytest.mark.asyncio
    async def test_aws_client_error(self, middleware, mock_request, mock_aws_client):
        # Test handling of AWS client errors
        mock_aws_client.send_metric.return_value = False
        error_message = "Test error"

        async def raise_error(request):
            raise Exception(error_message)

        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, raise_error)

        mock_aws_client.send_metric.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_tracking_disabled(self, app, mock_aws_client, mock_request):
        # Test with error tracking disabled
        middleware = ErrorMiddleware(app, aws_client=mock_aws_client, track_errors=False)
        error_message = "Test error"

        async def raise_error(request):
            raise Exception(error_message)

        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, raise_error)

        mock_aws_client.send_metric.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_metric_namespace(self, app, mock_aws_client, mock_request):
        # Test with custom metric namespace
        middleware = ErrorMiddleware(app, aws_client=mock_aws_client, metric_namespace="CustomNamespace")
        error_message = "Test error"

        async def raise_error(request):
            raise Exception(error_message)

        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, raise_error)

        assert mock_aws_client.send_metric.call_args[1]['namespace'] == "CustomNamespace"

    @pytest.mark.asyncio
    async def test_error_details(self, middleware, mock_request, mock_aws_client):
        # Test error details in metric data
        mock_aws_client.send_metric.return_value = True
        error_message = "Test error"

        async def raise_error(request):
            raise ValueError(error_message)

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, raise_error)

        metric_data = mock_aws_client.send_metric.call_args[1]
        assert metric_data['metric_name'] == 'ErrorCount'
        assert 'dimensions' in metric_data
        assert metric_data['dimensions']['ErrorType'] == 'ValueError'

    @pytest.mark.asyncio
    async def test_request_context(self, middleware, mock_request, mock_aws_client):
        # Test request context in error tracking
        mock_aws_client.send_metric.return_value = True
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"

        async def raise_error(request):
            raise Exception("Test error")

        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, raise_error)

        metric_data = mock_aws_client.send_metric.call_args[1]
        assert 'dimensions' in metric_data
        assert metric_data['dimensions']['Endpoint'] == "/api/test"
        assert metric_data['dimensions']['Method'] == "POST"
