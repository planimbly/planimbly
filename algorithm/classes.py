from sqlite3 import Date, Time


# data class for employees
class employee:
    def __init__(self, id: int, job_time: int):
        self.id = id
        self.job_time = job_time


# data class for existing schedules
class schedule:
    def __init__(self, id: int, date_start: Date, date_end: Date, shifts: list):
        self.id = id
        self.date_start = date_start
        self.date_end = date_end
        self.shifts = shifts


# data class for shift types
class shift_type:
    def __init__(self, id: int, hour_start: Time, hour_end: Time, id_workplace: int, active_days: str):
        self.id = id
        self.hour_start = hour_start
        self.hour_end = hour_end
        self.id_workplace = id_workplace
        self.active_days = active_days


# data class for shifts
class shift:
    def __init__(self, id: int, id_emp: int, id_sched: int, date: Date, shift_type: shift_type):
        self.id = id
        self.id_employee = id_emp
        self.id_schedule = id_sched
        self.date = date
        self.shift_type = shift_type


# data class for the input
class data:
    def __init__(self, employees: list, schedules: list, date_start: Date, date_end: Date, s_types: list):
        self.employees = employees
        self.schedules = schedules
        self.date_start = date_start
        self.date_end = date_end
        self.shift_type = s_types
