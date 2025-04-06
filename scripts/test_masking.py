#!/usr/bin/env python3
"""
Masking Utility Test Script

This script allows you to test the data masking functionality with various input types.
Run this script from the root of the project to see how different sensitive data is masked.
"""

import sys
import os
import json
from pprint import pprint

# Add the backend directory to the path so we can import the masking module
sys.path.append(os.path.abspath("backend"))

try:
    from app.utils.masking import mask_data, mask_email, mask_credit_card, mask_phone_number, mask_ip_address
except ImportError:
    print("Error: Could not import masking module. Make sure you're running this script from the project root.")
    print("Usage: python scripts/test_masking.py [additional_fields]")
    sys.exit(1)

def run_examples():
    """
    Run examples of the masking functionality with various input types.
    """
    # Set additional fields to mask based on command line arguments
    additional_fields = sys.argv[1] if len(sys.argv) > 1 else "personal_info,account_number"
    os.environ["MASK_ADDITIONAL_FIELDS"] = additional_fields

    print(f"Using additional fields for masking: {additional_fields}")
    print("\n" + "="*50)

    # Simple examples of individual masking functions
    examples = [
        ("Email", mask_email, "user@example.com"),
        ("Credit Card", mask_credit_card, "4111-1111-1111-1111"),
        ("Phone Number", mask_phone_number, "+1-555-123-4567"),
        ("IP Address", mask_ip_address, "192.168.1.100"),
    ]

    print("INDIVIDUAL MASKING FUNCTIONS")
    print("-"*30)
    for name, func, value in examples:
        masked = func(value)
        print(f"{name}: '{value}' -> '{masked}'")

    # Complex examples with nested data
    print("\n" + "="*50)
    print("COMPLEX DATA MASKING")
    print("-"*30)

    # Sample user data
    user_data = {
        "username": "testuser",
        "email": "user@example.com",
        "password": "securepassword123",
        "personal_info": {
            "full_name": "Test User",
            "dob": "1990-01-01"
        }
    }

    # Sample payment data
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

    print("\nUser Data - Original:")
    pprint(user_data)
    print("\nUser Data - Masked:")
    pprint(mask_data(user_data))

    print("\nPayment Data - Original:")
    pprint(payment_data)
    print("\nPayment Data - Masked:")
    pprint(mask_data(payment_data))

    # Test with string input
    json_string = json.dumps(payment_data)
    print("\nJSON String - Original:")
    print(json_string)
    print("\nJSON String - Masked:")
    print(mask_data(json_string))

    # Test with None and non-dict values
    print("\nEdge Cases:")
    print(f"None value: {mask_data(None)}")
    print(f"Integer: {mask_data(12345)}")
    print(f"Empty dict: {mask_data({})}")
    print(f"Empty list: {mask_data([])}")

    # Test with a list of dictionaries
    list_data = [user_data, payment_data]
    print("\nList of Dictionaries - Original:")
    pprint(list_data)
    print("\nList of Dictionaries - Masked:")
    pprint(mask_data(list_data))

    print("\n" + "="*50)
    print("TESTING COMPLETE")
    print("="*50)

if __name__ == "__main__":
    run_examples()
