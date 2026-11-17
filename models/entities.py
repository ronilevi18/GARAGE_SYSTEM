"""
מחלקות הישויות (Entities) — תואמות אחד-לאחד לתרשימי המחלקות (חלק ב').
המחלקות שמשתתפות בשלוש הדרישות (Customer, Vehicle, WorkCase, RepairTask,
TaskSorter, User, Employee, SystemLog) ממומשות ומשמשות בפועל בקוד הקונטרולרים.
שאר המחלקות (Module 3 / boundary) מוגדרות כדי לשמור על התאמה מלאה לתרשים המחלקות,
ואינן נדרשות לשלוש הדרישות המוצגות.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ===== Module 1: Core CRM & Assets =====

@dataclass
class Customer:
    id: Optional[int] = None
    name: str = ""
    number: str = ""            # phone number
    status: str = "Active"

    def view(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "number": self.number, "status": self.status}


@dataclass
class PrivateCustomer(Customer):
    address: str = ""
    notes: str = ""
    birthDate: str = ""


@dataclass
class BusinessCustomer(Customer):
    businessId: str = ""
    address: str = ""
    notes: str = ""


@dataclass
class Vehicle:
    vehicleId: Optional[int] = None
    licensePlate: str = ""
    model: str = ""
    year: Optional[int] = None
    type: str = "Private"
    status: str = "Active"

    def viewDetails(self) -> Dict[str, Any]:
        return {"vehicleId": self.vehicleId, "licensePlate": self.licensePlate,
                "model": self.model, "year": self.year, "type": self.type}


@dataclass
class User:
    userId: Optional[int] = None
    role: str = "Employee"

    def checkPermissions(self, allowed_roles: List[str]) -> bool:
        return self.role in allowed_roles


@dataclass
class Employee(User):
    employeeId: Optional[int] = None
    phoneNumber: str = ""


@dataclass
class ServiceRecord:
    recordId: Optional[int] = None
    serviceDate: str = ""
    cost: float = 0.0


@dataclass
class SystemLog:
    changeId: Optional[int] = None
    timestamp: str = ""
    entityId: Optional[int] = None
    actionType: str = ""


# ===== Module 2: Operations & Workflow =====

@dataclass
class WorkCase:
    workCaseId: Optional[int] = None
    status: str = "Open"


@dataclass
class RepairTask:
    taskId: Optional[int] = None
    taskName: str = ""
    status: str = "NotStarted"


class TaskSorter:
    """מחלקת המיון מתרשים Sequence דרישה 15 (נוצרת ב-«create» ונהרסת ב-«destroy»).
    sortTasksByUrgency ממיין לפי: דדליין, סטטוס, רמת עדיפות ועומס עבודה."""

    def sortTasksByUrgency(self, rawTaskList: List[dict]) -> List[dict]:
        from datetime import datetime

        def score(t):
            try:
                days = (datetime.strptime(t['deadline'], '%Y-%m-%d') - datetime.now()).days
            except Exception:
                days = 999
            status_weight = {'InProgress': 0, 'NotStarted': 1, 'Completed': 5, 'Cancelled': 6}.get(t.get('status'), 3)
            return (days, status_weight, int(t.get('priority_level') or 3), -int(t.get('workload') or 1))

        return sorted(rawTaskList, key=score)


@dataclass
class DamageAssessment:
    assessmentId: Optional[int] = None
    estimatedCost: float = 0.0


@dataclass
class QualityCheck:
    checkId: Optional[int] = None
    isApproved: bool = False


@dataclass
class Anomaly:
    anomalyId: Optional[int] = None
    type: str = ""


# ===== Module 3: Inventory & Logistics (לא נכלל בשלוש הדרישות; קיים לשם התאמה לתרשים) =====

@dataclass
class Part:
    partId: Optional[int] = None
    name: str = ""
    quantityInStock: int = 0
    minQuantity: int = 0
    price: float = 0.0


@dataclass
class PaintFormula(Part):
    formulaId: Optional[int] = None
    colorCode: str = ""
    mixRatio: str = ""


@dataclass
class Supplier:
    supplierId: Optional[int] = None
    name: str = ""


@dataclass
class ServiceCatalog:
    actionId: Optional[int] = None
    description: str = ""
    basePrice: float = 0.0


@dataclass
class PartOrder:
    orderId: Optional[int] = None
    date: str = ""
    status: str = "Created"


@dataclass
class PartOrderLine:
    quantity: int = 0
    unitPrice: float = 0.0

    def calculateLineTotal(self) -> float:
        return self.quantity * self.unitPrice
