#!/usr/bin/env python3.11
"""
API Key Management Script

Usage:
    python3.11 scripts/manage_keys.py create <name> <email> [institution]
    python3.11 scripts/manage_keys.py list
    python3.11 scripts/manage_keys.py deactivate <key_id>
    python3.11 scripts/manage_keys.py stats <key_id>
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.auth import create_researcher_key, create_admin_key


def create_key(name: str, email: str, institution: str = None):
    """Create a new API key"""
    print(f"Creating API key for {name} ({email})...")

    key_id, api_key = create_researcher_key(
        owner_name=name,
        owner_email=email,
        institution=institution
    )

    print("\n✅ API Key created successfully!")
    print(f"\nKey ID: {key_id}")
    print(f"API Key: {api_key}")
    print("\n⚠️  IMPORTANT: Save this key securely!")
    print("   This is the only time you will see the full key.")
    print("\nThe key owner should use it in requests:")
    print(f'  curl -H "X-API-Key: {api_key}" https://api.aybllc.org/v1/health')


def create_admin():
    """Create admin API key"""
    print("Creating admin API key...")

    key_id, api_key = create_admin_key()

    print("\n✅ Admin API Key created!")
    print(f"\nKey ID: {key_id}")
    print(f"API Key: {api_key}")
    print("\n⚠️  Save this key securely!")


def list_keys():
    """List all API keys"""
    import sqlite3

    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id, owner_name, owner_email, institution,
               created_at, expires_at, is_active, daily_limit, monthly_limit
        FROM api_keys
        ORDER BY created_at DESC
    """)

    keys = cursor.fetchall()
    conn.close()

    if not keys:
        print("No API keys found.")
        return

    print("\n=== API Keys ===\n")
    for key in keys:
        status = "✅ Active" if key['is_active'] else "❌ Inactive"
        expires = key['expires_at'] if key['expires_at'] else "Never"

        print(f"Key ID: {key['key_id']}")
        print(f"  Owner: {key['owner_name']} ({key['owner_email']})")
        if key['institution']:
            print(f"  Institution: {key['institution']}")
        print(f"  Status: {status}")
        print(f"  Created: {key['created_at']}")
        print(f"  Expires: {expires}")
        print(f"  Limits: {key['daily_limit']}/day, {key['monthly_limit']}/month")
        print()


def deactivate_key(key_id: str):
    """Deactivate an API key"""
    # Check if key exists
    key_info = db.get_key_info(key_id)
    if not key_info:
        print(f"❌ Key not found: {key_id}")
        return

    print(f"Deactivating key: {key_id}")
    print(f"  Owner: {key_info['owner_name']} ({key_info['owner_email']})")

    # Confirm
    confirm = input("\nAre you sure? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    db.deactivate_key(key_id)
    print("✅ Key deactivated successfully!")


def show_stats(key_id: str):
    """Show usage statistics for a key"""
    # Get key info
    key_info = db.get_key_info(key_id)
    if not key_info:
        print(f"❌ Key not found: {key_id}")
        return

    # Get usage stats
    stats = db.get_usage_stats(key_id)

    print(f"\n=== Statistics for {key_id} ===\n")
    print(f"Owner: {key_info['owner_name']} ({key_info['owner_email']})")
    if key_info['institution']:
        print(f"Institution: {key_info['institution']}")
    print(f"\nStatus: {'✅ Active' if key_info['is_active'] else '❌ Inactive'}")
    print(f"Created: {key_info['created_at']}")
    print(f"Expires: {key_info['expires_at'] if key_info['expires_at'] else 'Never'}")
    print(f"\n--- Usage ---")
    print(f"Today: {stats['requests_today']}/{key_info['daily_limit']}")
    print(f"This month: {stats['requests_month']}/{key_info['monthly_limit']}")

    # Calculate percentages
    daily_pct = (stats['requests_today'] / key_info['daily_limit']) * 100
    monthly_pct = (stats['requests_month'] / key_info['monthly_limit']) * 100

    print(f"\nDaily usage: {daily_pct:.1f}%")
    print(f"Monthly usage: {monthly_pct:.1f}%")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: manage_keys.py create <name> <email> [institution]")
            sys.exit(1)

        name = sys.argv[2]
        email = sys.argv[3]
        institution = sys.argv[4] if len(sys.argv) > 4 else None

        create_key(name, email, institution)

    elif command == "admin":
        create_admin()

    elif command == "list":
        list_keys()

    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("Usage: manage_keys.py deactivate <key_id>")
            sys.exit(1)

        key_id = sys.argv[2]
        deactivate_key(key_id)

    elif command == "stats":
        if len(sys.argv) < 3:
            print("Usage: manage_keys.py stats <key_id>")
            sys.exit(1)

        key_id = sys.argv[2]
        show_stats(key_id)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
