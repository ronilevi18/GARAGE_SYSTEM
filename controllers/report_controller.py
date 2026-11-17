"""
בקר דוחות — דרישה 20: דוח זמן טיפול מורכב.
מתאים למחלקת ReportController בתרשים, ולתרשים ה-Sequence:
  GUI -> queryOpenWorkOrders(filters) -> Database.getOpenWorkOrders(filters) -> openWorkOrdersList
  loop (כל הזמנת עבודה): queryStatusHistory(workOrderId) -> Database.getStatusHistoryById(workOrderId)
  Controller -> calculateReportMetrics(openWorkOrdersList) -> reportMetrics
  Controller -> saveGeneratedReport(reportMetrics) -> Database.saveReportMetrics(metrics)
"""
from datetime import datetime
from db.database import Database, now_ts
from controllers.system_log_controller import SystemLogController

WORK_TYPE_HE = {'BodyRepair': 'פחחות', 'PaintServices': 'צבע', 'ThirdPartyAccident': 'תאונת צד ג׳'}


class ReportController:
    def __init__(self, db: Database):
        self.db = db
        self.log = SystemLogController(db)

    # --- queryOpenWorkOrders(filters) ---
    def queryOpenWorkOrders(self, filters: dict):
        return self.db.getOpenWorkOrders(filters)

    # --- queryStatusHistory(workOrderId) ---
    def queryStatusHistory(self, workOrderId: int):
        return self.db.getStatusHistoryById(workOrderId)

    # --- calculateReportMetrics(openWorkOrdersList) ---
    def calculateReportMetrics(self, openWorkOrdersList: list):
        from db.database import STATION_CHAIN, STATION_HE
        rows = []
        total_hours = 0.0
        bottlenecks = []
        type_counts = {'BodyRepair': 0, 'PaintServices': 0, 'ThirdPartyAccident': 0}
        station_totals = {}   # station -> {'total':h, 'count':n}
        for case in openWorkOrdersList:
            created = datetime.strptime(case['created_at'], '%Y-%m-%d %H:%M:%S')
            hours_open = round((datetime.now() - created).total_seconds() / 3600, 1)
            total_hours += hours_open
            wt = case.get('work_type', 'BodyRepair')
            type_counts[wt] = type_counts.get(wt, 0) + 1
            # זמן מצטבר בכל תחנה (לגרף) + התחנה הנוכחית והזמן בה (לעמודה)
            station_times = self.db.getStationTimesByCase(case['work_case_id'])
            for st, hrs in station_times.items():
                agg = station_totals.setdefault(st, {'total': 0, 'count': 0})
                agg['total'] = round(agg['total'] + hrs, 1)
                agg['count'] += 1
            cur_station, cur_hours = self.db.getCurrentStationHours(case['work_case_id'])
            is_bottleneck = cur_hours > 48   # מעל יומיים באותה תחנה = צוואר בקבוק
            if is_bottleneck:
                bottlenecks.append(case['case_number'])
            rows.append({
                'case_number': case['case_number'],
                'vehicle_number': case['license_plate'],
                'work_type': WORK_TYPE_HE.get(wt, wt),
                'current_status': case['status'],
                'hours_case_open': hours_open,                       # כמה שעות התיק פתוח (סה"כ)
                'current_station': STATION_HE.get(cur_station, '—'),  # התחנה הנוכחית
                'hours_in_current_station': cur_hours,                # כמה שעות הרכב באותה תחנה
                'bottleneck': 'כן' if is_bottleneck else 'לא',
            })
        avg = round(total_hours / len(rows), 1) if rows else 0
        total_cases = len(rows) or 1
        pie = [
            {'label': 'פחחות', 'key': 'BodyRepair', 'count': type_counts['BodyRepair'],
             'percent': round(type_counts['BodyRepair'] * 100 / total_cases)},
            {'label': 'צבע', 'key': 'PaintServices', 'count': type_counts['PaintServices'],
             'percent': round(type_counts['PaintServices'] * 100 / total_cases)},
            {'label': 'תאונת צד ג׳', 'key': 'ThirdPartyAccident', 'count': type_counts['ThirdPartyAccident'],
             'percent': round(type_counts['ThirdPartyAccident'] * 100 / total_cases)},
        ]
        # גרף תחנות לפי סדר השרשרת (תווית עברית), כולל ממוצע
        stations = []
        for st in STATION_CHAIN:
            agg = station_totals.get(st)
            if agg and agg['total'] > 0:
                stations.append({
                    'station': STATION_HE[st],
                    'total': agg['total'],
                    'count': agg['count'],
                    'avg': round(agg['total'] / agg['count'], 1) if agg['count'] else 0,
                })
        return {
            'rows': rows,
            'average_open_hours': avg,
            'total_cases': len(rows),
            'bottlenecks': bottlenecks,
            'pie': pie,
            'stations': stations,
            'generated_at': now_ts(),
        }

    # --- ייצוא הדוח לקובץ CSV שנפתח באקסל (ללא תלות בספריות) ---
    def exportToCsv(self, metrics: dict, path: str):
        import csv
        with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['מס תיק', 'מספר רכב', 'סוג', 'תחנה נוכחית',
                        'שעות שהתיק פתוח', 'שעות בתחנה הנוכחית', 'צוואר בקבוק'])
            for r in metrics['rows']:
                w.writerow([r['case_number'], r['vehicle_number'], r['work_type'], r['current_station'],
                            r['hours_case_open'], r['hours_in_current_station'], r['bottleneck']])
            w.writerow([])
            w.writerow(['תחנה', 'סך שעות', 'מספר רכבים', 'ממוצע שעות'])
            for s in metrics['stations']:
                w.writerow([s['station'], s['total'], s['count'], s['avg']])
        return path

    # --- saveGeneratedReport(reportMetrics) ---
    def saveGeneratedReport(self, reportMetrics: dict, filters: dict, user_id: int) -> int:
        report_id = self.db.saveReportMetrics(reportMetrics, 'דוח זמן טיפול', filters, user_id)
        self.log.logChange(user_id, report_id, 'Save Treatment Time Report', 'GeneratedReport')
        return report_id
