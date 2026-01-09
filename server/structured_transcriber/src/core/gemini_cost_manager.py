"""
Gemini API Cost Management and Monitoring

Provides cost tracking, budgeting, and alerting functionality for Gemini API usage.

Phase 3 Implementation: 2025-10-21
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, asdict

from .config import LOG_DIR

# Configure logger
logger = logging.getLogger(__name__)

# Cost configuration file
COST_CONFIG_FILE = Path(LOG_DIR) / "gemini_cost_config.json"
COST_ALERTS_FILE = Path(LOG_DIR) / "gemini_cost_alerts.jsonl"


@dataclass
class CostBudget:
    """Cost budget configuration"""
    daily_limit: Optional[float] = None  # 日次上限（円）
    weekly_limit: Optional[float] = None  # 週次上限（円）
    monthly_limit: Optional[float] = None  # 月次上限（円）
    alert_threshold: float = 0.8  # アラート閾値（80%で警告）
    enable_auto_stop: bool = False  # 予算超過時に自動停止

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CostBudget':
        """Create from dictionary"""
        return cls(**data)


class CostManager:
    """
    Gemini API cost management system.

    Features:
    - Cost tracking per tier (free/paid)
    - Budget management (daily/weekly/monthly limits)
    - Alert system with callbacks
    - Auto-stop on budget exceeded

    Example:
        manager = CostManager()
        manager.set_budget(daily_limit=1000, alert_threshold=0.8)
        manager.add_alert_callback(send_email_alert)

        # Check before API call
        if manager.can_proceed():
            # Make API call
            ...
            manager.record_cost(tier="paid", tokens=1250)
    """

    # 料金設定（円/1M tokens、2025年10月時点）
    PRICING = {
        "free": {
            "input": 0,
            "output": 0,
        },
        "paid": {
            "gemini-2.5-flash": {
                "input": 1.875,  # $0.0125/1M tokens ≈ ¥1.875
                "output": 7.5,   # $0.05/1M tokens ≈ ¥7.5
            },
            "gemini-2.5-pro": {
                "input": 37.5,   # $0.25/1M tokens ≈ ¥37.5
                "output": 150,   # $1.00/1M tokens ≈ ¥150
            },
        }
    }

    def __init__(self):
        """Initialize cost manager"""
        self.budget = self._load_budget()
        self.alert_callbacks: List[Callable] = []
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        COST_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_budget(self) -> CostBudget:
        """Load budget configuration from file"""
        if COST_CONFIG_FILE.exists():
            try:
                with open(COST_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return CostBudget.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load budget config: {e}")

        return CostBudget()

    def _save_budget(self):
        """Save budget configuration to file"""
        try:
            with open(COST_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.budget.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save budget config: {e}")

    def set_budget(
        self,
        daily_limit: Optional[float] = None,
        weekly_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
        alert_threshold: float = 0.8,
        enable_auto_stop: bool = False
    ):
        """
        Set cost budget limits.

        Args:
            daily_limit: Daily cost limit in JPY (None = no limit)
            weekly_limit: Weekly cost limit in JPY (None = no limit)
            monthly_limit: Monthly cost limit in JPY (None = no limit)
            alert_threshold: Alert threshold (0.0-1.0, default 0.8 = 80%)
            enable_auto_stop: Whether to auto-stop on budget exceeded

        Example:
            # Set daily limit of ¥500
            manager.set_budget(daily_limit=500)

            # Set monthly limit of ¥10,000 with 90% alert
            manager.set_budget(monthly_limit=10000, alert_threshold=0.9)
        """
        self.budget = CostBudget(
            daily_limit=daily_limit,
            weekly_limit=weekly_limit,
            monthly_limit=monthly_limit,
            alert_threshold=alert_threshold,
            enable_auto_stop=enable_auto_stop
        )
        self._save_budget()
        logger.info(f"Budget updated: {self.budget}")

    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """
        Add alert callback function.

        Args:
            callback: Function to call on alert
                      Signature: callback(alert_type: str, data: dict)

        Example:
            def email_alert(alert_type, data):
                send_email(f"Alert: {alert_type}", data)

            manager.add_alert_callback(email_alert)
        """
        self.alert_callbacks.append(callback)

    def _trigger_alert(self, alert_type: str, data: Dict):
        """
        Trigger alert to all callbacks.

        Args:
            alert_type: Type of alert ("budget_warning", "budget_exceeded", etc.)
            data: Alert data
        """
        alert_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "data": data
        }

        # Log to file
        with open(COST_ALERTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert_entry, ensure_ascii=False) + "\n")

        logger.warning(f"Alert triggered: {alert_type} - {data}")

        # Call callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def calculate_cost(
        self,
        tier: str,
        model: str = "gemini-2.5-flash",
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> float:
        """
        Calculate cost for given usage.

        Args:
            tier: "free" or "paid"
            model: Model name (for paid tier)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in JPY

        Example:
            cost = manager.calculate_cost(
                tier="paid",
                model="gemini-2.5-flash",
                input_tokens=1000,
                output_tokens=500
            )
        """
        if tier == "free":
            return 0.0

        if model not in self.PRICING["paid"]:
            logger.warning(f"Unknown model: {model}, using gemini-2.5-flash pricing")
            model = "gemini-2.5-flash"

        pricing = self.PRICING["paid"][model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def record_cost(
        self,
        tier: str,
        model: str = "gemini-2.5-flash",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: Optional[float] = None
    ):
        """
        Record API cost.

        Args:
            tier: "free" or "paid"
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Pre-calculated cost (optional)
        """
        if cost is None:
            cost = self.calculate_cost(tier, model, input_tokens, output_tokens)

        if cost > 0:
            logger.info(f"Cost recorded: ¥{cost:.4f} ({tier}, {model})")

    def get_usage_stats(self, days: int = 1) -> Dict:
        """
        Get usage statistics for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with usage stats

        Example:
            stats = manager.get_usage_stats(days=7)
            print(f"Total cost: ¥{stats['total_cost']}")
        """
        from .gemini_client import get_usage_history

        history = get_usage_history(days=days)

        total_cost = 0.0
        free_calls = 0
        paid_calls = 0
        total_calls = len(history)

        for entry in history:
            tier = entry.get("tier", "free")
            model = entry.get("model", "gemini-2.5-flash")
            tokens = entry.get("tokens", 0)

            # Estimate token split (rough approximation)
            input_tokens = int(tokens * 0.7)
            output_tokens = int(tokens * 0.3)

            cost = self.calculate_cost(tier, model, input_tokens, output_tokens)
            total_cost += cost

            if tier == "free":
                free_calls += 1
            else:
                paid_calls += 1

        return {
            "period_days": days,
            "total_calls": total_calls,
            "free_calls": free_calls,
            "paid_calls": paid_calls,
            "total_cost": total_cost,
            "avg_cost_per_call": total_cost / total_calls if total_calls > 0 else 0,
        }

    def check_budget_status(self) -> Dict:
        """
        Check current budget status.

        Returns:
            Dictionary with budget status

        Example:
            status = manager.check_budget_status()
            if status["daily"]["exceeded"]:
                print("Daily budget exceeded!")
        """
        stats_daily = self.get_usage_stats(days=1)
        stats_weekly = self.get_usage_stats(days=7)
        stats_monthly = self.get_usage_stats(days=30)

        def check_limit(cost: float, limit: Optional[float]) -> Dict:
            if limit is None:
                return {"limit": None, "used": cost, "percentage": 0, "exceeded": False, "warning": False}

            percentage = cost / limit if limit > 0 else 0
            return {
                "limit": limit,
                "used": cost,
                "percentage": percentage,
                "exceeded": cost >= limit,
                "warning": percentage >= self.budget.alert_threshold
            }

        daily_status = check_limit(stats_daily["total_cost"], self.budget.daily_limit)
        weekly_status = check_limit(stats_weekly["total_cost"], self.budget.weekly_limit)
        monthly_status = check_limit(stats_monthly["total_cost"], self.budget.monthly_limit)

        # Trigger alerts if needed
        if daily_status["exceeded"]:
            self._trigger_alert("budget_exceeded", {"period": "daily", "status": daily_status})
        elif daily_status["warning"]:
            self._trigger_alert("budget_warning", {"period": "daily", "status": daily_status})

        if weekly_status["exceeded"]:
            self._trigger_alert("budget_exceeded", {"period": "weekly", "status": weekly_status})
        elif weekly_status["warning"]:
            self._trigger_alert("budget_warning", {"period": "weekly", "status": weekly_status})

        if monthly_status["exceeded"]:
            self._trigger_alert("budget_exceeded", {"period": "monthly", "status": monthly_status})
        elif monthly_status["warning"]:
            self._trigger_alert("budget_warning", {"period": "monthly", "status": monthly_status})

        return {
            "daily": daily_status,
            "weekly": weekly_status,
            "monthly": monthly_status,
        }

    def can_proceed(self) -> bool:
        """
        Check if API call can proceed based on budget.

        Returns:
            True if call can proceed, False if budget exceeded and auto-stop enabled

        Example:
            if manager.can_proceed():
                response = client.generate_content(...)
            else:
                logger.error("Budget exceeded, cannot proceed")
        """
        if not self.budget.enable_auto_stop:
            return True

        status = self.check_budget_status()

        # Check if any limit is exceeded
        if status["daily"]["exceeded"] or status["weekly"]["exceeded"] or status["monthly"]["exceeded"]:
            logger.error("Budget exceeded, auto-stop enabled")
            return False

        return True

    def print_budget_report(self):
        """Print detailed budget report"""
        status = self.check_budget_status()

        print("\n" + "=" * 70)
        print("Gemini API Budget Report")
        print("=" * 70)

        def print_period(name: str, data: Dict):
            print(f"\n{name}:")
            if data["limit"] is None:
                print(f"  No limit set")
                print(f"  Current cost: ¥{data['used']:.2f}")
            else:
                print(f"  Limit: ¥{data['limit']:.2f}")
                print(f"  Used: ¥{data['used']:.2f} ({data['percentage']*100:.1f}%)")
                if data["exceeded"]:
                    print(f"  Status: ❌ EXCEEDED")
                elif data["warning"]:
                    print(f"  Status: ⚠️  WARNING")
                else:
                    print(f"  Status: ✅ OK")

        print_period("Daily", status["daily"])
        print_period("Weekly", status["weekly"])
        print_period("Monthly", status["monthly"])

        print(f"\nAlert threshold: {self.budget.alert_threshold*100:.0f}%")
        print(f"Auto-stop: {'✅ Enabled' if self.budget.enable_auto_stop else '❌ Disabled'}")
        print("=" * 70 + "\n")


# ==================== Global Instance ====================

_global_cost_manager: Optional[CostManager] = None


def get_cost_manager() -> CostManager:
    """
    Get or create global CostManager instance.

    Returns:
        Shared CostManager instance
    """
    global _global_cost_manager

    if _global_cost_manager is None:
        _global_cost_manager = CostManager()

    return _global_cost_manager


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example: Set up cost management
    manager = get_cost_manager()

    # Set budget
    manager.set_budget(
        daily_limit=500,
        monthly_limit=10000,
        alert_threshold=0.8,
        enable_auto_stop=False
    )

    # Add alert callback
    def print_alert(alert_type: str, data: Dict):
        print(f"ALERT: {alert_type}")
        print(f"Data: {data}")

    manager.add_alert_callback(print_alert)

    # Check budget
    if manager.can_proceed():
        print("✅ Can proceed with API call")

    # Print report
    manager.print_budget_report()
