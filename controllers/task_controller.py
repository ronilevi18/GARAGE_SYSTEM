"""
בקר משימות — דרישה 15: לוח משימות אישי לעובד.
מתאים למחלקת TaskController בתרשים, ולתרשים ה-Sequence:
  GUI -> getEmployeeTasks(employeeId)
  Controller -> queryAssignedTasks(employeeId) -> Database.fetchRawTasksByEmployee(employeeId) -> rawTaskList
  Controller -> «create» taskSorter
  Controller -> taskSorter.sortTasksByUrgency(rawTaskList) -> sortedTaskList
  Controller -> sendSortedTasks(sortedTaskList)
  GUI -> loop: displayTaskDetails(task)
  Controller -> «destroy» taskSorter

הערה: לפי תרשים ה-Sequence דרישה 15 היא דרישת תצוגה (קריאה בלבד) ואינה משנה נתונים.
"""
from db.database import Database, now_ts
from models.entities import TaskSorter


class TaskController:
    def __init__(self, db: Database):
        self.db = db

    # --- getEmployeeTasks(employeeId) ---
    def getEmployeeTasks(self, employeeId: int):
        rawTaskList = self.queryAssignedTasks(employeeId)   # queryAssignedTasks
        taskSorter = TaskSorter()                           # «create» taskSorter
        sortedTaskList = taskSorter.sortTasksByUrgency(rawTaskList)  # sortTasksByUrgency
        result = self.sendSortedTasks(sortedTaskList)       # sendSortedTasks
        del taskSorter                                      # «destroy» taskSorter
        return result

    def getEmployeeActiveTasks(self, employeeId: int):
        """תצוגת עובד: רק משימות פעילות (ללא שהושלמו/בוטלו)."""
        return [t for t in self.getEmployeeTasks(employeeId)
                if t['status'] not in ('Completed', 'Cancelled')]

    # --- queryAssignedTasks(employeeId) ---
    def queryAssignedTasks(self, employeeId: int):
        return self.db.fetchRawTasksByEmployee(employeeId)

    # --- sortTasksByUrgency(rawTaskList) ---
    # (ממומש במחלקה TaskSorter בתרשים — נקרא דרך האובייקט taskSorter למעלה)

    # --- sendSortedTasks(sortedTaskList) ---
    def sendSortedTasks(self, sortedTaskList: list):
        return sortedTaskList

    # --- תצוגת מנהל: כל המשימות של כל העובדים, ממוינות לפי דחיפות ---
    def getAllTasksSorted(self):
        from models.entities import TaskSorter
        raw = self.db.fetchAllTasks()
        sorter = TaskSorter()
        sorted_list = sorter.sortTasksByUrgency(raw)
        del sorter
        return sorted_list

    # --- קידום סטטוס משימה (סעיף 3+4: רשימה נפתחת לעדכון) ---
    def updateTaskStatus(self, task_id: int, new_status: str):
        return self.db.updateRepairTaskStatus(task_id, new_status)

    # --- פעמון התראה (סעיף 4): המנהל שולח תזכורת לעובד לקדם שלב ---
    def notifyEmployee(self, employee_name: str, task_id: int, message: str, user_id: int):
        return self.db.addNotification('Employee', employee_name, 'RepairTask', task_id, message, user_id)

    # --- קידום בשרשרת ע"י המנהל: סיווג לעובד הבא + הודעה ללקוח (דרישה 15) ---
    def advanceChain(self, task_id: int, next_employee_id: int, user_id: int):
        # סיווג המשימה לעובד הבא והחזרתה למצב פעיל
        ts = now_ts()
        self.db.run("UPDATE repair_tasks SET employee_id=?, status='NotStarted', updated_at=? WHERE task_id=?",
                    (next_employee_id, ts, task_id))
        # שליפת פרטי הלקוח כדי לעדכן אותו
        info = self.db.query_one("""
            SELECT c.name AS customer_name, wc.work_case_id, wc.case_number
            FROM repair_tasks rt
            JOIN work_cases wc ON rt.work_case_id = wc.work_case_id
            JOIN customers c ON wc.customer_id = c.customer_id
            WHERE rt.task_id = ?""", (task_id,))
        seq = None
        if info:
            seq = self.db.addNotification('Customer', info['customer_name'], 'WorkCase',
                                          info['work_case_id'],
                                          f"הטיפול ברכבך (תיק {info['case_number']}) התקדם לשלב הבא.", user_id)
        return {'customer_name': info['customer_name'] if info else '', 'seq': seq}

    def listEmployees(self):
        return self.db.query("SELECT employee_id, full_name, role FROM employees ORDER BY full_name")
