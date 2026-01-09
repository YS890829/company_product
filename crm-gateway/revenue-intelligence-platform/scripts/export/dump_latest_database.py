#!/usr/bin/env python3
"""
最新のデータベーススキーマとデータをダンプするスクリプト

Usage:
    python3 dump_latest_database.py
"""

import os
import sys
from pathlib import Path
from supabase import create_client
import json
from datetime import datetime

# Supabase接続設定
SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0')

# データベース接続情報（PostgreSQL直接接続用）
DB_HOST = '127.0.0.1'
DB_PORT = 54322
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'postgres'

def dump_schema_and_data():
    """スキーマとデータをダンプ"""
    try:
        import psycopg2
        from psycopg2 import sql

        print("=" * 80)
        print("最新データベースダンプ")
        print("=" * 80)
        print()

        # PostgreSQL接続
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor()

        # 1. スキーマダンプ（CREATE TABLE文）
        print("Step 1: スキーマダンプ中...")
        schema_sql = []

        # テーブル一覧取得
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name IN ('companies', 'deals', 'meetings', 'emails')
            ORDER BY
                CASE table_name
                    WHEN 'companies' THEN 1
                    WHEN 'deals' THEN 2
                    WHEN 'meetings' THEN 3
                    WHEN 'emails' THEN 4
                END
        """)
        tables = [row[0] for row in cur.fetchall()]

        schema_sql.append("-- " + "=" * 76)
        schema_sql.append("-- Revenue Intelligence Platform - Database Schema (Latest)")
        schema_sql.append("-- " + "=" * 76)
        schema_sql.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        schema_sql.append(f"-- Tables: {', '.join(tables)}")
        schema_sql.append("-- " + "=" * 76)
        schema_sql.append("")

        for table in tables:
            print(f"  - {table} テーブル...")

            # DROP TABLE文
            schema_sql.append(f"-- {table} テーブル")
            schema_sql.append(f"DROP TABLE IF EXISTS {table} CASCADE;")
            schema_sql.append("")

            # CREATE TABLE文（カラム定義）
            cur.execute(f"""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    column_default,
                    is_nullable,
                    udt_name
                FROM information_schema.columns
                WHERE table_name = '{table}'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()

            create_lines = [f"CREATE TABLE {table} ("]

            for i, (col_name, data_type, char_len, col_default, nullable, udt_name) in enumerate(columns):
                # データ型変換
                if data_type == 'USER-DEFINED':
                    col_type = udt_name
                elif data_type == 'ARRAY':
                    col_type = 'TEXT[]'
                elif data_type == 'character varying':
                    col_type = f'VARCHAR({char_len})' if char_len else 'TEXT'
                elif data_type == 'timestamp with time zone':
                    col_type = 'TIMESTAMP WITH TIME ZONE'
                elif data_type == 'numeric':
                    col_type = 'DECIMAL'
                else:
                    col_type = data_type.upper()

                # カラム定義
                col_def = f"  {col_name} {col_type}"

                # DEFAULT値
                if col_default:
                    if 'gen_random_uuid()' in col_default:
                        col_def += " DEFAULT gen_random_uuid()"
                    elif 'now()' in col_default.lower():
                        col_def += " DEFAULT NOW()"
                    elif "'[]'::jsonb" in col_default:
                        col_def += " DEFAULT '[]'::JSONB"
                    else:
                        col_def += f" DEFAULT {col_default}"

                # NOT NULL制約
                if nullable == 'NO':
                    col_def += " NOT NULL"

                # カンマ
                if i < len(columns) - 1:
                    col_def += ","

                create_lines.append(col_def)

            create_lines.append(");")
            schema_sql.extend(create_lines)
            schema_sql.append("")

            # PRIMARY KEY制約
            cur.execute(f"""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = '{table}'
                  AND tc.constraint_type = 'PRIMARY KEY'
            """)
            pk_cols = cur.fetchall()
            if pk_cols:
                pk_col = pk_cols[0][0]
                schema_sql.append(f"ALTER TABLE {table} ADD PRIMARY KEY ({pk_col});")
                schema_sql.append("")

            # FOREIGN KEY制約
            cur.execute(f"""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = '{table}'
                  AND tc.constraint_type = 'FOREIGN KEY'
            """)
            fk_constraints = cur.fetchall()
            for col_name, foreign_table, foreign_col in fk_constraints:
                schema_sql.append(
                    f"ALTER TABLE {table} ADD FOREIGN KEY ({col_name}) "
                    f"REFERENCES {foreign_table}({foreign_col}) ON DELETE CASCADE;"
                )
                schema_sql.append("")

        # schema_new.sqlに書き込み
        schema_file = Path(__file__).parent.parent.parent / 'database' / 'schema_new.sql'
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(schema_sql))

        print(f"✅ スキーマダンプ完了: {schema_file}")
        print(f"   サイズ: {schema_file.stat().st_size:,} bytes")
        print()

        # 2. データダンプ（INSERT文）
        print("Step 2: データダンプ中...")

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        data_sql = []
        data_sql.append("-- " + "=" * 76)
        data_sql.append("-- Revenue Intelligence Platform - Seed Data (Latest)")
        data_sql.append("-- " + "=" * 76)
        data_sql.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        data_sql.append("-- " + "=" * 76)
        data_sql.append("")

        total_records = 0

        for table in tables:
            print(f"  - {table} テーブル...")

            # 全データ取得（ページネーション対応）
            all_records = []
            page_size = 1000
            offset = 0

            while True:
                result = supabase.table(table).select('*').range(offset, offset + page_size - 1).execute()
                records = result.data

                if not records:
                    break

                all_records.extend(records)
                offset += page_size

                if len(records) < page_size:
                    break

            records = all_records

            if not records:
                print(f"    （データなし）")
                continue

            print(f"    {len(records):,}件")
            total_records += len(records)

            data_sql.append(f"-- {table} テーブル ({len(records):,}件)")

            # カラム名取得
            columns = list(records[0].keys())

            for record in records:
                values = []
                for col in columns:
                    val = record[col]
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, str):
                        # エスケープ処理
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, (list, dict)):
                        # JSON/JSONB
                        json_str = json.dumps(val, ensure_ascii=False).replace("'", "''")
                        values.append(f"'{json_str}'::JSONB")
                    elif isinstance(val, bool):
                        values.append('TRUE' if val else 'FALSE')
                    else:
                        values.append(str(val))

                insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                data_sql.append(insert_sql)

            data_sql.append("")

        # seed_new.sqlに書き込み
        seed_file = Path(__file__).parent.parent.parent / 'database' / 'seed_new.sql'
        with open(seed_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(data_sql))

        print(f"✅ データダンプ完了: {seed_file}")
        print(f"   サイズ: {seed_file.stat().st_size:,} bytes")
        print(f"   総レコード数: {total_records:,}件")
        print()

        # 3. サマリー
        print("=" * 80)
        print("ダンプ完了サマリー")
        print("=" * 80)
        print(f"schema_new.sql: {schema_file.stat().st_size:,} bytes")
        print(f"seed_new.sql: {seed_file.stat().st_size:,} bytes")
        print(f"総レコード数: {total_records:,}件")
        print()
        print("次のステップ:")
        print("  mv database/schema_new.sql database/schema.sql")
        print("  mv database/seed_new.sql database/seed.sql")

        cur.close()
        conn.close()

        return True

    except ImportError:
        print("❌ エラー: psycopg2がインストールされていません")
        print("   インストール: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = dump_schema_and_data()
    sys.exit(0 if success else 1)
