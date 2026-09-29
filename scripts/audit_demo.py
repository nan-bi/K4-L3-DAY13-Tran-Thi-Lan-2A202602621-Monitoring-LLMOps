import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent dir to path so we can import app module
sys.path.append(str(Path(__file__).parent.parent))
from app.audit import log_audit_event, apply_retention_policy, AUDIT_LOG_PATH

def simulate_events():
    print(f"--- Ghi log audit giả lập vào {AUDIT_LOG_PATH} ---")
    log_audit_event("user_123", "LOGIN", "SUCCESS", {"ip": "192.168.1.1"})
    log_audit_event("user_456", "DATA_ACCESS", "DENIED", {"resource": "finance_db"})
    log_audit_event("user_123", "UPDATE_RECORD", "SUCCESS", {"table": "users", "id": 789})
    print("Đã tạo 3 audit events mới.")

def query_audit_logs(user_id=None, action=None):
    print(f"\n--- Truy vấn Audit Log (User: {user_id}, Action: {action}) ---")
    if not AUDIT_LOG_PATH.exists():
        print("Audit log không tồn tại.")
        return
        
    with AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                match_user = user_id is None or event.get("user_id") == user_id
                match_action = action is None or event.get("action") == action
                
                if match_user and match_action:
                    print(json.dumps(event, indent=2))
            except Exception:
                pass

def demo():
    simulate_events()
    
    # Minh họa truy vấn
    query_audit_logs(user_id="user_123")
    query_audit_logs(action="DATA_ACCESS")
    
    # Minh họa retention policy
    print("\n--- Áp dụng Retention Policy (30 days default) ---")
    
    # Thêm một log cũ giả lập
    old_event = {
        "timestamp": (datetime.utcnow() - timedelta(days=40)).isoformat() + "Z",
        "user_id": "old_user",
        "action": "OLD_ACTION",
        "status": "SUCCESS",
        "details": {}
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(old_event) + "\n")
        
    print("Đã thêm 1 sự kiện giả lập cách đây 40 ngày.")
    
    apply_retention_policy()
    print("Đã chạy apply_retention_policy().")
    
    print("\n--- Kiểm tra lại số lượng log sau khi dọn dẹp ---")
    count = sum(1 for _ in AUDIT_LOG_PATH.open("r", encoding="utf-8"))
    print(f"Tổng số bản ghi hiện tại: {count} (Các sự kiện cũ hơn 30 ngày đã bị xóa)")

if __name__ == "__main__":
    demo()
