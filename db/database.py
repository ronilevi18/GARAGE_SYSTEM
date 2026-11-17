"""
שכבת בסיס הנתונים (Database) — מתאימה למחלקת Database בתרשימי המחלקות.
שמות השיטות הציבוריות תואמים בדיוק לתרשימים:
  - Module 1: queryExistingCustomersAndVehicles(), saveNewEntities()
  - Module 2: fetchRawTasksByEmployee(employeeId)
  - Module 3: getOpenWorkOrders(filters), getStatusHistoryById(workOrderId), saveReportMetrics(metrics)
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "garage.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"


def now_ts() -> str:
    """חותמת זמן מדויקת לרמת השנייה — לצורך אימות עדכון בזמן אמת (סעיף 8)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# שרשרת התחנות הפיזית במוסך (דרישה 20) — מפתח טכני -> תווית עברית
STATION_CHAIN = ["Reception", "BodyWork", "Paint", "WaitingParts", "WaitingAssessor", "QualityCheck"]
STATION_HE = {
    "Reception": "קבלה", "BodyWork": "פחחות", "Paint": "צבע",
    "WaitingParts": "המתנה לחלקים", "WaitingAssessor": "המתנה לשמאי", "QualityCheck": "בדיקת איכות",
}


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path

    # ---------- תשתית פנימית ----------
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            conn.commit()

    def _fetch_all(self, query, params=()):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def _fetch_one(self, query, params=()):
        with self.connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def _execute(self, query, params=()):
        with self.connect() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.lastrowid

    # ---------- Module 1 : Database (תרשים) ----------
    def queryExistingCustomersAndVehicles(self):
        """תרשים Sequence דרישה 3: 'Query all existing customers and vehicles'."""
        return self._fetch_all("""
            SELECT c.customer_id, c.name, c.phone_number, c.customer_type,
                   v.vehicle_id, v.license_plate, v.model, v.year, v.vehicle_type
            FROM customers c
            LEFT JOIN vehicles v ON c.customer_id = v.customer_id
            WHERE c.status = 'Active'
            ORDER BY c.name
        """)

    def saveNewEntities(self, customerDetails: dict, vehicleDetails: dict):
        """תרשים Sequence דרישה 3: 'Save new customer and vehicle entities'.
        מבצע «create» newCustomer ואז «create» newVehicle ומחזיר את המזהים."""
        ts = now_ts()
        ctype = customerDetails.get('customer_type') or 'Private'
        if ctype not in ('Private', 'Business'):
            ctype = 'Private'
        vtype = vehicleDetails.get('vehicle_type') or 'Private'
        if vtype not in ('Private', 'Business', 'Electric', 'Luxury'):
            vtype = 'Private'
        customer_id = self._execute("""
            INSERT INTO customers(customer_type,name,id_number,phone_number,address,notes,birth_date,business_id,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ctype,
            customerDetails.get('name', ''),
            customerDetails.get('id_number', ''),
            customerDetails.get('phone_number', ''),
            customerDetails.get('address', ''),
            customerDetails.get('notes', ''),
            customerDetails.get('birth_date', ''),
            customerDetails.get('business_id', ''),
            'Active', ts, ts
        ))
        vehicle_id = self._execute("""
            INSERT INTO vehicles(customer_id,license_plate,model,year,vehicle_type,km,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            customer_id,
            vehicleDetails.get('license_plate', ''),
            vehicleDetails.get('model', ''),
            int(vehicleDetails.get('year') or 0),
            vtype,
            int(vehicleDetails.get('km') or 0),
            'Active', ts, ts
        ))
        return customer_id, vehicle_id

    def saveWorkCase(self, workOrderDetails: dict) -> int:
        """תרשים Sequence דרישה 3: שמירת ההזמנה (נקראת מתוך saveWorkOrder של הקונטרולר)."""
        return self._execute("""
            INSERT INTO work_cases(case_number,customer_id,vehicle_id,accident_details,work_type,status,opened_by_user_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            workOrderDetails['case_number'], workOrderDetails['customer_id'], workOrderDetails['vehicle_id'],
            workOrderDetails['accident_details'], workOrderDetails.get('work_type', 'BodyRepair'),
            workOrderDetails['status'], workOrderDetails['opened_by_user_id'],
            workOrderDetails['created_at'], workOrderDetails['updated_at']
        ))

    def insertStatusHistory(self, work_case_id, old_status, new_status, user_id):
        ts = now_ts()
        return self._execute("""
            INSERT INTO status_history(work_case_id,old_status,new_status,changed_by_user_id,changed_at,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?)
        """, (work_case_id, old_status, new_status, user_id, ts, ts, ts))

    # ---------- Module 2 : Database (תרשים) ----------
    def fetchRawTasksByEmployee(self, employeeId: int):
        """תרשים Sequence דרישה 15: 'fetchRawTasksByEmployee(employeeId)' -> rawTaskList."""
        return self._fetch_all("""
            SELECT rt.task_id, wc.case_number, v.license_plate AS vehicle_number,
                   rt.task_name, rt.deadline, rt.status, rt.priority_level, rt.workload,
                   rt.employee_id, wc.work_case_id
            FROM repair_tasks rt
            JOIN work_cases wc ON rt.work_case_id = wc.work_case_id
            JOIN vehicles v ON wc.vehicle_id = v.vehicle_id
            WHERE rt.employee_id = ?
            ORDER BY rt.deadline ASC
        """, (employeeId,))

    # ---------- Module 3 : Database (תרשים) ----------
    def getOpenWorkOrders(self, filters: dict):
        """תרשים Sequence דרישה 20: 'getOpenWorkOrders(filters): List'."""
        q = """
            SELECT wc.work_case_id, wc.case_number, wc.status, wc.work_type,
                   wc.created_at, wc.updated_at,
                   c.name AS customer_name, v.license_plate, v.model
            FROM work_cases wc
            JOIN customers c ON wc.customer_id = c.customer_id
            JOIN vehicles v ON wc.vehicle_id = v.vehicle_id
            WHERE wc.status = 'Open'
        """
        params = []
        if filters.get('date_from'):
            q += " AND date(wc.created_at) >= date(?)"; params.append(filters['date_from'])
        if filters.get('date_to'):
            q += " AND date(wc.created_at) <= date(?)"; params.append(filters['date_to'])
        if filters.get('work_type') and filters['work_type'] != 'All':
            q += " AND wc.work_type = ?"; params.append(filters['work_type'])
        q += " ORDER BY wc.created_at DESC"
        return self._fetch_all(q, tuple(params))

    def getStatusHistoryById(self, workOrderId: int):
        """תרשים Sequence דרישה 20: 'getStatusHistoryById(workOrderId): List'."""
        return self._fetch_all("""
            SELECT * FROM status_history WHERE work_case_id = ? ORDER BY changed_at ASC
        """, (workOrderId,))

    def saveReportMetrics(self, metrics: dict, report_name: str, filters: dict, user_id: int) -> int:
        """תרשים Sequence דרישה 20: 'saveReportMetrics(metrics: Map): boolean' (מחזיר report_id)."""
        ts = now_ts()
        return self._execute("""
            INSERT INTO generated_reports(report_name,filters_json,metrics_json,generated_by_user_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?)
        """, (report_name, json.dumps(filters, ensure_ascii=False), json.dumps(metrics, ensure_ascii=False), user_id, ts, ts))

    # ---------- שירות כללי לשכבת ה-GUI (קריאות תצוגה ישירות) ----------
    def query(self, sql, params=()):
        return self._fetch_all(sql, params)

    def query_one(self, sql, params=()):
        return self._fetch_one(sql, params)

    def run(self, sql, params=()):
        return self._execute(sql, params)

    # ---------- קידום סטטוס תיק עבודה (Open -> ... -> Closed) ----------
    def updateWorkCaseStatus(self, work_case_id, new_status, user_id):
        old = self.query_one("SELECT status FROM work_cases WHERE work_case_id=?", (work_case_id,))
        old_status = old['status'] if old else None
        ts = now_ts()
        self._execute("UPDATE work_cases SET status=?, updated_at=? WHERE work_case_id=?",
                      (new_status, ts, work_case_id))
        self.insertStatusHistory(work_case_id, old_status, new_status, user_id)
        return True

    def getActiveWorkCases(self):
        """תיקים שאינם סגורים — לתצוגת מעקב/קידום שלב במסך דרישה 3."""
        return self._fetch_all("""
            SELECT wc.work_case_id, wc.case_number, v.license_plate, wc.work_type,
                   wc.status, wc.created_at, wc.updated_at
            FROM work_cases wc JOIN vehicles v ON wc.vehicle_id = v.vehicle_id
            WHERE wc.status != 'Closed'
            ORDER BY wc.work_case_id DESC
        """)

    # ---------- דרישה 15: קידום סטטוס משימה + תצוגת מנהל ----------
    def updateRepairTaskStatus(self, task_id, new_status):
        ts = now_ts()
        self._execute("UPDATE repair_tasks SET status=?, updated_at=? WHERE task_id=?",
                      (new_status, ts, task_id))
        return True

    def fetchAllTasks(self):
        """תצוגת מנהל: משימות כל העובדים, כולל שם ותפקיד העובד."""
        return self._fetch_all("""
            SELECT rt.task_id, wc.case_number, v.license_plate AS vehicle_number,
                   rt.task_name, rt.deadline, rt.status, rt.priority_level, rt.workload,
                   rt.employee_id, e.full_name AS employee_name, e.role AS employee_role, wc.work_case_id
            FROM repair_tasks rt
            JOIN work_cases wc ON rt.work_case_id = wc.work_case_id
            JOIN vehicles v ON wc.vehicle_id = v.vehicle_id
            JOIN employees e ON rt.employee_id = e.employee_id
            ORDER BY rt.deadline ASC
        """)

    # ---------- דרישה 20: זמן בכל תחנה/שלב לכל רכב (לפי station_visits) ----------
    def getStationTimesByCase(self, work_case_id):
        """כמה שעות הרכב שהה בכל תחנה. תחנה פתוחה (left_at=NULL) נמדדת עד עכשיו."""
        from datetime import datetime
        visits = self._fetch_all(
            "SELECT station, entered_at, left_at FROM station_visits WHERE work_case_id=? ORDER BY entered_at ASC",
            (work_case_id,))
        times = {}
        for v in visits:
            start = datetime.strptime(v['entered_at'], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(v['left_at'], '%Y-%m-%d %H:%M:%S') if v['left_at'] else datetime.now()
            hours = round((end - start).total_seconds() / 3600, 1)
            times[v['station']] = round(times.get(v['station'], 0) + hours, 1)
        return times

    def getCurrentStationHours(self, work_case_id):
        """כמה שעות הרכב נמצא בתחנה הנוכחית (התחנה הפתוחה האחרונה)."""
        from datetime import datetime
        v = self._fetch_one(
            "SELECT station, entered_at FROM station_visits WHERE work_case_id=? AND left_at IS NULL ORDER BY entered_at DESC LIMIT 1",
            (work_case_id,))
        if not v:
            return (None, 0)
        start = datetime.strptime(v['entered_at'], '%Y-%m-%d %H:%M:%S')
        return (v['station'], round((datetime.now() - start).total_seconds() / 3600, 1))

    def moveToStation(self, work_case_id, station):
        """סוגר את התחנה הנוכחית ופותח חדשה (קידום בשרשרת)."""
        ts = now_ts()
        self._execute("UPDATE station_visits SET left_at=?, updated_at=? WHERE work_case_id=? AND left_at IS NULL",
                      (ts, ts, work_case_id))
        return self._execute("""INSERT INTO station_visits(work_case_id,station,entered_at,created_at,updated_at)
                                VALUES(?,?,?,?,?)""", (work_case_id, station, ts, ts, ts))

    # ---------- דרישה 15: תיקים בקבלה הממתינים לסיווג ע"י המנהל ----------
    def getCasesAwaitingAssignment(self):
        """תיקים שנמצאים בתחנת 'קבלה' (left_at IS NULL) ואין להם משימה פעילה."""
        return self._fetch_all("""
            SELECT wc.work_case_id, wc.case_number, wc.work_type, wc.accident_details,
                   v.license_plate, c.name AS customer_name
            FROM work_cases wc
            JOIN vehicles v ON wc.vehicle_id = v.vehicle_id
            JOIN customers c ON wc.customer_id = c.customer_id
            JOIN station_visits sv ON sv.work_case_id = wc.work_case_id
                 AND sv.station = 'Reception' AND sv.left_at IS NULL
            WHERE wc.status NOT IN ('Closed','Completed')
              AND NOT EXISTS (
                SELECT 1 FROM repair_tasks rt
                WHERE rt.work_case_id = wc.work_case_id
                  AND rt.status NOT IN ('Completed','Cancelled'))
            ORDER BY wc.work_case_id DESC
        """)

    def assignTaskToCase(self, work_case_id, employee_id, station, task_name, deadline, priority, user_id):
        """המנהל מסווג תיק: יוצר משימה לעובד, מקדם את הרכב לתחנה שנבחרה, ומיידע את העובד."""
        ts = now_ts()
        task_id = self._execute("""
            INSERT INTO repair_tasks(work_case_id,employee_id,task_name,deadline,status,priority_level,workload,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (work_case_id, employee_id, task_name, deadline, 'NotStarted', priority, 1, ts, ts))
        self.moveToStation(work_case_id, station)
        self.updateWorkCaseStatus(work_case_id, 'InProgress', user_id)
        emp = self.query_one("SELECT full_name FROM employees WHERE employee_id=?", (employee_id,))
        if emp:
            self.addNotification('Employee', emp['full_name'], 'RepairTask', task_id,
                                 f"הוקצתה לך משימה חדשה: {task_name}", user_id)
        return task_id

    # ---------- דיווח חריגה (דרישה 15, מסך עובד) ----------
    def addAnomalyReport(self, task_id, employee_id, description):
        ts = now_ts()
        return self._execute("""INSERT INTO anomaly_reports(task_id,employee_id,description,created_at,updated_at)
                                VALUES(?,?,?,?,?)""", (task_id, employee_id, description, ts, ts))

    def getAnomalyReports(self):
        """כל דיווחי החריגה — לתצוגת המנהל, כולל שם העובד והמשימה."""
        return self._fetch_all("""
            SELECT ar.report_id, ar.description, ar.created_at,
                   e.full_name AS employee_name, rt.task_name, wc.case_number
            FROM anomaly_reports ar
            JOIN employees e ON ar.employee_id = e.employee_id
            JOIN repair_tasks rt ON ar.task_id = rt.task_id
            JOIN work_cases wc ON rt.work_case_id = wc.work_case_id
            ORDER BY ar.report_id DESC
        """)

    # ---------- התראות לנמען מסוים (חלון קופץ לעובד) ----------
    def getNotificationsForRecipient(self, recipient_type, recipient_name):
        return self._fetch_all("""
            SELECT notification_id, message, recipient_seq, sent_at
            FROM notifications WHERE recipient_type=? AND recipient_name=? AND seen=0
            ORDER BY notification_id ASC""", (recipient_type, recipient_name))

    def markNotificationSeen(self, notification_id):
        return self._execute("UPDATE notifications SET seen=1, updated_at=? WHERE notification_id=?",
                             (now_ts(), notification_id))

    # ---------- פעמון התראה (סעיפים 4 + 8) ----------
    def addNotification(self, recipient_type, recipient_name, related_entity, related_id, message, user_id):
        ts = now_ts()
        # מספור התראה נפרד לכל נמען (מתחיל מ-1 לכל עובד/לקוח)
        prev = self._fetch_one(
            "SELECT COUNT(*) AS c FROM notifications WHERE recipient_type=? AND recipient_name=?",
            (recipient_type, recipient_name))
        seq = (prev['c'] if prev else 0) + 1
        self._execute("""
            INSERT INTO notifications(recipient_type,recipient_name,related_entity,related_id,message,recipient_seq,sent_by_user_id,sent_at,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (recipient_type, recipient_name, related_entity, related_id, message, seq, user_id, ts, ts, ts))
        return seq

    def getNotifications(self):
        return self._fetch_all("""
            SELECT n.*, u.full_name AS sender FROM notifications n
            JOIN users u ON n.sent_by_user_id = u.user_id
            ORDER BY n.notification_id DESC
        """)
