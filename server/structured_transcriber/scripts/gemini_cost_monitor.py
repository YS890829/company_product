#!/usr/bin/env python3
"""
Gemini API Cost Monitor - CLI Tool

Provides cost tracking, budgeting, and monitoring for Gemini API usage.

Phase 3 Implementation: 2025-10-21

Usage:
    # View current status
    python scripts/gemini_cost_monitor.py status

    # Set budget
    python scripts/gemini_cost_monitor.py set-budget --daily 500 --monthly 10000

    # View detailed report
    python scripts/gemini_cost_monitor.py report --days 7

    # Export data
    python scripts/gemini_cost_monitor.py export --output costs.csv
"""

import sys
import argparse
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.gemini_cost_manager import get_cost_manager, CostManager
from src.core.gemini_client import get_usage_history, USAGE_TRACKING_FILE


def cmd_status(args):
    """Show current cost status"""
    manager = get_cost_manager()

    print("\n" + "=" * 70)
    print("Gemini API Cost Status")
    print("=" * 70)

    # Get recent stats
    stats_today = manager.get_usage_stats(days=1)
    stats_week = manager.get_usage_stats(days=7)
    stats_month = manager.get_usage_stats(days=30)

    print(f"\n📊 Usage Statistics:")
    print(f"  Today:     {stats_today['total_calls']:3d} calls, ¥{stats_today['total_cost']:8.2f}")
    print(f"  This week: {stats_week['total_calls']:3d} calls, ¥{stats_week['total_cost']:8.2f}")
    print(f"  This month:{stats_month['total_calls']:3d} calls, ¥{stats_month['total_cost']:8.2f}")

    # Budget status
    status = manager.check_budget_status()

    print(f"\n💰 Budget Status:")

    def print_budget_line(name: str, data: Dict):
        if data['limit'] is None:
            print(f"  {name:8s}: No limit set (used: ¥{data['used']:.2f})")
        else:
            status_icon = "❌" if data['exceeded'] else ("⚠️ " if data['warning'] else "✅")
            print(f"  {name:8s}: {status_icon} ¥{data['used']:6.2f} / ¥{data['limit']:6.2f} ({data['percentage']*100:5.1f}%)")

    print_budget_line("Daily", status['daily'])
    print_budget_line("Weekly", status['weekly'])
    print_budget_line("Monthly", status['monthly'])

    print(f"\n⚙️  Settings:")
    print(f"  Alert threshold: {manager.budget.alert_threshold*100:.0f}%")
    print(f"  Auto-stop:       {'✅ Enabled' if manager.budget.enable_auto_stop else '❌ Disabled'}")

    print("=" * 70 + "\n")


def cmd_set_budget(args):
    """Set budget limits"""
    manager = get_cost_manager()

    manager.set_budget(
        daily_limit=args.daily,
        weekly_limit=args.weekly,
        monthly_limit=args.monthly,
        alert_threshold=args.threshold,
        enable_auto_stop=args.auto_stop
    )

    print("\n✅ Budget updated successfully!")
    print(f"   Daily limit:   {f'¥{args.daily}' if args.daily else 'Not set'}")
    print(f"   Weekly limit:  {f'¥{args.weekly}' if args.weekly else 'Not set'}")
    print(f"   Monthly limit: {f'¥{args.monthly}' if args.monthly else 'Not set'}")
    print(f"   Alert threshold: {args.threshold*100:.0f}%")
    print(f"   Auto-stop: {'Enabled' if args.auto_stop else 'Disabled'}\n")


def cmd_report(args):
    """Generate detailed cost report"""
    manager = get_cost_manager()

    print("\n" + "=" * 70)
    print(f"Gemini API Cost Report (Last {args.days} Days)")
    print("=" * 70)

    history = get_usage_history(days=args.days)

    if not history:
        print("\n⚠️  No usage data found for this period.\n")
        return

    # Calculate statistics
    total_calls = len(history)
    free_calls = sum(1 for h in history if h['tier'] == 'free')
    paid_calls = sum(1 for h in history if h['tier'] == 'paid')
    fallback_calls = sum(1 for h in history if h.get('was_fallback', False))
    errors = sum(1 for h in history if h.get('error'))

    # Calculate costs
    total_cost = 0.0
    model_costs = {}
    daily_costs = {}

    for entry in history:
        tier = entry.get('tier', 'free')
        model = entry.get('model', 'gemini-2.5-flash')
        tokens = entry.get('tokens', 0)
        date = entry['timestamp'][:10]

        # Estimate token split
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)

        cost = manager.calculate_cost(tier, model, input_tokens, output_tokens)
        total_cost += cost

        # Track by model
        if model not in model_costs:
            model_costs[model] = {'calls': 0, 'cost': 0.0}
        model_costs[model]['calls'] += 1
        model_costs[model]['cost'] += cost

        # Track by day
        if date not in daily_costs:
            daily_costs[date] = {'calls': 0, 'cost': 0.0}
        daily_costs[date]['calls'] += 1
        daily_costs[date]['cost'] += cost

    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Period:         {history[0]['timestamp'][:10]} to {history[-1]['timestamp'][:10]}")
    print(f"  Total calls:    {total_calls}")
    print(f"  Free tier:      {free_calls} ({free_calls/total_calls*100:.1f}%)")
    print(f"  Paid tier:      {paid_calls} ({paid_calls/total_calls*100:.1f}%)")
    print(f"  Fallback events:{fallback_calls}")
    print(f"  Errors:         {errors}")
    print(f"  Total cost:     ¥{total_cost:.2f}")

    # Print by model
    if model_costs:
        print(f"\n📱 By Model:")
        for model, data in sorted(model_costs.items(), key=lambda x: x[1]['cost'], reverse=True):
            print(f"  {model:25s}: {data['calls']:4d} calls, ¥{data['cost']:8.2f}")

    # Print daily breakdown
    if args.breakdown and daily_costs:
        print(f"\n📅 Daily Breakdown:")
        for date in sorted(daily_costs.keys(), reverse=True):
            data = daily_costs[date]
            print(f"  {date}: {data['calls']:4d} calls, ¥{data['cost']:8.2f}")

    # Budget comparison
    status = manager.check_budget_status()
    print(f"\n💰 Budget Status:")
    if status['daily']['limit']:
        print(f"  Daily:   ¥{status['daily']['used']:6.2f} / ¥{status['daily']['limit']:6.2f} ({status['daily']['percentage']*100:5.1f}%)")
    if status['monthly']['limit']:
        print(f"  Monthly: ¥{status['monthly']['used']:6.2f} / ¥{status['monthly']['limit']:6.2f} ({status['monthly']['percentage']*100:5.1f}%)")

    print("=" * 70 + "\n")


def cmd_export(args):
    """Export usage data to CSV"""
    history = get_usage_history(days=args.days)

    if not history:
        print("\n⚠️  No usage data found for this period.\n")
        return

    output_path = Path(args.output)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'timestamp', 'model', 'tier', 'was_fallback', 'tokens', 'error'
        ])
        writer.writeheader()
        writer.writerows(history)

    print(f"\n✅ Exported {len(history)} records to {output_path}\n")


def cmd_clear(args):
    """Clear usage history"""
    if not args.confirm:
        print("\n⚠️  This will delete all usage history!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.\n")
            return

    if USAGE_TRACKING_FILE.exists():
        # Backup before clearing
        backup_path = USAGE_TRACKING_FILE.with_suffix('.jsonl.backup')
        USAGE_TRACKING_FILE.rename(backup_path)
        print(f"\n✅ Usage history cleared (backup saved to {backup_path})\n")
    else:
        print("\n⚠️  No usage history file found.\n")


def cmd_alerts(args):
    """View recent alerts"""
    from src.core.gemini_cost_manager import COST_ALERTS_FILE

    if not COST_ALERTS_FILE.exists():
        print("\n⚠️  No alerts found.\n")
        return

    print("\n" + "=" * 70)
    print(f"Recent Alerts (Last {args.days} Days)")
    print("=" * 70)

    cutoff = datetime.now() - timedelta(days=args.days)
    alerts = []

    with open(COST_ALERTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if timestamp >= cutoff:
                    alerts.append(entry)
            except Exception as e:
                continue

    if not alerts:
        print(f"\n✅ No alerts in the last {args.days} days.\n")
        return

    for alert in sorted(alerts, key=lambda x: x['timestamp'], reverse=True):
        timestamp = alert['timestamp'][:19]
        alert_type = alert['type']
        data = alert['data']

        icon = "⚠️ " if 'warning' in alert_type else "❌"
        print(f"\n{icon} {timestamp} - {alert_type}")
        if 'period' in data:
            period_data = data['status']
            print(f"   Period: {data['period']}")
            print(f"   Used: ¥{period_data['used']:.2f} / ¥{period_data['limit']:.2f} ({period_data['percentage']*100:.1f}%)")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Gemini API Cost Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View current status
  %(prog)s status

  # Set daily budget of ¥500
  %(prog)s set-budget --daily 500

  # Set monthly budget with auto-stop
  %(prog)s set-budget --monthly 10000 --auto-stop

  # Generate 7-day report
  %(prog)s report --days 7 --breakdown

  # Export data to CSV
  %(prog)s export --output costs.csv --days 30

  # View recent alerts
  %(prog)s alerts --days 7
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status command
    subparsers.add_parser('status', help='Show current cost status')

    # Set budget command
    budget_parser = subparsers.add_parser('set-budget', help='Set budget limits')
    budget_parser.add_argument('--daily', type=float, help='Daily cost limit (JPY)')
    budget_parser.add_argument('--weekly', type=float, help='Weekly cost limit (JPY)')
    budget_parser.add_argument('--monthly', type=float, help='Monthly cost limit (JPY)')
    budget_parser.add_argument('--threshold', type=float, default=0.8, help='Alert threshold (0.0-1.0, default: 0.8)')
    budget_parser.add_argument('--auto-stop', action='store_true', help='Enable auto-stop on budget exceeded')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate cost report')
    report_parser.add_argument('--days', type=int, default=7, help='Number of days to report (default: 7)')
    report_parser.add_argument('--breakdown', action='store_true', help='Show daily breakdown')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export usage data to CSV')
    export_parser.add_argument('--output', type=str, default='gemini_costs.csv', help='Output file path')
    export_parser.add_argument('--days', type=int, default=30, help='Number of days to export (default: 30)')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear usage history')
    clear_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')

    # Alerts command
    alerts_parser = subparsers.add_parser('alerts', help='View recent alerts')
    alerts_parser.add_argument('--days', type=int, default=7, help='Number of days (default: 7)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    commands = {
        'status': cmd_status,
        'set-budget': cmd_set_budget,
        'report': cmd_report,
        'export': cmd_export,
        'clear': cmd_clear,
        'alerts': cmd_alerts,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
