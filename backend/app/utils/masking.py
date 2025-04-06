"""
Utilities for masking sensitive data in logs.

This module provides functions for masking sensitive information before logging.
"""

import os
import re
from typing import Dict, Any, List, Union, Pattern


# Regular expressions for sensitive data patterns
PATTERNS = {
    # Credit card numbers (with or without spaces/dashes)
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),

    # Social security numbers (with or without dashes)
    "ssn": re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b"),

    # Email addresses
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),

    # Phone numbers (various formats)
    "phone": re.compile(r"\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),

    # API keys and tokens (common patterns)
    "api_key": re.compile(r"\b[A-Za-z0-9_\-]{20,}\b"),

    # IP addresses
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}

# Sensitive field names (case-insensitive)
SENSITIVE_FIELDS = {
    "password", "token", "api_key", "apikey", "secret", "credential",
    "auth", "authorization", "access_token", "refresh_token",
    "private_key", "secret_key", "key", "ssn", "credit_card",
    "card_number", "cvv", "cvc", "pin"
}

# Load additional fields to mask from environment variable
ADDITIONAL_FIELDS = set(
    field.strip().lower()
    for field in os.getenv("MASK_ADDITIONAL_FIELDS", "").split(",")
    if field.strip()
)

# Combine default and additional fields
FIELDS_TO_MASK = SENSITIVE_FIELDS.union(ADDITIONAL_FIELDS)


def mask_credit_card(value: str) -> str:
    """
    Mask credit card number, showing only the last 4 digits.

    Args:
        value: Credit card number

    Returns:
        Masked credit card number
    """
    if not value or len(value) < 8:
        return value

    # Keep only the last 4 digits
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) < 8:  # Not likely a credit card
        return value

    return f"****-****-****-{digits[-4:]}"


def mask_email(value: str) -> str:
    """
    Mask email address, showing only first 2 characters and domain.

    Args:
        value: Email address

    Returns:
        Masked email address
    """
    if not value or "@" not in value:
        return value

    username, domain = value.split("@", 1)
    if len(username) <= 2:
        masked_username = username[0] + "*" * (len(username) - 1)
    else:
        masked_username = username[:2] + "*" * (len(username) - 2)

    return f"{masked_username}@{domain}"


def mask_phone(value: str) -> str:
    """
    Mask phone number, showing only the last 4 digits.

    Args:
        value: Phone number

    Returns:
        Masked phone number
    """
    if not value:
        return value

    # Keep only digits
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) < 7:  # Not likely a phone number
        return value

    return f"***-***-{digits[-4:]}"


def mask_ip_address(value: str) -> str:
    """
    Mask IP address, showing only the first octet.

    Args:
        value: IP address

    Returns:
        Masked IP address
    """
    if not value or "." not in value:
        return value

    parts = value.split(".")
    if len(parts) != 4:
        return value

    return f"{parts[0]}.***.***"


def mask_string_value(value: str) -> str:
    """
    Apply appropriate masking based on the string content.

    Args:
        value: String to mask

    Returns:
        Masked string
    """
    if not value or not isinstance(value, str):
        return value

    # Apply pattern-based masking
    if PATTERNS["credit_card"].search(value):
        return PATTERNS["credit_card"].sub(
            lambda m: mask_credit_card(m.group(0)), value
        )

    if PATTERNS["email"].search(value):
        return PATTERNS["email"].sub(
            lambda m: mask_email(m.group(0)), value
        )

    if PATTERNS["phone"].search(value):
        return PATTERNS["phone"].sub(
            lambda m: mask_phone(m.group(0)), value
        )

    if PATTERNS["ip_address"].search(value):
        return PATTERNS["ip_address"].sub(
            lambda m: mask_ip_address(m.group(0)), value
        )

    if PATTERNS["ssn"].search(value):
        return PATTERNS["ssn"].sub("***-**-****", value)

    if PATTERNS["api_key"].search(value):
        return PATTERNS["api_key"].sub(
            lambda m: m.group(0)[:4] + "***" + m.group(0)[-4:]
            if len(m.group(0)) > 8 else "********",
            value
        )

    return value


def mask_sensitive_data(data: Any, parent_key: str = "") -> Any:
    """
    Recursively mask sensitive data in various data structures.

    Args:
        data: Data to mask (dict, list, str, etc.)
        parent_key: Key of the parent field (for nested structures)

    Returns:
        Data with sensitive information masked
    """
    if data is None:
        return None

    # Handle dictionaries
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            lower_key = key.lower() if isinstance(key, str) else ""

            # Check if the field should be completely masked
            if lower_key in FIELDS_TO_MASK:
                masked_data[key] = "***MASKED***"
            else:
                # Recursively mask nested data
                masked_data[key] = mask_sensitive_data(value, lower_key)

        return masked_data

    # Handle lists and tuples
    elif isinstance(data, (list, tuple)):
        return type(data)(mask_sensitive_data(item, parent_key) for item in data)

    # Handle strings (apply pattern-based masking)
    elif isinstance(data, str):
        # If parent key is sensitive, mask completely
        if parent_key and parent_key.lower() in FIELDS_TO_MASK:
            return "***MASKED***"

        # Otherwise apply pattern-based masking
        return mask_string_value(data)

    # Return other data types as-is
    return data


def mask_request_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in request data.

    Args:
        request_data: Dictionary containing request data

    Returns:
        Masked request data
    """
    masked_data = {}

    # Mask headers if present
    if "headers" in request_data:
        headers = dict(request_data["headers"])
        masked_headers = {}

        for header_name, header_value in headers.items():
            header_lower = header_name.lower()
            if any(sensitive in header_lower for sensitive in ("auth", "token", "key", "secret", "credential")):
                masked_headers[header_name] = "***MASKED***"
            else:
                masked_headers[header_name] = header_value

        masked_data["headers"] = masked_headers

    # Mask everything else recursively
    for key, value in request_data.items():
        if key != "headers":  # Headers already handled above
            masked_data[key] = mask_sensitive_data(value)

    return masked_data
