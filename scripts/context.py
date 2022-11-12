from datetime import date, datetime as dt, timedelta
from apps.accounts.models import Employee
from apps.schedules.models import ShiftType
from scripts.helpers import get_month_by_weeks, flatten


class ShiftTypeInfo:
    shift_type = ShiftType
    duration = 0
    id = 0

    def __init__(self, st: ShiftType, id: int):
        self.shift_type = st
        self.id = id
        self.duration = (dt.combine(date.min, self.shift_type.hour_end) - dt.combine(date.min,
                                                                                     self.shift_type.hour_start)).seconds // 60
        print(self)

    def get_duration_in_minutes(self):
        return self.duration

    def get_duration_in_hours(self):
        return self.duration / 60

    def get(self):
        return self.shift_type

    def __str__(self):
        return "[SHIFT] ID: %i | Duration: %.1f | %s | %s" % (self.id,
                                                              self.get_duration_in_hours(),
                                                              self.shift_type.workplace,
                                                              self.shift_type.name)


class EmployeeInfo:
    employee = Employee
    workplaces = []
    preferences = []
    absences = []
    absent_days = []

    def __init__(self, emp: Employee, wp: list, pref: list, ab: list):
        self.employee = emp
        self.workplaces = wp
        self.preferences = pref
        self.absences = ab
        self.absent_days = self.prepare_absent_days()
        print(self.workplaces, self.preferences, self.absences, self.absent_days)

    def prepare_absent_days(self):
        ad = []
        for ab in self.absences:
            for i in range((ab.end - ab.start).days + 1):
                inter_date = ab.start + timedelta(days=i)
                ad.append(inter_date)
                print("added absence for emp %i on day %i" % (ab.employee.pk, inter_date.day))
        return ad

    def get_absent_days_in_month(self, month: int):
        """ Returns days on which given employee is absent """
        return [d.day for d in self.absent_days if d.month == month]

    def get(self):
        return self.employee

    def __str__(self):
        return "[EMPLOYEE] ID: %i | JT: %i | %s %s" % (self.employee.pk,
                                                       self.employee.job_time,
                                                       self.employee.first_name,
                                                       self.employee.last_name)


class Context:
    year = 0
    month = 0
    total_work_time = int
    total_job_time = int
    job_time_multiplier = float
    overtime_multiplier = float
    month_by_weeks = []
    # Fixed assignment: (employee, shift, day).
    fixed_assignments = []
    # Request: (employee, shift, day, weight)
    # A negative weight indicates that the employee desire this assignment.
    requests = []

    employees = []
    shift_types = []
    weekly_cover_demands = []
    illegal_transitions = []
    overnight_shifts = []

    def __init__(self, emp: list[EmployeeInfo], st: list[ShiftType], year: int, month: int):
        self.year = year
        self.month = month
        self.month_by_weeks = get_month_by_weeks(year, month)
        self.employees = emp
        self.shift_types = [ShiftTypeInfo(s, st.index(s)) for s in st]
        self.weekly_cover_demands = [tuple(s.get().demand for s in self.shift_types[1:]) for _ in range(7)]
        self.requests = self.prepare_requests()
        self.fixed_assignments = self.prepare_fixed_assignments()
        self.illegal_transitions = self.find_illegal_transitions()
        self.overnight_shifts = self.find_overnight_shifts()
        self.total_work_time = self.calc_total_work_time()
        self.total_job_time = sum(ei.get().job_time for ei in self.employees)
        self.job_time_multiplier = self.total_work_time / self.total_job_time
        self.overtime_multiplier = (self.total_work_time - sum(ei.get().job_time for ei in self.get_full_time_employees())) \
            / (self.total_job_time - sum(ei.get().job_time for ei in self.get_full_time_employees()))

    def find_illegal_transitions(self):
        """Finds illegal transitions between shift types
        Returns a list of tuples of given structure:
        (i, j, p)
        i - index of shift that is transitioning to 'j'
        j - index of shift that 'i' transitions to
        p - penalty of transition between shift 'i' to shift 'j'
        """
        it = []
        for i in self.shift_types[1:]:
            i_start = dt.combine(date.min, i.get().hour_start)
            i_end = i_start + timedelta(minutes=i.duration)  # do all of above in case of overnight shifts
            for j in self.shift_types[1:]:
                if i == j:
                    continue
                j_start = dt.combine(date.min + timedelta(days=1), j.get().hour_start)
                s_delta = j_start - i_end
                s_delta = int(s_delta.total_seconds() // 60)
                # print(f"Delta between {i.get().name} and {j.get().name}: {s_delta / 60}h")
                if s_delta < (11 * 60):  # break between i and j is below 11 hours
                    print(f"Found illegal transition: {i.get().name} to {j.get().name}")
                    # TODO: think about returning a list instead of tuples (np zeby przechowywac transitions dla wiecej niz 2 zmian)
                    it.append((i.id, j.id, 0))
        return it

    def find_overnight_shifts(self):
        """Determines which shifts are happening overnight
        Returns a tuple of given structure for each overnight shift constraint:
        (shift, hard_min, soft_min, min_penalty,
                soft_max, hard_max, max_penalty)
        """
        # NOTE: * kiedyś może trzeba będzie poeksperymentować z karami za nocki, lub damy ustawić to użytkownikowi
        #       * na razie to działa poprawnie tylko w przypadku gdy jest tylko jedna nocna zmiana
        # TODO: przerobić funkcję do weekly constraintów żeby mogła przyjmować sumę shiftów
        sc = []
        wsc = []
        for i in self.shift_types:
            start = i.get().hour_start.hour
            end = i.get().hour_end.hour
            if end < start:
                print(f"Found overnight shift: {i.get().name}")
                # between 2 and 3 consecutive days of night shifts, 1 and 4 are possible but penalized.
                sc.append((i.id, 1, 2, 20, 3, 4, 5))
                # At least 1 night shift per week (penalized). At most 4 (hard).
                wsc.append((i.id, 0, 1, 2, 3, 4, 0))
        return sc, wsc

    def get_shift_info_by_id(self, id: int):
        return next(x for x in self.shift_types if x.id == id)

    def calc_total_work_time(self):
        total_minutes = 0
        num_month_weekdays = []
        for d in range(len(self.weekly_cover_demands)):
            num_month_weekdays.append(sum([x[1] == d for x in flatten(self.month_by_weeks)]))

        for d in range(len(self.weekly_cover_demands)):
            for s in range(len(self.weekly_cover_demands[d])):  # s for num_month_weekdays, s+1 for shift_types
                if self.shift_types[s + 1] == "-":
                    continue
                total_minutes += num_month_weekdays[d] * self.shift_types[s + 1].duration
        return total_minutes / 60

    def prepare_requests(self):
        req = []
        for ei in self.employees:
            for pref in ei.preferences:
                for week in self.month_by_weeks:
                    for d in week:
                        if pref.active_days[d[1] - 1] == "1":
                            req.append((ei.employee.pk,
                                        next(st.id for st in self.shift_types if pref.shift_type == st.get()), d[0],
                                        -1))
        return req

    def prepare_fixed_assignments(self):
        fa = []
        for ei in self.employees:
            for d in ei.get_absent_days_in_month(self.month):
                fa.append((ei.employee.pk, 0, d))
        return fa

    def get_full_time_employees(self):
        return [ei for ei in self.employees if ei.get().job_time == 160]
