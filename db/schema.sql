PRAGMA foreign_keys = ON;

-- ===== Module 1: Core CRM & Assets =====

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('CEO','GarageManager','WorkManager','BodyWorker','Painter','Driver','Employee')),
    employee_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone_number TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_type TEXT NOT NULL CHECK(customer_type IN ('Private','Business')),
    name TEXT NOT NULL,
    id_number TEXT,
    phone_number TEXT NOT NULL,
    address TEXT,
    notes TEXT,
    birth_date TEXT,
    business_id TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive','InMaintenance')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    license_plate TEXT NOT NULL UNIQUE,
    model TEXT NOT NULL,
    year INTEGER,
    vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('Private','Business','Electric','Luxury')),
    km INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive','InMaintenance')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS service_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    cost REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- ===== Module 2: Operations & Workflow =====

CREATE TABLE IF NOT EXISTS work_cases (
    work_case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    accident_details TEXT NOT NULL,
    work_type TEXT NOT NULL DEFAULT 'BodyRepair' CHECK(work_type IN ('BodyRepair','PaintServices','ThirdPartyAccident')),
    status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','InProgress','WaitingForParts','WaitingForInsurance','Completed','Closed','Cancelled')),
    opened_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY(opened_by_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS repair_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_case_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NotStarted' CHECK(status IN ('NotStarted','InProgress','Completed','Cancelled')),
    priority_level INTEGER NOT NULL DEFAULT 3 CHECK(priority_level BETWEEN 1 AND 5),
    workload INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(work_case_id) REFERENCES work_cases(work_case_id),
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS damage_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_case_id INTEGER NOT NULL,
    estimated_cost REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(work_case_id) REFERENCES work_cases(work_case_id)
);

CREATE TABLE IF NOT EXISTS quality_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    is_approved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES repair_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES repair_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS status_history (
    status_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_case_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    changed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(work_case_id) REFERENCES work_cases(work_case_id),
    FOREIGN KEY(changed_by_user_id) REFERENCES users(user_id)
);

-- ===== Module 3: Inventory & Logistics + Reports =====

CREATE TABLE IF NOT EXISTS service_catalog (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    base_price REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity_in_stock INTEGER NOT NULL DEFAULT 0,
    min_quantity INTEGER NOT NULL DEFAULT 0,
    price REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paint_formulas (
    formula_id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    color_code TEXT NOT NULL,
    mix_ratio TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(part_id) REFERENCES parts(part_id)
);

CREATE TABLE IF NOT EXISTS part_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Created' CHECK(status IN ('Created','SentToSupplier','Received','Cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE IF NOT EXISTS part_order_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(order_id) REFERENCES part_orders(order_id),
    FOREIGN KEY(part_id) REFERENCES parts(part_id)
);

CREATE TABLE IF NOT EXISTS generated_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT NOT NULL,
    filters_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    generated_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(generated_by_user_id) REFERENCES users(user_id)
);

-- SystemLog (Module 1)
CREATE TABLE IF NOT EXISTS system_log (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    entity_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Notifications (פעמון התראה — לעובד / ללקוח, מאפשר קידום שלב)
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_type TEXT NOT NULL,        -- 'Employee' / 'Customer'
    recipient_name TEXT NOT NULL,
    related_entity TEXT NOT NULL,        -- 'RepairTask' / 'WorkCase'
    related_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    recipient_seq INTEGER NOT NULL DEFAULT 1,
    seen INTEGER NOT NULL DEFAULT 0,
    sent_by_user_id INTEGER NOT NULL,
    sent_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(sent_by_user_id) REFERENCES users(user_id)
);

-- מעקב תחנות (שרשרת הטיפול הפיזית במוסך) — דרישה 20
CREATE TABLE IF NOT EXISTS station_visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_case_id INTEGER NOT NULL,
    station TEXT NOT NULL,            -- Reception/BodyWork/Paint/WaitingParts/WaitingAssessor/QualityCheck
    entered_at TEXT NOT NULL,
    left_at TEXT,                     -- NULL = עדיין בתחנה זו
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(work_case_id) REFERENCES work_cases(work_case_id)
);

-- דיווחי חריגה מעובדים — דרישה 15 (מסך עובד)
CREATE TABLE IF NOT EXISTS anomaly_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES repair_tasks(task_id),
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
);
