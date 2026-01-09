#!/usr/bin/env python3
"""
Phase 2 Fallback Testing Script

Tests the auto-fallback functionality of GeminiClient.

Usage:
    python scripts/test_phase2_fallback.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.gemini_client import create_gemini_client, print_usage_report
from src.core.gemini_helpers import generate_with_fallback, print_usage_summary
from dotenv import load_dotenv

# Load environment
load_dotenv()


def test_basic_generation():
    """Test 1: Basic text generation"""
    print("\n" + "=" * 70)
    print("Test 1: Basic Text Generation")
    print("=" * 70)

    try:
        response = generate_with_fallback(
            prompt="What is 2 + 2?",
            model_name="gemini-2.5-flash"
        )
        print(f"✅ Success: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_json_generation():
    """Test 2: JSON generation"""
    print("\n" + "=" * 70)
    print("Test 2: JSON Generation")
    print("=" * 70)

    try:
        response = generate_with_fallback(
            prompt='Generate a JSON object with name and age fields',
            model_name="gemini-2.5-flash",
            response_mime_type="application/json"
        )
        print(f"✅ Success: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_client_direct():
    """Test 3: Direct client usage"""
    print("\n" + "=" * 70)
    print("Test 3: Direct Client Usage")
    print("=" * 70)

    try:
        client = create_gemini_client()

        response = client.generate_content(
            prompt="Say hello in Japanese",
            model_name="gemini-2.5-flash"
        )

        print(f"✅ Success: {response.text}")
        print(f"\nUsage stats: {client.get_usage_stats()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_fallback_disabled():
    """Test 4: Fallback disabled"""
    print("\n" + "=" * 70)
    print("Test 4: Fallback Disabled (should use single tier)")
    print("=" * 70)

    try:
        response = generate_with_fallback(
            prompt="Count from 1 to 5",
            model_name="gemini-2.5-flash",
            enable_fallback=False
        )
        print(f"✅ Success: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_usage_tracking():
    """Test 5: Usage tracking"""
    print("\n" + "=" * 70)
    print("Test 5: Usage Tracking")
    print("=" * 70)

    try:
        # Make several calls
        for i in range(3):
            generate_with_fallback(f"Test call {i+1}")

        # Print summary
        print_usage_summary()

        # Print report
        print_usage_report(days=1)

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Phase 2: Auto-Fallback Testing")
    print("=" * 70)

    tests = [
        ("Basic Generation", test_basic_generation),
        ("JSON Generation", test_json_generation),
        ("Direct Client", test_client_direct),
        ("Fallback Disabled", test_fallback_disabled),
        ("Usage Tracking", test_usage_tracking),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
