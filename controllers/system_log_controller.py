"""בקר יומן המערכת (SystemLog) — מתאים למחלקת SystemLog בתרשים המחלקות (Module 1)."""
from db.database import Database, now_ts


class SystemLogController:
    def __init__(self, db: Database):
        self.db = db

    def logChange(self, userId: int, entityId: int, actionType: str, entityName: str) -> int:
        ts = now_ts()
        return self.db.run("""
            INSERT INTO system_log(action_type,user_id,entity_id,entity_name,timestamp,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?)
        """, (actionType, userId, entityId, entityName, ts, ts, ts))

    def getHistory(self):
        return self.db.query("""
            SELECT sl.change_id, sl.action_type, sl.entity_name, sl.entity_id, sl.timestamp,
                   u.full_name AS user_name
            FROM system_log sl
            JOIN users u ON sl.user_id = u.user_id
            ORDER BY sl.timestamp DESC, sl.change_id DESC
        """)
