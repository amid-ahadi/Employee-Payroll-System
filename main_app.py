# main_app.py

import tkinter as tk
from database_ops import init_db # Import init_db from database_ops
from frames import LoginFrame, MainMenuFrame, AddEmployeeFrame, ViewEmployeesFrame, SearchEditDeleteFrame, PayrollManagementFrame, AbsenceOvertimeLeaveFrame, ReportsFrame

class EmployeeManagerApp:
    def __init__(self, master):
        self.master = master
        master.title("سیستم جامع مدیریت کارمندان")
        master.geometry("1000x700") # Increased window size
        master.resizable(True, True) # Allow resizing for better table view

        init_db() # Initialize the database

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        self.current_frame = None
        self.create_login_frame()

    def show_frame(self, frame_class, *args, **kwargs):
        """Hides the current frame and shows the new one."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = frame_class(self.master, self, *args, **kwargs)
        self.current_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def create_login_frame(self):
        self.show_frame(LoginFrame)

    def create_main_menu_frame(self):
        self.show_frame(MainMenuFrame)

    def create_add_employee_frame(self):
        self.show_frame(AddEmployeeFrame)

    def create_view_employees_frame(self):
        self.show_frame(ViewEmployeesFrame)

    def create_search_edit_delete_frame(self):
        self.show_frame(SearchEditDeleteFrame)

    def create_payroll_management_frame(self):
        self.show_frame(PayrollManagementFrame)

    def create_absence_overtime_leave_frame(self, employee_national_id):
        self.show_frame(AbsenceOvertimeLeaveFrame, employee_national_id=employee_national_id)

    def create_reports_frame(self):
        self.show_frame(ReportsFrame)

# --- Main execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeManagerApp(root)
    root.mainloop()