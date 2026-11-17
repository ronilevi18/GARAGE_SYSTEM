"""
שכבת ה-GUI (Flask) — מייצגת את ה-actor "GUI" בתרשימי ה-Sequence.
מסכים: כניסה (login) -> תפריט ראשי -> שלוש הדרישות -> יומן מערכת.
הרצה מקומית, ללא אינטרנט: python app.py  ואז פתיחת http://127.0.0.1:5000
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db.database import Database, STATION_CHAIN, STATION_HE
from controllers.auth_controller import AuthController
from controllers.work_order_controller import WorkOrderController
from controllers.task_controller import TaskController
from controllers.report_controller import ReportController, WORK_TYPE_HE
from controllers.system_log_controller import SystemLogController

app = Flask(__name__)
app.secret_key = "or-habazak-garage-local-secret"

db = Database()
db.init_db()
auth = AuthController(db)

MANAGER_ROLES = ["GarageManager", "WorkManager", "CEO"]

# שלבי הטיפול בתיק (תחנות) — לפי תרשים WorkCaseStatus
WORK_CASE_STATUSES = ["Open", "InProgress", "WaitingForParts", "WaitingForInsurance", "Completed", "Closed"]
WORK_CASE_STATUS_HE = {
    "Open": "פתוח", "InProgress": "בטיפול", "WaitingForParts": "ממתין לחלקים",
    "WaitingForInsurance": "ממתין לביטוח", "Completed": "הושלם", "Closed": "סגור",
}
TASK_STATUSES = ["NotStarted", "InProgress", "Completed", "Cancelled"]
TASK_STATUS_HE = {"NotStarted": "טרם החל", "InProgress": "בביצוע", "Completed": "הושלם", "Cancelled": "בוטל"}


# ---------- עזרי הרשאה ----------
def current_user():
    return session.get("user")


def require_login():
    return current_user() is not None


def valid_phone(phone):
    """טלפון חייב להיות בדיוק 10 ספרות."""
    p = (phone or "").strip()
    return p.isdigit() and len(p) == 10


# ---------- מסך כניסה ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = auth.login(request.form.get("username", ""), request.form.get("password", ""))
        if not user:
            flash("שם משתמש או סיסמה שגויים. נסו שוב.", "error")
            return redirect(url_for("login"))
        session["user"] = user
        if auth.checkPermissions(user, MANAGER_ROLES):
            return redirect(url_for("menu"))
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- תפריט ראשי ----------
@app.route("/menu")
def menu():
    if not require_login():
        return redirect(url_for("login"))
    user = current_user()
    # עובד רגיל: דף הבית הוא דרישה 15 בלבד
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return redirect(url_for("dashboard"))
    return render_template("menu.html", user=user)


# ===================== דרישה 3: פתיחת הזמנת עבודה =====================
@app.route("/work-order", methods=["GET"])
def work_order():
    if not require_login():
        return redirect(url_for("login"))
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        flash("⛔ אין לך הרשאה לגשת לדרישה 3 (פתיחת תיק עבודה) — היא זמינה למנהלים בלבד.", "error")
        return redirect(url_for("dashboard"))
    ctl = WorkOrderController(db)
    existing = [r for r in ctl.getCustomersAndVehicles() if r.get("vehicle_id")]
    all_active = ctl.getActiveCases()
    page = max(1, int(request.args.get("page", 1)))
    per_page = 3
    total_pages = max(1, (len(all_active) + per_page - 1) // per_page)
    page = min(page, total_pages)
    active_cases = all_active[(page - 1) * per_page: page * per_page]
    # סיכום קצר למילוי הפינה
    summary = {
        'active': len(all_active),
        'today': sum(1 for c in all_active if c['created_at'][:10] == __import__('datetime').date.today().isoformat()),
    }
    return render_template("work_order.html", user=user, existing=existing,
                           active_cases=active_cases, page=page, total_pages=total_pages, summary=summary)


@app.route("/work-order/advance", methods=["POST"])
def wo_advance():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return jsonify({"ok": False, "error": "אין הרשאה."}), 403
    f = request.form
    wid = int(f.get("work_case_id"))
    new_status = f.get("status", "").strip()
    if new_status not in WORK_CASE_STATUSES:
        return jsonify({"ok": False, "error": "סטטוס לא חוקי."}), 400
    WorkOrderController(db).advanceStatus(wid, new_status, user["user_id"])
    he = WORK_CASE_STATUS_HE.get(new_status, new_status)
    return jsonify({"ok": True, "message": f"סטטוס התיק עודכן ל'{he}'."})


@app.route("/work-order/create-entities", methods=["POST"])
def wo_create_entities():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    f = request.form
    required = ["name", "phone_number", "license_plate", "model"]
    if any(not f.get(k, "").strip() for k in required):
        return jsonify({"ok": False, "error": "שם, טלפון, מספר רישוי ודגם הם שדות חובה."}), 400
    if not valid_phone(f.get("phone_number")):
        return jsonify({"ok": False, "error": "מספר הטלפון חייב להכיל בדיוק 10 ספרות."}), 400
    ctl = WorkOrderController(db)
    try:
        cid, vid = ctl.createNewCustomerAndVehicle(
            {k: f.get(k, "").strip() for k in ["customer_type", "name", "phone_number", "id_number", "address", "notes", "birth_date", "business_id"]},
            {k: f.get(k, "").strip() for k in ["license_plate", "model", "year", "vehicle_type", "km"]},
            user["user_id"],
        )
    except Exception as e:
        msg = "מספר הרישוי כבר קיים במערכת." if "license_plate" in str(e) else "אירעה שגיאה בשמירת הנתונים. בדקו את הפרטים ונסו שוב."
        return jsonify({"ok": False, "error": msg}), 400
    return jsonify({"ok": True, "customer_id": cid, "vehicle_id": vid,
                    "message": f"נשמר בבסיס הנתונים: לקוח #{cid}, רכב #{vid}."})


@app.route("/work-order/open", methods=["POST"])
def wo_open():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    f = request.form
    accident = f.get("accident_details", "").strip()
    if not accident:
        return jsonify({"ok": False, "error": "יש למלא תיאור נזק/תאונה לפני פתיחת ההזמנה."}), 400
    ctl = WorkOrderController(db)
    existing_id = f.get("existing_customer_id", "").strip()
    existing_vehicle = f.get("existing_vehicle_id", "").strip()
    try:
        if existing_id and existing_vehicle:
            cid, vid = int(existing_id), int(existing_vehicle)
        else:
            required = ["name", "phone_number", "license_plate", "model"]
            if any(not f.get(k, "").strip() for k in required):
                return jsonify({"ok": False, "error": "בחרו רכב קיים או מלאו פרטי לקוח ורכב חדשים."}), 400
            if not valid_phone(f.get("phone_number")):
                return jsonify({"ok": False, "error": "מספר הטלפון חייב להכיל בדיוק 10 ספרות."}), 400
            cid, vid = ctl.createNewCustomerAndVehicle(
                {k: f.get(k, "").strip() for k in ["customer_type", "name", "phone_number", "id_number", "address", "notes", "birth_date", "business_id"]},
                {k: f.get(k, "").strip() for k in ["license_plate", "model", "year", "vehicle_type", "km"]},
                user["user_id"],
            )
        work_type = f.get("work_type", "BodyRepair").strip() or "BodyRepair"
        result = ctl.openNewWorkOrder(cid, vid, accident, user["user_id"], work_type)
    except Exception as e:
        msg = "מספר הרישוי כבר קיים במערכת." if "license_plate" in str(e) else "אירעה שגיאה בפתיחת ההזמנה. בדקו את הפרטים ונסו שוב."
        return jsonify({"ok": False, "error": msg}), 400
    return jsonify({"ok": True, "result": result,
                    "message": f"נפתחה הזמנת עבודה {result['case_number']} בסטטוס פתוח."})


# ===================== דרישה 15: לוח משימות לעובד =====================
@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login"))
    user = current_user()
    ctl = TaskController(db)
    is_manager = auth.checkPermissions(user, MANAGER_ROLES)
    pending = []
    if is_manager:
        tasks = ctl.getAllTasksSorted()          # מנהל רואה את כל העובדים
        employee_id = None
        employees = ctl.listEmployees()
        awaiting = db.getCasesAwaitingAssignment()   # תיקים בקבלה הממתינים לסיווג
        anomalies = db.getAnomalyReports()            # דיווחי חריגה מעובדים
    else:
        employee_id = user.get("employee_id") or 1
        tasks = ctl.getEmployeeActiveTasks(employee_id)  # עובד רואה רק פעילות שלו
        employees = []
        awaiting = []
        anomalies = []
        pending = db.getNotificationsForRecipient('Employee', user.get('full_name', ''))
    return render_template("dashboard.html", user=user, tasks=tasks,
                           employee_id=employee_id, is_manager=is_manager, employees=employees,
                           awaiting=awaiting, anomalies=anomalies, stations=STATION_CHAIN, station_he=STATION_HE,
                           pending_notifications=pending,
                           task_statuses=TASK_STATUSES, task_status_he=TASK_STATUS_HE)


@app.route("/dashboard/assign", methods=["POST"])
def assign_case():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return jsonify({"ok": False, "error": "רק מנהל יכול לסווג תיקים."}), 403
    f = request.form
    desc = f.get("task_name", "").strip()
    station = f.get("station", "").strip()
    if not desc:
        return jsonify({"ok": False, "error": "יש לכתוב תיאור משימה (מלל)."}), 400
    if station not in STATION_CHAIN:
        return jsonify({"ok": False, "error": "תחנה לא חוקית."}), 400
    tid = db.assignTaskToCase(int(f.get("work_case_id")), int(f.get("employee_id")), station,
                              desc, f.get("deadline", "").strip() or "2026-12-31",
                              int(f.get("priority", 3)), user["user_id"])
    SystemLogController(db).logChange(user["user_id"], tid, 'Assign Task', 'RepairTask')
    return jsonify({"ok": True, "message": "התיק סווג, נוצרה משימה והעובד קיבל התראה."})


@app.route("/dashboard/notify-seen", methods=["POST"])
def notify_seen():
    if not require_login():
        return jsonify({"ok": False}), 401
    db.markNotificationSeen(int(request.form.get("notification_id")))
    return jsonify({"ok": True})


@app.route("/dashboard/car-ready", methods=["POST"])
def car_ready():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return jsonify({"ok": False, "error": "אין הרשאה."}), 403
    task_id = int(request.form.get("task_id"))
    info = db.query_one("""
        SELECT c.name AS customer_name, wc.work_case_id, wc.case_number
        FROM repair_tasks rt JOIN work_cases wc ON rt.work_case_id=wc.work_case_id
        JOIN customers c ON wc.customer_id=c.customer_id WHERE rt.task_id=?""", (task_id,))
    if not info:
        return jsonify({"ok": False, "error": "תיק לא נמצא."}), 404
    db.updateWorkCaseStatus(info['work_case_id'], 'Completed', user['user_id'])
    seq = db.addNotification('Customer', info['customer_name'], 'WorkCase', info['work_case_id'],
                             f"הרכב שלך (תיק {info['case_number']}) מוכן לאיסוף!", user['user_id'])
    return jsonify({"ok": True, "message": f"🔔 נשלחה הודעה ל{info['customer_name']}: הרכב מוכן לאיסוף (#{seq})."})


@app.route("/dashboard/report-anomaly", methods=["POST"])
def report_anomaly():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    f = request.form
    task_id = int(f.get("task_id"))
    desc = f.get("description", "").strip()
    if not desc:
        return jsonify({"ok": False, "error": "יש לכתוב תיאור חריגה."}), 400
    emp_id = user.get("employee_id") or 1
    db.addAnomalyReport(task_id, emp_id, desc)
    # המנהל מקבל התראה על החריגה
    db.addNotification('Manager', 'מנהל', 'RepairTask', task_id,
                       f"דיווח חריגה ממשימה #{task_id}: {desc}", user['user_id'])
    SystemLogController(db).logChange(user['user_id'], task_id, 'Anomaly Report', 'RepairTask')
    return jsonify({"ok": True, "message": "דיווח החריגה נשלח למנהל. תודה."})


@app.route("/dashboard/advance-chain", methods=["POST"])
def task_advance_chain():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return jsonify({"ok": False, "error": "רק מנהל יכול לקדם בשרשרת."}), 403
    f = request.form
    task_id = int(f.get("task_id"))
    next_emp = int(f.get("next_employee_id"))
    res = TaskController(db).advanceChain(task_id, next_emp, user["user_id"])
    SystemLogController(db).logChange(user["user_id"], task_id, 'Advance Chain', 'RepairTask')
    return jsonify({"ok": True, "message": f"המשימה סווגה לעובד הבא, ונשלח עדכון ללקוח {res['customer_name']}."})


@app.route("/dashboard/update-status", methods=["POST"])
def task_update_status():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    f = request.form
    task_id = int(f.get("task_id"))
    new_status = f.get("status", "").strip()
    if new_status not in TASK_STATUSES:
        return jsonify({"ok": False, "error": "סטטוס לא חוקי."}), 400
    TaskController(db).updateTaskStatus(task_id, new_status)
    SystemLogController(db).logChange(current_user()["user_id"], task_id, f'Task -> {new_status}', 'RepairTask')
    return jsonify({"ok": True, "message": f"סטטוס המשימה עודכן ל'{TASK_STATUS_HE.get(new_status)}'."})


@app.route("/dashboard/notify", methods=["POST"])
def task_notify():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        return jsonify({"ok": False, "error": "רק מנהל יכול לשלוח התראה."}), 403
    f = request.form
    task_id = int(f.get("task_id"))
    emp = f.get("employee_name", "עובד")
    nid = TaskController(db).notifyEmployee(emp, task_id, f"תזכורת לקדם את משימה #{task_id}", user["user_id"])
    return jsonify({"ok": True, "message": f"🔔 נשלחה התראה ל{emp} (התראה #{nid})."})


# ===================== דרישה 20: דוח זמן טיפול =====================
@app.route("/report", methods=["GET"])
def report():
    if not require_login():
        return redirect(url_for("login"))
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        flash("⛔ אין לך הרשאה לגשת לדרישה 20 (דוח זמן טיפול) — היא זמינה למנהלים בלבד.", "error")
        return redirect(url_for("dashboard"))
    return render_template("report.html", user=user, metrics=None)


@app.route("/report/generate", methods=["POST"])
def report_generate():
    if not require_login():
        return jsonify({"ok": False, "error": "נדרשת התחברות"}), 401
    user = current_user()
    f = request.form
    filters = {
        "date_from": f.get("date_from", "").strip(),
        "date_to": f.get("date_to", "").strip(),
        "work_type": f.get("work_type", "All"),
    }
    ctl = ReportController(db)
    open_cases = ctl.queryOpenWorkOrders(filters)
    metrics = ctl.calculateReportMetrics(open_cases)
    rid = ctl.saveGeneratedReport(metrics, filters, user["user_id"])
    metrics["report_id"] = rid
    session["last_filters"] = filters   # רק הפילטרים (קטן) — לצורך ייצוא
    return jsonify({"ok": True, "metrics": metrics,
                    "message": f"דוח #{rid} נשמר בבסיס הנתונים בשעה {metrics['generated_at']}."})


@app.route("/report/export")
def report_export():
    if not require_login():
        return redirect(url_for("login"))
    user = current_user()
    if not auth.checkPermissions(user, MANAGER_ROLES):
        flash("אין הרשאה.", "error")
        return redirect(url_for("menu"))
    filters = session.get("last_filters")
    if filters is None:
        flash("יש להפיק דוח לפני הייצוא.", "error")
        return redirect(url_for("report"))
    ctl = ReportController(db)
    metrics = ctl.calculateReportMetrics(ctl.queryOpenWorkOrders(filters))
    import tempfile, os
    from flask import send_file
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    ctl.exportToCsv(metrics, path)
    return send_file(path, as_attachment=True, download_name="treatment_report.csv",
                     mimetype="text/csv")


# ---------- יומן מערכת ----------
@app.route("/system-log")
def system_log():
    if not require_login():
        return redirect(url_for("login"))
    if not auth.checkPermissions(current_user(), MANAGER_ROLES):
        flash("אין הרשאה — יומן המערכת זמין למנהלים בלבד.", "error")
        return redirect(url_for("dashboard"))
    rows = SystemLogController(db).getHistory()
    return render_template("system_log.html", user=current_user(), rows=rows)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
