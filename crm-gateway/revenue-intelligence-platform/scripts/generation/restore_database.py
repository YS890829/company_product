#!/usr/bin/env python3
"""
データベース復元スクリプト
schema.sql と seed.sql を実行
"""

import psycopg2

def execute_sql_file(filepath: str):
    """Execute SQL file"""
    print(f"Executing {filepath}...")

    with open(filepath, 'r') as f:
        sql = f.read()

    conn = psycopg2.connect(
        host='127.0.0.1',
        port=54322,
        database='postgres',
        user='postgres',
        password='postgres'
    )

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"✓ {filepath} executed successfully")
    except Exception as e:
        print(f"❌ Error executing {filepath}: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    print("=" * 80)
    print("データベース復元開始")
    print("=" * 80)
    print()

    # Execute schema.sql
    execute_sql_file('/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/database/schema.sql')
    print()

    # Execute seed.sql (if exists and contains data)
    try:
        execute_sql_file('/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/database/seed.sql')
    except FileNotFoundError:
        print("⚠️  seed.sql not found, skipping")
    except Exception as e:
        print(f"⚠️  seed.sql failed: {str(e)}, continuing without seed data")

    print()
    print("=" * 80)
    print("✅ データベース復元完了")
    print("=" * 80)


if __name__ == '__main__':
    main()
