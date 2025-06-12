# database_ops.py

import sqlite3
from datetime import datetime
from config import DB_NAME # Import DB_NAME from config

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            national_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            position TEXT,
            base_salary REAL NOT NULL
        )
    ''')

    # payroll table is now for historical full payrolls (payslips)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_national_id TEXT,
            payroll_month TEXT NOT NULL, -- YYYY-MM (e.g., 2023-01)
            base_salary_at_time REAL NOT NULL, -- Base salary when payroll was calculated
            overtime_hours REAL DEFAULT 0,
            absence_hours REAL DEFAULT 0,
            benefits REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            loan_deduction REAL DEFAULT 0, -- NEW: Loan deduction for this payroll
            net_payment REAL NOT NULL, -- Final amount paid to employee
            payslip_details TEXT, -- JSON/Text field for detailed breakdown
            recorded_date TEXT NOT NULL, -- Date this payroll was recorded
            FOREIGN KEY (employee_national_id) REFERENCES employees(national_id) ON DELETE CASCADE,
            UNIQUE(employee_national_id, payroll_month) -- Ensure only one payroll per month per employee
        )
    ''')

    # Absences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_national_id TEXT,
            absence_date TEXT NOT NULL,
            hours_absent REAL NOT NULL,
            reason TEXT,
            FOREIGN KEY (employee_national_id) REFERENCES employees(national_id) ON DELETE CASCADE
        )
    ''')

    # Overtimes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS overtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_national_id TEXT,
            overtime_date TEXT NOT NULL,
            hours_worked REAL NOT NULL,
            description TEXT,
            FOREIGN KEY (employee_national_id) REFERENCES employees(national_id) ON DELETE CASCADE
        )
    ''')

    # Leaves table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_national_id TEXT,
            leave_start_date TEXT NOT NULL,
            leave_end_date TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            duration_days REAL NOT NULL,
            description TEXT,
            FOREIGN KEY (employee_national_id) REFERENCES employees(national_id) ON DELETE CASCADE
        )
    ''')

    # NEW TABLE: Loans and Advances
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_national_id TEXT NOT NULL,
            loan_date TEXT NOT NULL,
            amount REAL NOT NULL,
            remaining_amount REAL NOT NULL,
            installment_amount REAL, -- Optional: suggested monthly deduction
            description TEXT,
            is_active INTEGER DEFAULT 1, -- 1 for active, 0 for paid off
            FOREIGN KEY (employee_national_id) REFERENCES employees(national_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def get_employee_data(national_id=None):
    """Fetches employee(s) data from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if national_id:
        cursor.execute("SELECT national_id, first_name, last_name, position, base_salary FROM employees WHERE national_id = ?", (national_id,))
        emp_data = cursor.fetchone()
    else:
        cursor.execute("SELECT national_id, first_name, last_name, position, base_salary FROM employees")
        emp_data = cursor.fetchall()
    conn.close()
    return emp_data

def add_employee_to_db(national_id, first_name, last_name, position, base_salary):
    """Adds a new employee to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO employees (national_id, first_name, last_name, position, base_salary) VALUES (?, ?, ?, ?, ?)",
                       (national_id, first_name, last_name, position, base_salary))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # national_id already exists
    finally:
        conn.close()

def update_employee_in_db(national_id, first_name, last_name, position, base_salary):
    """Updates an existing employee's data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET first_name=?, last_name=?, position=?, base_salary=? WHERE national_id=?",
                   (first_name, last_name, position, base_salary, national_id))
    conn.commit()
    conn.close()

def delete_employee_from_db(national_id):
    """Deletes an employee and their related records from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Due to ON DELETE CASCADE, deleting from employees will automatically delete from all related tables
    cursor.execute("DELETE FROM employees WHERE national_id = ?", (national_id,))
    conn.commit()
    conn.close()

def record_monthly_payroll_to_db(employee_national_id, payroll_month, base_salary_at_time,
                                  overtime_hours, absence_hours, benefits, deductions,
                                  loan_deduction, net_payment, payslip_details):
    """Records a complete monthly payroll (payslip) for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    recorded_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO payroll (employee_national_id, payroll_month, base_salary_at_time, 
                                 overtime_hours, absence_hours, benefits, deductions, 
                                 loan_deduction, net_payment, payslip_details, recorded_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (employee_national_id, payroll_month, base_salary_at_time,
              overtime_hours, absence_hours, benefits, deductions,
              loan_deduction, net_payment, payslip_details, recorded_date))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This indicates a unique constraint violation (payroll already exists for this month)
        return False
    finally:
        conn.close()

def get_payroll_history(employee_national_id):
    """Fetches full payroll history (payslips) for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT payroll_month, base_salary_at_time, overtime_hours, absence_hours, benefits, deductions, loan_deduction, net_payment, payslip_details, recorded_date FROM payroll WHERE employee_national_id = ? ORDER BY payroll_month DESC",
                   (employee_national_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def get_absences_in_month(employee_national_id, year_month):
    """Calculates total absence hours for an employee in a given YYYY-MM."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(hours_absent) FROM absences WHERE employee_national_id = ? AND STRFTIME('%Y-%m', absence_date) = ?",
                   (employee_national_id, year_month))
    total_hours = cursor.fetchone()[0]
    conn.close()
    return total_hours if total_hours is not None else 0

def get_overtimes_in_month(employee_national_id, year_month):
    """Calculates total overtime hours for an employee in a given YYYY-MM."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(hours_worked) FROM overtimes WHERE employee_national_id = ? AND STRFTIME('%Y-%m', overtime_date) = ?",
                   (employee_national_id, year_month))
    total_hours = cursor.fetchone()[0]
    conn.close()
    return total_hours if total_hours is not None else 0

def add_loan_to_db(employee_national_id, loan_date, amount, installment_amount, description=""):
    """Adds a new loan record for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO loans (employee_national_id, loan_date, amount, remaining_amount, installment_amount, description) VALUES (?, ?, ?, ?, ?, ?)",
                   (employee_national_id, loan_date, amount, amount, installment_amount, description))
    conn.commit()
    conn.close()

def get_active_loans(employee_national_id):
    """Fetches active loans for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, loan_date, amount, remaining_amount, installment_amount, description FROM loans WHERE employee_national_id = ? AND is_active = 1 ORDER BY loan_date ASC",
                   (employee_national_id,))
    loans = cursor.fetchall()
    conn.close()
    return loans

def update_loan_remaining_amount(loan_id, new_remaining_amount):
    """Updates the remaining amount of a loan. If remaining_amount <= 0, marks as inactive."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    is_active = 1 if new_remaining_amount > 0 else 0
    cursor.execute("UPDATE loans SET remaining_amount = ?, is_active = ? WHERE id = ?",
                   (new_remaining_amount, is_active, loan_id))
    conn.commit()
    conn.close()

def get_loan_by_id(loan_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, employee_national_id, loan_date, amount, remaining_amount, installment_amount, description, is_active FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    conn.close()
    return loan

def add_absence_to_db(employee_national_id, absence_date, hours_absent, reason=""):
    """Adds an absence record for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO absences (employee_national_id, absence_date, hours_absent, reason) VALUES (?, ?, ?, ?)",
                   (employee_national_id, absence_date, hours_absent, reason))
    conn.commit()
    conn.close()

def get_absences_history(employee_national_id):
    """Fetches absence history for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT absence_date, hours_absent, reason FROM absences WHERE employee_national_id = ? ORDER BY absence_date DESC",
                   (employee_national_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def add_overtime_to_db(employee_national_id, overtime_date, hours_worked, description=""):
    """Adds an overtime record for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO overtimes (employee_national_id, overtime_date, hours_worked, description) VALUES (?, ?, ?, ?)",
                   (employee_national_id, overtime_date, hours_worked, description))
    conn.commit()
    conn.close()

def get_overtime_history(employee_national_id):
    """Fetches overtime history for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT overtime_date, hours_worked, description FROM overtimes WHERE employee_national_id = ? ORDER BY overtime_date DESC",
                   (employee_national_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def add_leave_to_db(employee_national_id, leave_start_date, leave_end_date, leave_type, duration_days, description=""):
    """Adds a leave record for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leaves (employee_national_id, leave_start_date, leave_end_date, leave_type, duration_days, description) VALUES (?, ?, ?, ?, ?, ?)",
                   (employee_national_id, leave_start_date, leave_end_date, leave_type, duration_days, description))
    conn.commit()
    conn.close()

def get_leave_history(employee_national_id):
    """Fetches leave history for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT leave_start_date, leave_end_date, leave_type, duration_days, description FROM leaves WHERE employee_national_id = ? ORDER BY leave_start_date DESC",
                   (employee_national_id,))
    history = cursor.fetchall()
    conn.close()
    return history