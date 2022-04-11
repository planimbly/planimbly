from sqlite3 import Date, Time

# data class for employees
class employee:
    def __init__(self, id : int, job_time : int):
        self.id = id
        self.job_time = job_time

# data class for existing schedules
class schedule:
    def __init__(self, id : int, date_start : Date, date_end : Date, shifts : list):
        self.id = id
        self.date_start = date_start
        self.date_end = date_end
        self.shifts = shifts

# data class for shift types
class shift_type:
    def __init__(self, id : int, hour_start : Time, hour_end : Time, id_workplace : int, active_days : str):
        self.id = id
        self.hour_start = hour_start
        self.hour_end = hour_end
        self.id_workplace = id_workplace
        self.active_days = active_days

# data class for shifts
class shift:
    def __init__(self, id : int, id_emp : int, id_sched : int, date : Date, shift_type : shift_type):
        self.id = id
        self.id_employee = id_emp
        self.id_schedule = id_sched
        self.date = date
        self.shift_type = shift_type

# data class for the input
class data:
    def __init__(self, employees : list, schedules : list, date_start : Date, date_end : Date):
        self.employees = employees
        self.schedules = schedules
        self.date_start = date_start
        self.date_end = date_end

# function for preparing data for the algorithm
def gather_data():
    employees = [] # employee list
    schedules = [] # already existing schedules

    # gathering data from the server

    # sample data
    e = employee(1, 8)
    employees.append(e)

    d = data(employees, schedules)

    return d

# schedule making function
def make_schedule(data : data):
    # placeholder code for now

    # sample data
    emp : employee = data.employees[-1]
    st = shift_type(1, Time(8, 30), Time(16, 30), 1, '1111100')

    shifts = []

    # magic algorithm preparing the schedule

    d = Date(2022, 4, 12)

    shifts.append(
        {
            'id': 1, # shift id
            'id_employee': emp,
            'date': d,
            'shift_type': st.id # shift_type id
        }
    )

    # sample dictionary prepared for sending over to the server
    schedule = {
        'id': 1, # schedule id
        'date_start': data.date_start,
        'date_end': data.date_end,
        'shifts': shifts
    }

    return schedule

# function for sending the data to the server
def send_data(schedule : dict):
    pass

def main():
    data = gather_data()
    schedule = make_schedule(data)
    send_data(schedule)

if __name__ == "__main__":
    main()
