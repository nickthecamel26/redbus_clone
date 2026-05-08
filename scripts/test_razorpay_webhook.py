"""
Standalone testing utility for Razorpay webhook signature verification.

This script tests the POST /api/v1/payments/webhook endpoint with:
1. Success Case: Valid signature - Expects 200 OK
2. Invalid Signature Case: Modified signature - Expects 400 Bad Request  
3. Missing Header Case: No signature header - Expects 400 Bad Request

Usage:
    python scripts/test_razorpay_webhook.py

Requirements:
    - Backend server running on http://localhost:8000
    - RAZORPAY_WEBHOOK_SECRET set in environment or .env file
"""

import os
import sys
import json
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# Add parent directory to path to import from backend if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment variables from .env file
load_dotenv()

# Configuration
WEBHOOK_URL = "http://localhost:8000/api/v1/payments/webhook"
WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test_1234567890abcdef")


def generate_razorpay_signature(payload: str, secret: str) -> str:
    """
    Generate Razorpay webhook signature using HMAC-SHA256.
    
    Args:
        payload: JSON string payload
        secret: Webhook secret key
        
    Returns:
        Hexadecimal signature string
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def send_webhook_request(payload: dict, signature: str = None) -> requests.Response:
    """
    Send POST request to webhook endpoint.
    
    Args:
        payload: Dictionary payload to send
        signature: Optional signature header value
        
    Returns:
        Response object
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if signature is not None:
        headers["X-Razorpay-Signature"] = signature
    
    # Serialize payload to JSON string to ensure body matches signature
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    response = requests.post(
        WEBHOOK_URL,
        headers=headers,
        data=payload_json
    )
    
    return response


def test_success_case():
    """Test Case 1: Valid payment.captured payload with correct signature."""
    print("\n" + "=" * 60)
    print("TEST CASE 1: Success Case - Valid Signature")
    print("=" * 60)
    
    # Create valid payment.captured payload - MUST match exact structure
    # Note: Using the exact same structure as used in container test
    payload_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_12345",
                    "amount": 89900,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "booking_id": 28
                    }
                }
            }
        }
    }
    
    # Convert to JSON string for signature generation (compact format, no spaces)
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    
    print(f"Payload JSON: {payload_json}")
    print(f"Payload length: {len(payload_json)} bytes")
    
    # Generate valid signature using EXACT same method as server
    signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Generated Signature: {signature}")
    print(f"Webhook Secret: {WEBHOOK_SECRET[:25]}...")
    
    # Send request with valid signature (using same JSON serialization)
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature
    }
    
    # Use data= instead of json= to send exact bytes
    response = requests.post(WEBHOOK_URL, headers=headers, data=payload_json)
    
    # Validate response
    if response.status_code == 200:
        print("✅ SUCCESS: Signature Verified - Received 200 OK")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
        print("\n💡 Check Uvicorn terminal for 'Webhook Signature Verified' log")
        return True
    else:
        print(f"❌ FAILED: Expected 200 OK, got {response.status_code}")
        print(f"Response: {response.text}")
        print(f"\nDebug: The signature may not match due to encoding differences")
        return False


def test_invalid_signature_case():
    """Test Case 2: Valid payload but with modified/invalid signature."""
    print("\n" + "=" * 60)
    print("TEST CASE 2: Invalid Signature Case")
    print("=" * 60)
    
    # Create valid payload
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_12345",
                    "amount": 89900,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "booking_id": 28
                    }
                }
            }
        }
    }
    
    # Serialize payload
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Generate invalid signature (modified)
    invalid_signature = "invalid_signature_1234567890abcdef"
    print(f"Using Invalid Signature: {invalid_signature[:30]}...")
    print(f"Payload JSON: {payload_json[:60]}...")
    
    # Send request with invalid signature
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": invalid_signature
    }
    response = requests.post(WEBHOOK_URL, headers=headers, data=payload_json)
    
    # Validate response - should be 400 Bad Request
    if response.status_code == 400:
        print("✅ SUCCESS: Invalid Signature Caught - Received 400 Bad Request")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
        return True
    else:
        print(f"❌ FAILED: Expected 400 Bad Request, got {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_missing_header_case():
    """Test Case 3: Payload without X-Razorpay-Signature header."""
    print("\n" + "=" * 60)
    print("TEST CASE 3: Missing Header Case")
    print("=" * 60)
    
    # Create valid payload
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_12345",
                    "amount": 89900,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "booking_id": 28
                    }
                }
            }
        }
    }
    
    # Serialize payload
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print("Sending request WITHOUT X-Razorpay-Signature header...")
    print(f"Payload JSON: {payload_json[:60]}...")
    
    # Send request without signature header
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(WEBHOOK_URL, headers=headers, data=payload_json)
    
    # Validate response - should be 400 Bad Request
    if response.status_code == 400:
        print("✅ SUCCESS: Missing Header Caught - Received 400 Bad Request")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
        return True
    else:
        print(f"❌ FAILED: Expected 400 Bad Request, got {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    """Run all test cases."""
    print("\n" + "🚀 " * 30)
    print("RAZORPAY WEBHOOK SIGNATURE VERIFICATION TEST SUITE")
    print("🚀 " * 30)
    print(f"\nTarget URL: {WEBHOOK_URL}")
    print(f"Webhook Secret: {WEBHOOK_SECRET[:25]}...")
    
    # Track results
    results = []
    
    # Run test cases
    results.append(("Success Case", test_success_case()))
    results.append(("Invalid Signature Case", test_invalid_signature_case()))
    results.append(("Missing Header Case", test_missing_header_case()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Webhook signature verification is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
    
    print("\n" + "=" * 60)
    print("💡 Note: Check the Uvicorn terminal logs to see:")
    print("   - 'Received Razorpay webhook request'")
    print("   - 'Webhook Signature Verified' (for success case)")
    print("   - 'Invalid Signature' (for invalid signature case)")
    print("   - 'Missing X-Razorpay-Signature header' (for missing header case)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
