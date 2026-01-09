#!/usr/bin/env python3
"""
Phase 3 Cost Management Testing Script

Tests the cost management and monitoring features.

Usage:
    python scripts/test_phase3_cost_management.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.gemini_cost_manager import get_cost_manager, CostManager


def test_budget_setting():
    """Test 1: Budget configuration"""
    print("\n" + "=" * 70)
    print("Test 1: Budget Configuration")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Set budget
        manager.set_budget(
            daily_limit=500,
            weekly_limit=2000,
            monthly_limit=10000,
            alert_threshold=0.8,
            enable_auto_stop=False
        )

        # Verify
        assert manager.budget.daily_limit == 500
        assert manager.budget.weekly_limit == 2000
        assert manager.budget.monthly_limit == 10000
        assert manager.budget.alert_threshold == 0.8
        assert manager.budget.enable_auto_stop == False

        print("✅ Success: Budget configured correctly")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_cost_calculation():
    """Test 2: Cost calculation"""
    print("\n" + "=" * 70)
    print("Test 2: Cost Calculation")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Test free tier
        free_cost = manager.calculate_cost(
            tier="free",
            input_tokens=1000,
            output_tokens=500
        )
        assert free_cost == 0.0, f"Free tier should be ¥0, got ¥{free_cost}"

        # Test paid tier (gemini-2.5-flash)
        paid_cost = manager.calculate_cost(
            tier="paid",
            model="gemini-2.5-flash",
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000   # 1M tokens
        )
        # Expected: (1M * 1.875) + (1M * 7.5) = 1.875 + 7.5 = 9.375
        expected = 9.375
        assert abs(paid_cost - expected) < 0.01, f"Expected ¥{expected}, got ¥{paid_cost}"

        print(f"✅ Success: Free tier = ¥{free_cost}, Paid tier = ¥{paid_cost:.2f}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_usage_stats():
    """Test 3: Usage statistics"""
    print("\n" + "=" * 70)
    print("Test 3: Usage Statistics")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        stats = manager.get_usage_stats(days=1)

        print(f"✅ Success: Retrieved stats for today")
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Free calls:  {stats['free_calls']}")
        print(f"   Paid calls:  {stats['paid_calls']}")
        print(f"   Total cost:  ¥{stats['total_cost']:.2f}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_budget_status():
    """Test 4: Budget status checking"""
    print("\n" + "=" * 70)
    print("Test 4: Budget Status Checking")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Set a low daily limit for testing
        manager.set_budget(daily_limit=0.01, alert_threshold=0.5)

        status = manager.check_budget_status()

        print(f"✅ Success: Budget status retrieved")
        print(f"   Daily status:")
        print(f"     Limit: ¥{status['daily']['limit']}")
        print(f"     Used: ¥{status['daily']['used']:.4f}")
        print(f"     Exceeded: {status['daily']['exceeded']}")
        print(f"     Warning: {status['daily']['warning']}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_can_proceed():
    """Test 5: Auto-stop functionality"""
    print("\n" + "=" * 70)
    print("Test 5: Auto-Stop Functionality")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Test with auto-stop disabled
        manager.set_budget(daily_limit=0.01, enable_auto_stop=False)
        can_proceed = manager.can_proceed()
        assert can_proceed == True, "Should proceed when auto-stop is disabled"
        print(f"✅ Auto-stop disabled: can_proceed = {can_proceed}")

        # Test with auto-stop enabled (may exceed budget)
        manager.set_budget(daily_limit=0.01, enable_auto_stop=True)
        can_proceed = manager.can_proceed()
        print(f"✅ Auto-stop enabled: can_proceed = {can_proceed}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_alert_callback():
    """Test 6: Alert callbacks"""
    print("\n" + "=" * 70)
    print("Test 6: Alert Callbacks")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Add callback
        alerts_received = []

        def test_callback(alert_type: str, data: dict):
            alerts_received.append({'type': alert_type, 'data': data})
            print(f"   📢 Alert received: {alert_type}")

        manager.add_alert_callback(test_callback)

        # Trigger check (may or may not trigger alert depending on actual usage)
        manager.set_budget(daily_limit=0.01, alert_threshold=0.0)
        manager.check_budget_status()

        print(f"✅ Success: Alert callback registered")
        print(f"   Alerts received: {len(alerts_received)}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_budget_report():
    """Test 7: Budget report generation"""
    print("\n" + "=" * 70)
    print("Test 7: Budget Report Generation")
    print("=" * 70)

    try:
        manager = get_cost_manager()

        # Set budget
        manager.set_budget(
            daily_limit=100,
            weekly_limit=500,
            monthly_limit=2000,
            alert_threshold=0.8
        )

        # Print report
        manager.print_budget_report()

        print("✅ Success: Budget report generated")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Phase 3: Cost Management Testing")
    print("=" * 70)

    tests = [
        ("Budget Setting", test_budget_setting),
        ("Cost Calculation", test_cost_calculation),
        ("Usage Statistics", test_usage_stats),
        ("Budget Status", test_budget_status),
        ("Auto-Stop", test_can_proceed),
        ("Alert Callbacks", test_alert_callback),
        ("Budget Report", test_budget_report),
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
