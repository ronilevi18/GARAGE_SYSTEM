"""
בקר הזמנות עבודה — דרישה 3: פתיחת הזמנת עבודה חדשה.
מתאים למחלקת WorkOrderController בתרשים המחלקות, ולתרשים ה-Sequence:
  GUI -> getCustomersAndVehicles()  -> Database.queryExistingCustomersAndVehicles()
  GUI -> createNewCustomerAndVehicle(customerDetails, vehicleDetails)
              -> «create» newCustomer, «create» newVehicle -> Database.saveNewEntities()
  GUI -> openNewWorkOrder(customerId, vehicleId, accidentDetails)
              -> יצירת מספר תיק ייחודי, תאריך נוכחי, סטטוס 'Open'
              -> saveWorkOrder(workOrderDetails) -> Database.saveWorkCase()
"""
from db.database import Database, now_ts
from controllers.system_log_controller import SystemLogController
from models.entities import Customer, Vehicle, WorkCase


class WorkOrderController:
    def __init__(self, db: Database):
        self.db = db
        self.log = SystemLogController(db)

    # --- הודעה 1 בתרשים: getCustomersAndVehicles() ---
    def getCustomersAndVehicles(self):
        return self.db.queryExistingCustomersAndVehicles()

    # --- הודעה 2 בתרשים: createNewCustomerAndVehicle(customerDetails, vehicleDetails) ---
    def createNewCustomerAndVehicle(self, customerDetails: dict, vehicleDetails: dict, user_id: int):
        # «create» newCustomer  /  «create» newVehicle  (כפי שמופיע בתרשים ה-Sequence)
        newCustomer = Customer(name=customerDetails.get('name', ''),
                               number=customerDetails.get('phone_number', ''))
        newVehicle = Vehicle(licensePlate=vehicleDetails.get('license_plate', ''),
                             model=vehicleDetails.get('model', ''))
        # Save new customer and vehicle entities
        customer_id, vehicle_id = self.db.saveNewEntities(customerDetails, vehicleDetails)
        newCustomer.id = customer_id
        newVehicle.vehicleId = vehicle_id
        self.log.logChange(user_id, customer_id, 'Create Customer', 'Customer')
        self.log.logChange(user_id, vehicle_id, 'Create Vehicle', 'Vehicle')
        return customer_id, vehicle_id

    # --- הודעה 3 בתרשים: openNewWorkOrder(customerId, vehicleId, accidentDetails) ---
    def openNewWorkOrder(self, customerId: int, vehicleId: int, accidentDetails: str,
                         user_id: int, work_type: str = 'BodyRepair'):
        ts = now_ts()
        # מספר תיק ייחודי קצר: OHB-<MMDD>-<HHMM>-<vehicleId>
        compact = ts[5:7] + ts[8:10] + "-" + ts[11:13] + ts[14:16]
        case_number = f"OHB-{compact}-{vehicleId}"
        workCase = WorkCase(status='Open')
        work_case_id = self.saveWorkOrder({
            'case_number': case_number,
            'customer_id': customerId,
            'vehicle_id': vehicleId,
            'accident_details': accidentDetails,
            'work_type': work_type,
            'status': 'Open',
            'opened_by_user_id': user_id,
            'created_at': ts,
            'updated_at': ts,
        })
        workCase.workCaseId = work_case_id
        self.db.insertStatusHistory(work_case_id, None, 'Open', user_id)
        # התיק נכנס לתחנת "קבלה" וממתין לסיווג ע"י המנהל (לא נוצרת משימה אוטומטית)
        self.db.moveToStation(work_case_id, 'Reception')
        self.log.logChange(user_id, work_case_id, 'Open New Work Order', 'WorkCase')
        return {'work_case_id': work_case_id, 'case_number': case_number, 'status': 'Open'}

    # --- הודעה 4 בתרשים: saveWorkOrder(workOrderDetails) ---
    def saveWorkOrder(self, workOrderDetails: dict) -> int:
        return self.db.saveWorkCase(workOrderDetails)

    # --- קידום סטטוס תיק (מעקב התקדמות בתחנות וסגירה) ---
    def advanceStatus(self, work_case_id: int, new_status: str, user_id: int):
        self.db.updateWorkCaseStatus(work_case_id, new_status, user_id)
        self.log.logChange(user_id, work_case_id, f'Status -> {new_status}', 'WorkCase')
        return True

    def getActiveCases(self):
        return self.db.getActiveWorkCases()
