import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))

# Retention in days
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "30"))

def log_audit_event(user_id: str, action: str, status: str, details: Dict[str, Any] = None) -> None:
    """
    Writes a structured audit log event to a separate audit log file.
    Schema includes timestamp, user_id, action, status, and details.
    """
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "action": action,
        "status": status,
        "details": details or {}
    }
    
    try:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logging.error(f"Failed to write audit log: {e}")

def apply_retention_policy() -> None:
    """
    Cleans up audit logs older than the retention period.
    """
    if not AUDIT_LOG_PATH.exists():
        return
        
    cutoff_date = datetime.utcnow() - timedelta(days=AUDIT_RETENTION_DAYS)
    retained_logs = []
    
    try:
        with AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_date = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)
                    if event_date >= cutoff_date:
                        retained_logs.append(line)
                except Exception:
                    # Keep invalid lines or handle differently
                    retained_logs.append(line)
                    
        with AUDIT_LOG_PATH.open("w", encoding="utf-8") as f:
            for line in retained_logs:
                f.write(line)
    except Exception as e:
        logging.error(f"Failed to apply audit retention policy: {e}")
