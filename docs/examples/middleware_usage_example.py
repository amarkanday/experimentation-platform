"""
Example of using the enhanced logging middleware.

This example demonstrates how to use the logging middleware with
sensitive data masking and performance metrics collection.
"""

import os
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient

from backend.app.middleware.logging_middleware import LoggingMiddleware
from backend.app.core.logging import setup_logging


# Set up environment variables for middleware configuration
os.environ["COLLECT_REQUEST_BODY"] = "true"
os.environ["MASK_ADDITIONAL_FIELDS"] = "personal_info,account_number"
os.environ["LOG_LEVEL"] = "INFO"


# Create FastAPI application
app = FastAPI()

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Set up logging
setup_logging(enable_cloudwatch=False)


@app.get("/api/public")
async def public_endpoint():
    """A simple public endpoint returning some data."""
    return {"status": "ok", "message": "Public API"}


@app.post("/api/users")
async def create_user(request: Request):
    """
    Example endpoint with sensitive data that will be masked.

    This demonstrates how the middleware handles masking of sensitive
    information in request bodies.
    """
    body = await request.json()

    # Process user data (sensitive data is already masked in logs)
    return {
        "id": "user123",
        "username": body.get("username"),
        "email": body.get("email"),
        "created": True
    }


@app.post("/api/payments")
async def process_payment(request: Request):
    """
    Example endpoint with sensitive payment data that will be masked.

    This demonstrates how fields like credit card numbers, tokens and
    custom fields are masked.
    """
    body = await request.json()

    # Process payment (sensitive data is already masked in logs)
    return {
        "transaction_id": "txn_123456",
        "status": "completed",
        "amount": body.get("amount")
    }


# Example usage
if __name__ == "__main__":
    # Create test client
    client = TestClient(app)

    print("Making requests to demonstrate logging and masking...")

    # Make a simple request
    response = client.get("/api/public")
    print(f"Public API response: {response.status_code}")

    # Make a request with user data (sensitive)
    user_data = {
        "username": "testuser",
        "email": "user@example.com",
        "password": "securepassword123",
        "personal_info": {
            "full_name": "Test User",
            "dob": "1990-01-01"
        }
    }
    response = client.post("/api/users", json=user_data)
    print(f"Create user response: {response.status_code}")

    # Make a request with payment data (sensitive)
    payment_data = {
        "amount": 100.50,
        "currency": "USD",
        "credit_card": "4111-1111-1111-1111",
        "cvv": "123",
        "account_number": "123456789",
        "token": "tok_visa_4242424242424242",
        "customer": {
            "email": "customer@example.com",
            "phone": "+1-555-123-4567",
            "ip_address": "192.168.1.100"
        }
    }
    response = client.post("/api/payments", json=payment_data)
    print(f"Process payment response: {response.status_code}")

    print("\nCheck the logs to see how sensitive data is masked and performance metrics are collected!")
    print("You should see masked data like:")
    print("  - Passwords: '***MASKED***'")
    print("  - Credit cards: '****-****-****-1111'")
    print("  - Emails: 'us***@example.com'")
    print("  - Phone numbers: '***-***-4567'")
    print("  - IP addresses: '192.***.***'")
    print("  - Custom fields: account_number and personal_info")
    print("\nAnd performance metrics like:")
    print("  - Process time (ms)")
    print("  - Memory usage (MB)")
    print("  - CPU usage (%)")
