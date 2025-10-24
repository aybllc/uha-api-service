"""
Database management for API keys and request logging
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import bcrypt

from .config import settings


class Database:
    """Database manager for API keys and request logs"""

    def __init__(self, db_path: Path = settings.DATABASE_PATH):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # API Keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                key_hash TEXT NOT NULL UNIQUE,
                owner_name TEXT NOT NULL,
                owner_email TEXT NOT NULL,
                institution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                daily_limit INTEGER DEFAULT 1000,
                monthly_limit INTEGER DEFAULT 50000,
                notes TEXT
            )
        """)

        # Request logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_time_ms INTEGER,
                status_code INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER,
                error_message TEXT,
                FOREIGN KEY (key_id) REFERENCES api_keys(key_id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_key_timestamp
            ON request_logs(key_id, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp
            ON request_logs(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_keys_active
            ON api_keys(is_active)
        """)

        conn.commit()
        conn.close()

    def generate_api_key(self) -> str:
        """Generate a new API key"""
        # Format: uha_live_<32-char-hex>
        random_part = secrets.token_hex(16)
        return f"uha_live_{random_part}"

    def hash_key(self, api_key: str) -> str:
        """Hash an API key using bcrypt"""
        return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

    def verify_key(self, api_key: str, key_hash: str) -> bool:
        """Verify an API key against its hash"""
        return bcrypt.checkpw(api_key.encode(), key_hash.encode())

    def create_api_key(
        self,
        owner_name: str,
        owner_email: str,
        institution: Optional[str] = None,
        daily_limit: int = 1000,
        monthly_limit: int = 50000,
        expires_days: Optional[int] = 365,
        notes: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Create a new API key

        Returns: (key_id, api_key)
        """
        # Generate key and hash
        api_key = self.generate_api_key()
        key_hash = self.hash_key(api_key)

        # Generate key ID
        key_id = f"key_{owner_email.split('@')[0]}_{secrets.token_hex(4)}"

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_keys (
                key_id, key_hash, owner_name, owner_email, institution,
                expires_at, daily_limit, monthly_limit, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            key_id, key_hash, owner_name, owner_email, institution,
            expires_at, daily_limit, monthly_limit, notes
        ))

        conn.commit()
        conn.close()

        return key_id, api_key

    def authenticate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate an API key

        Returns: Key info dict if valid, None if invalid
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all active keys (small table, this is fine)
        cursor.execute("""
            SELECT * FROM api_keys
            WHERE is_active = 1
            AND (expires_at IS NULL OR expires_at > ?)
        """, (datetime.utcnow(),))

        for row in cursor.fetchall():
            if self.verify_key(api_key, row['key_hash']):
                conn.close()
                return dict(row)

        conn.close()
        return None

    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key information"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM api_keys WHERE key_id = ?", (key_id,))
        row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None

    def deactivate_key(self, key_id: str):
        """Deactivate an API key"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE api_keys SET is_active = 0 WHERE key_id = ?
        """, (key_id,))

        conn.commit()
        conn.close()

    def log_request(
        self,
        key_id: Optional[str],
        endpoint: str,
        method: str,
        status_code: int,
        processing_time_ms: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log an API request"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO request_logs (
                key_id, endpoint, method, status_code, processing_time_ms,
                ip_address, user_agent, request_size_bytes, response_size_bytes,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            key_id, endpoint, method, status_code, processing_time_ms,
            ip_address, user_agent, request_size, response_size, error_message
        ))

        conn.commit()
        conn.close()

    def get_usage_stats(self, key_id: str) -> Dict[str, int]:
        """Get usage statistics for a key"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Requests today
        cursor.execute("""
            SELECT COUNT(*) as count FROM request_logs
            WHERE key_id = ? AND DATE(timestamp) = DATE('now')
        """, (key_id,))
        requests_today = cursor.fetchone()['count']

        # Requests this month
        cursor.execute("""
            SELECT COUNT(*) as count FROM request_logs
            WHERE key_id = ?
            AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        """, (key_id,))
        requests_month = cursor.fetchone()['count']

        conn.close()

        return {
            'requests_today': requests_today,
            'requests_month': requests_month
        }

    def check_rate_limit(self, key_id: str, key_info: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if key has exceeded rate limits

        Returns: (allowed: bool, reason: str)
        """
        stats = self.get_usage_stats(key_id)

        if stats['requests_today'] >= key_info['daily_limit']:
            return False, f"Daily limit exceeded ({key_info['daily_limit']} requests/day)"

        if stats['requests_month'] >= key_info['monthly_limit']:
            return False, f"Monthly limit exceeded ({key_info['monthly_limit']} requests/month)"

        return True, "OK"

    def cleanup_old_logs(self, days: int = 90):
        """Delete logs older than specified days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = datetime.utcnow() - timedelta(days=days)
        cursor.execute("""
            DELETE FROM request_logs WHERE timestamp < ?
        """, (cutoff,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted


# Global database instance
db = Database()
