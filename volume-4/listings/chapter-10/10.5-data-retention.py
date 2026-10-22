# Applied AI Engineering, Volume IV, Chapter 10
# Section 10.5, Data Retention
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Retention policy enforcement (pseudocode — adapt to your database)
from datetime import datetime, timedelta, timezone

def purge_expired_logs(db_conn, retention_days: int = 90) -> int:
    """Delete conversation logs older than retention_days. Returns count deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cursor = db_conn.execute(
        "DELETE FROM conversation_logs WHERE created_at < ? RETURNING id",
        (cutoff.isoformat(),)
    )
    count = cursor.rowcount
    db_conn.commit()
    return count
