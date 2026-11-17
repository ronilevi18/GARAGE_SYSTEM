"""
בקר הזדהות — ממפה למחלקת User בתרשים (login(), checkPermissions()).
מסך הכניסה נדרש בחלק ג': כניסה -> תפריט ראשי -> דרישות.
"""
from db.database import Database
from models.entities import User


class AuthController:
    def __init__(self, db: Database):
        self.db = db

    def login(self, username: str, password: str):
        """User.login() — טוען משתמש מתוך בסיס הנתונים (לא קבוע בקוד)."""
        row = self.db.query_one("""
            SELECT u.*, e.full_name AS employee_name
            FROM users u
            LEFT JOIN employees e ON u.employee_id = e.employee_id
            WHERE u.username = ? AND u.password = ?
        """, (username.strip(), password.strip()))
        return row

    def checkPermissions(self, user: dict, allowed_roles: list) -> bool:
        """User.checkPermissions() — בדיקת הרשאה לפי תפקיד."""
        if not user:
            return False
        u = User(userId=user.get("user_id"), role=user.get("role", ""))
        return u.checkPermissions(allowed_roles)
