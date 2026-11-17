-- =========================================================================
-- שאילתות SELECT להצגה בכיתה (סעיף 8) — הוכחת עדכון בזמן אמת עם חותמת זמן
-- אפשר להריץ ב-DB Browser for SQLite, או דרך sqlite3 garage.db
-- =========================================================================

-- דרישה 3: הצגת הזמנת העבודה החדשה שנשמרה, עם חותמת זמן מדויקת
SELECT wc.work_case_id, wc.case_number, c.name AS customer, v.license_plate,
       wc.work_type, wc.status, wc.created_at, wc.updated_at
FROM work_cases wc
JOIN customers c ON wc.customer_id = c.customer_id
JOIN vehicles  v ON wc.vehicle_id  = v.vehicle_id
ORDER BY wc.work_case_id DESC;

-- דרישה 3 (המשך): היסטוריית הסטטוס שנוצרה עם פתיחת ההזמנה
SELECT * FROM status_history ORDER BY status_history_id DESC;

-- דרישה 15: המשימות של עובד מסוים, כולל created_at / updated_at
-- (להחליף 1 במזהה העובד הרצוי)
SELECT rt.task_id, wc.case_number, v.license_plate AS vehicle_number,
       rt.task_name, rt.deadline, rt.status, rt.priority_level, rt.workload,
       rt.created_at, rt.updated_at
FROM repair_tasks rt
JOIN work_cases wc ON rt.work_case_id = wc.work_case_id
JOIN vehicles   v ON wc.vehicle_id    = v.vehicle_id
WHERE rt.employee_id = 1
ORDER BY rt.deadline ASC;

-- דרישה 20: הדוח שנשמר בטבלת generated_reports, עם חותמת זמן
SELECT report_id, report_name, generated_by_user_id, created_at, updated_at,
       filters_json, metrics_json
FROM generated_reports
ORDER BY report_id DESC;

-- יומן המערכת: כל הפעולות שתועדו, לפי חותמת זמן
SELECT sl.change_id, sl.action_type, u.full_name AS user_name,
       sl.entity_name, sl.entity_id, sl.timestamp
FROM system_log sl
JOIN users u ON sl.user_id = u.user_id
ORDER BY sl.timestamp DESC, sl.change_id DESC;
