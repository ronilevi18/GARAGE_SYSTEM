# אור הבזק — מערכת ניהול מוסך (Flask + SQLite, עברית RTL)

מערכת מקומית הרצה לחלוטין ללא אינטרנט. שכבת GUI ב-Flask, לוגיקה בבקרים (Controllers),
ונתונים ב-SQLite — בהתאמה מלאה לתרשימי המחלקות ולתרשימי ה-Sequence של חלק ב'.

## דרישות מקדימות
- Python 3.10 ומעלה
- חבילה אחת בלבד: Flask

## הרצה (ב-VS Code)
```bash
# 1. התקנת Flask (פעם אחת)
pip install flask

# 2. יצירת בסיס הנתונים ומילוי נתונים ראשוניים (פעם אחת)
python seed_data.py

# 3. הרצת המערכת
python app.py
```

## משתמשי הדגמה (נטענים מבסיס הנתונים)
- `manager` / `1234` — מנהל מוסך (רשאי לכל הדרישות)
- `painter` / `1234` — צבעי
- `body` / `1234` — פחח

## מבנה הפרויקט
```
GARAGE_SYSTEM/
├── app.py                         # שכבת ה-GUI (Flask) = ה-actor "GUI" בתרשימים
├── seed_data.py                   # נתונים ראשוניים
├── db/
│   ├── schema.sql                 # כל טבלאות בסיס הנתונים (תואם ERD)
│   └── database.py                # מחלקת Database (שמות שיטות מהתרשים)
├── models/
│   └── entities.py                # כל מחלקות תרשים המחלקות
├── controllers/
│   ├── work_order_controller.py   # דרישה 3
│   ├── task_controller.py         # דרישה 15 (+ TaskSorter)
│   ├── report_controller.py       # דרישה 20
│   ├── auth_controller.py         # כניסה (User.login / checkPermissions)
│   └── system_log_controller.py   # יומן מערכת
├── templates/                     # מסכי HTML בעברית RTL
├── static/style.css               # גיליון העיצוב הראשי
└── docs/
    ├── sequence_mapping.md        # מיפוי מלא תרשים ↔ קוד (לסעיף 8.1)
    └── select_queries_for_presentation.sql  # שאילתות הוכחה להצגה
```

## למה Flask ולא Console / Tkinter
- סעיף 1 דורש GUI גרפי (לא Console). ✔
- שפת הממשק עברית, בהתאם לקהל היעד (צוות מוסך ישראלי) — סעיף 3. ✔
- רץ מקומית על localhost ללא אינטרנט/קליטה — מתאים להצגה בכיתה (סעיף 6). ✔
- הפרדת GUI ↔ Controller ↔ Database תואמת ישירות את תרשימי ה-Sequence. ✔

## הוכחת השפעה על המערכת (סעיף 8)
בסיום כל דרישה ניתן להריץ את השאילתות שב-`docs/select_queries_for_presentation.sql`
כדי להציג את הטבלאות המעודכנות עם עמודות `created_at` / `updated_at` ברמת השנייה.
