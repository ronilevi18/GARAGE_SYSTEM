"""
נתונים ראשוניים (סעיף 6 + 8): נטענים ידנית לפני הדלקת המערכת.
כולל: משתמשים והרשאות (למסך הכניסה), עובדים, לקוחות, רכבים, תיקי עבודה ומשימות לדוגמה.
הרצה: python seed_data.py
"""
from db.database import Database, now_ts
from datetime import datetime, timedelta

DB = Database()
DB.init_db()


def seed():
    with DB.connect() as conn:
        ts = now_ts()
        # ניקוי טבלאות (סדר הפוך למפתחות זרים)
        for t in ['notifications', 'anomaly_reports', 'station_visits', 'system_log', 'generated_reports',
                  'part_order_lines', 'part_orders',
                  'paint_formulas', 'parts', 'suppliers', 'service_catalog',
                  'status_history', 'anomalies', 'quality_checks', 'damage_assessments',
                  'repair_tasks', 'work_cases', 'service_records', 'vehicles',
                  'customers', 'users', 'employees']:
            conn.execute(f"DELETE FROM {t}")

        # עובדים
        employees = [
            ('עמית כהן', 'Painter', '0501111111'),
            ('דוד לוי', 'BodyWorker', '0502222222'),
            ('ניר בר', 'WorkManager', '0503333333'),
            ('יוסי אברהם', 'Driver', '0504444444'),
        ]
        for e in employees:
            conn.execute("INSERT INTO employees(full_name,role,phone_number,created_at,updated_at) VALUES(?,?,?,?,?)", (*e, ts, ts))

        # משתמשים והרשאות (למסך הכניסה) — אחד מכל תפקיד
        users = [
            ('manager', '1234', 'ענבר', 'GarageManager', None),
            ('ceo', '1234', 'רוני', 'CEO', None),
            ('workmgr', '1234', 'ניר בר', 'WorkManager', 3),
            ('painter', '1234', 'עמית כהן', 'Painter', 1),
            ('body', '1234', 'דוד לוי', 'BodyWorker', 2),
            ('driver', '1234', 'יוסי אברהם', 'Driver', 4),
        ]
        for u in users:
            conn.execute("INSERT INTO users(username,password,full_name,role,employee_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (*u, ts, ts))

        # לקוחות
        customers = [
            ('Private', 'ירדן מזרחי', '301111111', '052-1234567', 'פתח תקווה', 'לקוח יוקרה', '1990-05-10', ''),
            ('Business', 'מטרולינק בע"מ', '', '03-7777777', 'רעננה', 'לקוח צי רכבים', '', '515555555'),
        ]
        for c in customers:
            conn.execute("""INSERT INTO customers(customer_type,name,id_number,phone_number,address,notes,birth_date,business_id,status,created_at,updated_at)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (*c, 'Active', ts, ts))

        # רכבים
        vehicles = [
            (1, '111-22-333', 'Tesla Model 3', 2023, 'Electric', 18000),
            (2, '444-55-666', 'Mercedes C300', 2022, 'Luxury', 24000),
        ]
        for v in vehicles:
            conn.execute("""INSERT INTO vehicles(customer_id,license_plate,model,year,vehicle_type,km,status,created_at,updated_at)
                            VALUES(?,?,?,?,?,?,?,?,?)""", (*v, 'Active', ts, ts))

        # תיקי עבודה — מגוון סוגים (לגרף עוגה) + היסטוריית סטטוס מרובת תחנות (לזמני תחנה)
        from datetime import datetime, timedelta
        def ts_ago(hours): return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        old_ts = ts_ago(96)
        cases = [
            ('OHB-SEED-001', 1, 1, 'נזק בפגוש קדמי לאחר תאונת חניה', 'ThirdPartyAccident', 'Open', 1, old_ts, old_ts),
            ('OHB-SEED-002', 2, 2, 'שריטות צבע בדלת שמאל', 'PaintServices', 'Open', 1, ts_ago(30), ts_ago(30)),
            ('OHB-SEED-003', 1, 1, 'החלפת כנף ופחחות', 'BodyRepair', 'Open', 1, ts_ago(50), ts_ago(50)),
        ]
        histories = {
            'OHB-SEED-001': [('Open', 96), ('InProgress', 70), ('WaitingForParts', 40)],
            'OHB-SEED-002': [('Open', 30), ('InProgress', 12)],
            'OHB-SEED-003': [('Open', 50), ('InProgress', 36), ('WaitingForInsurance', 20)],
        }
        # ביקורי תחנות (שרשרת פיזית) — entered/left; התחנה האחרונה פתוחה (left=NULL)
        # פורמט: (station, hours_ago_entered, hours_ago_left or None)
        station_visits = {
            'OHB-SEED-001': [('Reception', 96, 90), ('BodyWork', 90, 70), ('WaitingParts', 70, None)],
            'OHB-SEED-002': [('Reception', 30, 28), ('Paint', 28, None)],
            'OHB-SEED-003': [('Reception', 50, 47), ('BodyWork', 47, 30), ('WaitingAssessor', 30, None)],
        }
        for c in cases:
            cur = conn.execute("""INSERT INTO work_cases(case_number,customer_id,vehicle_id,accident_details,work_type,status,opened_by_user_id,created_at,updated_at)
                                  VALUES(?,?,?,?,?,?,?,?,?)""", c)
            wid = cur.lastrowid
            prev = None
            for status, hrs in histories[c[0]]:
                t = ts_ago(hrs)
                conn.execute("""INSERT INTO status_history(work_case_id,old_status,new_status,changed_by_user_id,changed_at,created_at,updated_at)
                                VALUES(?,?,?,?,?,?,?)""", (wid, prev, status, 1, t, t, t))
                prev = status
            for station, ent, lft in station_visits[c[0]]:
                conn.execute("""INSERT INTO station_visits(work_case_id,station,entered_at,left_at,created_at,updated_at)
                                VALUES(?,?,?,?,?,?)""",
                             (wid, station, ts_ago(ent), ts_ago(lft) if lft else None, ts_ago(ent), ts_ago(ent)))

        # תיק טרי שממתין לסיווג ע"י המנהל (בקבלה, ללא משימה)
        wid_new = conn.execute("""INSERT INTO work_cases(case_number,customer_id,vehicle_id,accident_details,work_type,status,opened_by_user_id,created_at,updated_at)
                                  VALUES(?,?,?,?,?,?,?,?,?)""",
                               ('OHB-SEED-004', 2, 2, 'מכה בדלת אחורית ימין, ממתין לבדיקת מנהל', 'BodyRepair', 'Open', 1, ts_ago(2), ts_ago(2))).lastrowid
        conn.execute("""INSERT INTO status_history(work_case_id,old_status,new_status,changed_by_user_id,changed_at,created_at,updated_at)
                        VALUES(?,?,?,?,?,?,?)""", (wid_new, None, 'Open', 1, ts_ago(2), ts_ago(2), ts_ago(2)))
        conn.execute("""INSERT INTO station_visits(work_case_id,station,entered_at,left_at,created_at,updated_at)
                        VALUES(?,?,?,?,?,?)""", (wid_new, 'Reception', ts_ago(2), None, ts_ago(2), ts_ago(2)))

        # משימות תיקון (לעובד 1 שתי משימות בדדליינים שונים, להדגמת מיון לפי דחיפות)
        d = lambda days: (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        tasks = [
            (1, 1, 'הכנת צבע והתאמת קוד גוון', d(1), 'NotStarted', 1, 3),
            (1, 2, 'יישור פגוש קדמי', d(2), 'InProgress', 2, 4),
            (2, 1, 'צביעת דלת שמאל ותיעוד גימור', d(3), 'NotStarted', 3, 2),
        ]
        for t in tasks:
            conn.execute("""INSERT INTO repair_tasks(work_case_id,employee_id,task_name,deadline,status,priority_level,workload,created_at,updated_at)
                            VALUES(?,?,?,?,?,?,?,?,?)""", (*t, ts, ts))

        # דיווח חריגה לדוגמה (להדגמת פאנל החריגות אצל המנהל)
        conn.execute("""INSERT INTO anomaly_reports(task_id,employee_id,description,created_at,updated_at)
                        VALUES(?,?,?,?,?)""",
                     (2, 2, 'התגלה נזק נוסף בכנף שלא תועד בקבלה — נדרש אישור להזמנת חלק.', ts_ago(5), ts_ago(5)))

        conn.commit()
    print('garage.db נוצר ואותחל בהצלחה עם נתונים ראשוניים.')


if __name__ == '__main__':
    seed()
