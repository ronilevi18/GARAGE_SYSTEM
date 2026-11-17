# מיפוי תרשים Sequence ↔ קוד (לסעיף 8.1 — מיפוי מלא בהצגה)

הטבלה מראה, לכל הודעה בתרשים ה-Sequence, את המחלקה והשיטה בקוד שבהן היא מתבצעת.
ה-actor "GUI" מיוצג על ידי app.py (Flask). שמות השיטות בקוד זהים לשמות בתרשים.

## דרישה 3 — פתיחת הזמנת עבודה (Open New Work Order)

| # | הודעה בתרשים | אובייקט בתרשים | מיקום בקוד |
|---|---|---|---|
| 1 | Request to open new work order | Garage Manager → GUI | `app.py` → `work_order()` |
| 2 | `getCustomersAndVehicles()` | GUI → WorkOrderController | `work_order_controller.py` → `getCustomersAndVehicles()` |
| 3 | Query all existing customers and vehicles | Controller → Database | `database.py` → `queryExistingCustomersAndVehicles()` |
| 4 | Display selection lists / Update selection display | GUI | `work_order.html` (select #existing) |
| 5 | `createNewCustomerAndVehicle(customerDetails, vehicleDetails)` | GUI → Controller | `work_order_controller.py` → `createNewCustomerAndVehicle()` |
| 6 | `«create» newCustomer` , `«create» newVehicle` | Controller → אובייקטים | בתוך `createNewCustomerAndVehicle()` (יצירת `Customer`, `Vehicle`) |
| 7 | Save new customer and vehicle entities | Controller → Database | `database.py` → `saveNewEntities()` |
| 8 | `openNewWorkOrder(customerId, vehicleId, accidentDetails)` | GUI → Controller | `work_order_controller.py` → `openNewWorkOrder()` |
| 9 | System creates case number, current date, status='Open' | Controller (הערה בתרשים) | בתוך `openNewWorkOrder()` |
| 10 | `saveWorkOrder(workOrderDetails)` | Controller → Controller/Database | `work_order_controller.py` → `saveWorkOrder()` → `database.py::saveWorkCase()` |
| 11 | Display success message and unique case number | Controller → GUI | החזרת dict ל-`wo_open()` והצגה ב-`work_order.html` |

## דרישה 15 — לוח משימות אישי (Employee Task Dashboard)

| # | הודעה בתרשים | אובייקט בתרשים | מיקום בקוד |
|---|---|---|---|
| 1 | Open personal dashboard | Employee → GUI | `app.py` → `dashboard()` |
| 2 | `getEmployeeTasks(employeeId)` | GUI → TaskController | `task_controller.py` → `getEmployeeTasks()` |
| 3 | `queryAssignedTasks(employeeId)` | Controller → Database | `task_controller.py::queryAssignedTasks()` → `database.py::fetchRawTasksByEmployee()` |
| 4 | Return rawTaskList | Database → Controller | ערך חוזר מ-`fetchRawTasksByEmployee()` |
| 5 | `«create» taskSorter` | Controller → TaskSorter | בתוך `getEmployeeTasks()`: `taskSorter = TaskSorter()` |
| 6 | `sortTasksByUrgency(rawTaskList)` | Controller → taskSorter | `entities.py::TaskSorter.sortTasksByUrgency()` |
| 7 | `sendSortedTasks(sortedTaskList)` | Controller → GUI | `task_controller.py::sendSortedTasks()` |
| 8 | loop: `displayTaskDetails(task)` | GUI | לולאת `{% for t in tasks %}` ב-`dashboard.html` |
| 9 | `«destroy» taskSorter` | Controller | בתוך `getEmployeeTasks()`: `del taskSorter` |

## דרישה 20 — דוח זמן טיפול (Complex Treatment Time Report)

| # | הודעה בתרשים | אובייקט בתרשים | מיקום בקוד |
|---|---|---|---|
| 1 | Open reports screen / Submit report request | Garage Manager → GUI | `app.py` → `report()` / `report_generate()` |
| 2 | `queryOpenWorkOrders(filters)` | GUI → ReportController | `report_controller.py::queryOpenWorkOrders()` → `database.py::getOpenWorkOrders()` |
| 3 | Return openWorkOrdersList | Database → Controller | ערך חוזר מ-`getOpenWorkOrders()` |
| 4 | loop: `queryStatusHistory(workOrderId)` | Controller → Database | `report_controller.py::queryStatusHistory()` → `database.py::getStatusHistoryById()` |
| 5 | `calculateReportMetrics(openWorkOrdersList)` | Controller | `report_controller.py::calculateReportMetrics()` |
| 6 | `saveGeneratedReport(reportMetrics)` | Controller → Database | `report_controller.py::saveGeneratedReport()` → `database.py::saveReportMetrics()` |
| 7 | `sendReportData(reportMetrics)` / Display report | Controller → GUI | JSON חוזר ל-`report.html` והצגה בטבלה |

## הערות על התאמה לתרשימי המחלקות (ללא שינוי התרשימים)

- כל המחלקות מתרשימי המחלקות מוגדרות ב-`models/entities.py`.
- המחלקות שמשתתפות בשלוש הדרישות (Customer, Vehicle, WorkCase, RepairTask, TaskSorter,
  User, Employee, SystemLog) ממומשות ונמצאות בשימוש בפועל.
- מחלקות מודול 3 (Part, PaintFormula, Supplier, ServiceCatalog, PartOrder, PartOrderLine)
  ומחלקות boundary (InsuranceAPI, NotificationAPI, SupplierAPI) קיימות בתרשים אך אינן חלק
  משלוש הדרישות שמומשו — הן מוגדרות לשם שלמות אך אינן מופעלות בזרימות אלה.
- שיטות ה-Database בקוד נושאות בדיוק את השמות מתיבת Database בכל מודול בתרשים.

---

## עדכון: שינויים שבוצעו בחלק ג' (לסימון בתרשימים)

לפי בקשת הלקוח נוספו יכולות מעבר למה שהופיע בתרשימי חלק ב'. **יש לעדכן את התרשימים ולסמן בצבע** את התוספות הבאות:

**דרישה 3 (WorkOrderController):**
- `advanceStatus(workCaseId, newStatus)` — קידום תיק בין תחנות הטיפול ועד סגירה.
- `getActiveCases()` — שליפת תיקים פעילים (שאינם סגורים).
- ב-Database: `updateWorkCaseStatus()`, `getActiveWorkCases()`.

**דרישה 15 (TaskController):**
- `updateTaskStatus(taskId, newStatus)` — עדכון סטטוס משימה מרשימה נפתחת.
- `getAllTasksSorted()` — תצוגת מנהל לכל משימות העובדים.
- `notifyEmployee(...)` — פעמון התראה לעובד.
- ב-Database: `updateRepairTaskStatus()`, `fetchAllTasks()`, `addNotification()`.

**דרישה 20 (ReportController):**
- הרחבת `calculateReportMetrics()` לכלול התפלגות לפי סוג עבודה (pie) וזמן בכל תחנה.
- `notifyCustomer(...)` — פעמון התראה ללקוח.
- ב-Database: `getStationTimesByCase()`, `addNotification()`.

**ישות חדשה:** `Notification` (notification_id, recipientType, recipientName, relatedEntity, relatedId, message, sentAt) — יש להוסיף לתרשים המחלקות ולסמן בצבע.

---

## עדכון נוסף (גרסה 5) — לסימון בתרשימים

**ישויות/טבלאות חדשות לתרשים המחלקות:**
- `StationVisit` (visitId, station, enteredAt, leftAt) — מעקב שרשרת התחנות (דרישה 20).
- `AnomalyReport` (reportId, taskId, employeeId, description) — דיווח חריגה מעובד (דרישה 15).
- הרחבת `Notification` עם recipientSeq (מספור נפרד לנמען) ו-seen (נצפה/לא).

**שרשרת התחנות (דרישה 20):** קבלה → פחחות → צבע → המתנה לחלקים → המתנה לשמאי → בדיקת איכות.
מחושב זמן שהייה בכל תחנה (getStationTimesByCase) ובתחנה הנוכחית (getCurrentStationHours).

**דרישה 15 (מנהל):** הוסר עדכון סטטוס ע"י המנהל. במקומו: שחרור משימה שהושלמה לעובד הבא (advanceChain),
או הודעת "הרכב מוכן" ללקוח (car-ready). פעמון התראה לעובד עם חלון קופץ אצל העובד (getNotificationsForRecipient/markNotificationSeen).

**דרישה 15 (עובד):** דיווח חריגה (addAnomalyReport) ששולח התראה למנהל. חסימת גישה לדרישות 3/20 (managers only).

**דרישה 20:** ייצוא Excel (exportToExcel), סינון לפי צוואר בקבוק, ושתי עמודות נפרדות —
"שעות שהתיק פתוח" מול "שעות הרכב בתחנה הנוכחית".
