from datetime import date, datetime as dt, timedelta
from apps.accounts.models import Employee
from apps.schedules.models import ShiftType
from scripts.helpers import get_month_by_weeks, get_month_by_billing_weeks, flatten, get_letter_for_weekday
from loguru import logger


class ShiftTypeInfo:
    """
        # TODO: docstrings here
    """
    shift_type = ShiftType
    duration = 0
    id = 0

    def __init__(self, st: ShiftType, index: int):
        self.shift_type = st
        self.id = index
        self.duration = (dt.combine(date.min, self.shift_type.hour_end) -
                         dt.combine(date.min, self.shift_type.hour_start)).seconds // 60
        print(self)

    def get_duration_in_minutes(self):
        return self.duration

    def get_duration_in_hours(self):
        return self.duration / 60

    def get(self):
        return self.shift_type

    def __str__(self):
        return "[SHIFT] ID: %i | Duration: %.1f | %s | %s | demand: %i" % \
               (self.id, self.get_duration_in_hours(), self.shift_type.workplace, self.shift_type.name, self.shift_type.demand)


class EmployeeInfo:
    """
        # TODO: docstrings here
    """
    employee = Employee
    workplaces = []
    preferences = []
    absences = []
    absent_days = []
    absent_time = 0
    job_time = 0
    term_assignments = []
    negative_indefinite_assignments = []
    positive_indefinite_assignments = []
    allowed_shift_types = {}  # Key: Shift_type object, Value: list of allowed days
    weekly_constraints = []
    work_time_constraint = (0, 0, 0, 0, 0, 0)  # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)

    def __init__(self, emp: Employee, wp: list, pref: list, ab: list, ass: list, jt: int):
        self.employee = emp
        self.workplaces = wp
        self.preferences = pref
        self.absences = ab
        self.absent_days, self.absent_time = self.prepare_absent_days()
        self.term_assignments, \
            self.negative_indefinite_assignments, \
            self.positive_indefinite_assignments = self.prepare_assignments(ass)
        if len(self.negative_indefinite_assignments) > 0 and len(self.positive_indefinite_assignments) > 0:
            print("[WARNING] both negative and positive indefinite assignments were found for employee %i" % self.get().pk)
        self.job_time = self.calculate_job_time(jt)
        self.job_time -= self.absent_time

    def calculate_job_time(self, jt):
        match self.employee.job_time:
            case '1':
                return jt
            case '1/2':
                return jt // 2
            case '1/4':
                return jt // 4
            case '3/4':
                return jt * 3 // 4

    def prepare_assignments(self, assignments: list):
        ta = []
        nia = []
        pia = []
        print(assignments)
        for a in assignments:
            if a.end is not None and a.start is not None:
                # term assignments
                for i in range((a.end - a.start).days + 1):
                    inter_date = a.start + timedelta(days=i)
                    ta.append((a.shift_type, a.negative_flag, inter_date))
                    print("[ASSIGNMENT] EMP: %2i | DAY: %2i | ST: %i | TYPE: %s" %
                          (a.employee.pk, inter_date.day, a.shift_type.id, "negative" if a.negative_flag else "positive"))
            else:
                # indefinite_assignments
                if a.negative_flag:
                    nia.append(a.shift_type)
                else:
                    pia.append(a.shift_type)
                print("[ASSIGNMENT] EMP: %2i | ST: %i | TYPE: %s" % (a.employee.pk, a.shift_type.id, "negative" if a.negative_flag else "positive"))
        return ta, nia, pia

    def prepare_absent_days(self):
        ad = []
        at = 0
        for ab in self.absences:
            at += ab.hours_number
            for i in range((ab.end - ab.start).days + 1):
                inter_date = ab.start + timedelta(days=i)
                ad.append(inter_date)
                logger.success("[ABSENCE] EMP: {:2d} | DAY: {:2d}".format(ab.employee.pk, inter_date.day))
        return ad, at

    def get_absent_days_in_month(self, month: int):
        """ Returns days on which given employee is absent """
        return [d.day for d in self.absent_days if d.month == month]

    def get(self):
        return self.employee

    def __str__(self):
        return "[EMPLOYEE] ID: %2i | JT: %3i | %s %s" % \
               (self.employee.pk, self.job_time, self.employee.first_name, self.employee.last_name)


class Context:
    """
    A class used to keep some bases for algorithm.

    Attributes:
    -------
    employees : list[EmployeeInfo]
        The list containing EmployeeInfo objects with all considered employees
    shift_types : list[ShiftType]
        The list containing ShiftType objects with all considered shifts
    weekly_cover_demands : list
        The list containing information about cover demands for shifts
    month : int
        The month we generate schedule for.
    year : int
        The year for the month.
    month_by_weeks : list
        The list of list. Primary lists represents month. Sub-lists represent weeks. Elements are tuples (day number, weekday number).
    month_by_billing_weeks : list
        The same stuff as month_by_weeks, however weeks are days 1-7, 8-14, etc..
    job_time : int
        The amount of hours for full time employees to fulfil their minimum hours number.
    fixed_assignments : list
        The list containing employee's id, shift's id and day for a fixed (set, hardcoded) schedule assignment.
    requests : list
        The list containing employee's id, shift's id, day and request weight for an employee requested assignment.
    illegal_transitions : list
        The list containing
    overnight_shifts : list
        The list containing detected overnight shifts (we need them for night shifts limitations).
    total_work_time : int
        The number of hours during month to cover based on weekly cover demands.
    total_job_time : int
        The sum of employees job times.
    max_work_time : int
        Maximal work time we can assign to employees.
    job_time_multiplier : float
        Total work time to total job time ratio.
    overtime_multiplier : float
        Overtime ratio for part-time employees.
    overtime_for_full_timers = bool
        True/false indicator for full-timers overtime (if true, we give additional hours to full-timers)
    overtime_above_full_time : int
        The number of hours to divide among full-timers.

    Methods:
    -------
    find_illegal_transitions
        Finds illegal transitions between shift types
    find_overnight_shifts
        Determines which shifts are happening overnight.
    get_shift_info_by_id
        Simple function to quickly get ShiftTypeInfo object from shift id.
    calculate_total_worktime
        Calculates total worktime during month (IN HOURS!), based on cover demands.
    prepare_requests
        Fetches employees requests and prepares them to be used later.
    prepare_fixed_assignments
        Prepares absent days for each employee to be added to fixed assignments.
    get_full_time_employees
        Filters employees and gets a list of full time employees.
    """

    # Bases: shifts and employees
    employees = []
    shift_types = []
    weekly_cover_demands = []

    # Timing and billing variables
    month = 0
    year = 0
    month_by_weeks = []
    month_by_billing_weeks = []

    job_time = int

    # Fixed assignment: (employee, shift, day).
    fixed_assignments = []
    # Request: (employee, shift, day, weight // negative weight -> employee desires assignment)
    requests = []

    # Illegal transitions and overnight shifts lists
    illegal_transitions = []
    overnight_shifts = []

    # Worktime and job time variables
    total_work_time = int
    total_job_time = int
    max_work_time = int

    # Multipliers
    job_time_multiplier = float
    overtime_multiplier = float
    overtime_for_full_timers = bool
    overtime_above_full_time = int

    def __init__(self, emp: list[EmployeeInfo], st: list[ShiftType], year: int, month: int, jt: int) -> None:
        """
        Args:
            emp: list of EmployeeInfo objects containing information about employees,
            st - list of ShiftType objects containing information about shifts,
            year - considered year passed from main function,
            month - considered month passed from main function,
            jt - full-time job worktime for given month,
        """

        # Preparing bases: shifts and employees
        self.shift_types = [ShiftTypeInfo(s, s.pk) for s in st]
        if len(self.shift_types) <= 1:  # 1 not 0, because when comparing to 0 it doesn't work - we have a free shift!
            logger.critical("NO SHIFTS!")

        self.weekly_cover_demands = [tuple(s.get().demand for s in self.shift_types[1:]) for _ in range(7)]

        self.employees = emp
        if not self.employees:
            logger.critical("NO EMPLOYEES!")

        # Preparing timing and billing stuff
        self.month = month
        logger.trace("Given month: {}".format(self.month))
        self.year = year
        logger.trace("Given year: {}".format(self.year))
        self.month_by_weeks = get_month_by_weeks(year, month)
        logger.trace("Month separated into weeks: {}".format(self.month_by_weeks))
        self.month_by_billing_weeks = get_month_by_billing_weeks(year, month)
        logger.trace("Month separated into billing weeks: {}".format(self.month_by_billing_weeks))
        self.job_time = jt
        logger.trace("Given job time for month: {}".format(self.job_time))

        # Preparing requests and absences
        if self.prepare_requests():
            self.requests = self.prepare_requests()
            logger.trace("Returned requests {}.".format(self.requests))
        else:
            logger.info("There are no employees' requests")

        if self.prepare_fixed_assignments():
            self.fixed_assignments = self.prepare_fixed_assignments()
            logger.trace("Returned absences {}.".format(self.fixed_assignments))
        else:
            logger.info("There are no absences")

        # Searching for illegal transitions and overnight shifts
        if self.find_illegal_transitions():
            self.illegal_transitions = self.find_illegal_transitions()
            logger.trace("Returned illegal transitions {}.".format(self.illegal_transitions))
        else:
            logger.info("No illegal transitions")

        if self.find_overnight_shifts():
            self.overnight_shifts = self.find_overnight_shifts()
            logger.trace("Found overnight shifts: {}.".format([s[0] for s in self.overnight_shifts[0]]))
        else:
            logger.info("No overnight shifts")

        # Calculating worktime and job time stuff
        self.total_work_time = self.calculate_total_worktime()
        self.total_job_time = sum(ei.job_time for ei in self.employees)
        logger.trace("Calculated total worktime: {}; job time: {}.".format(self.total_work_time, self.total_job_time))
        # TODO: calculate max_work_time for each employee in EmployeeInfo
        # TODO: calculate it from weekly_cover_demands, not hardcoded
        self.max_work_time = len(self.employees) * (len(flatten(self.month_by_weeks)) - 4) * 8
        logger.trace("Calculated maximum worktime: {}".format(self.max_work_time))

        # Calculating multipliers
        self.job_time_multiplier = self.total_work_time / self.total_job_time
        logger.trace("Calculated job time multiplier: {}".format(self.job_time_multiplier))

        if len(self.get_full_time_employees()) == 0:
            logger.warning("There are no full time employees!")
        elif len(self.employees) == len(self.get_full_time_employees()):
            self.overtime_multiplier = 1
        else:
            self.overtime_multiplier = (self.total_work_time - sum(ei.job_time for ei in self.get_full_time_employees())) \
                                   / (self.total_job_time - sum(ei.job_time for ei in self.get_full_time_employees()))

        self.overtime_for_full_timers = sum(self.job_time - ei.absent_time for ei in self.employees) < self.total_work_time
        self.overtime_above_full_time = self.total_work_time - sum(self.job_time - ei.absent_time for ei in self.employees)
        logger.trace("Calculated overtime multiplier {}; for full-timers {}, above full-time {}.".format(
            self.overtime_multiplier, self.overtime_for_full_timers, self.overtime_above_full_time))

    def find_illegal_transitions(self) -> list[tuple[int, int, int]]:
        """Finds illegal transitions between shift types

        - i - index of shift that is transitioning to 'j',
        - j - index of shift that 'i' transitions to,
        - p - penalty of transition between shift 'i' to shift 'j'

        Returns:
            a list of tuples of given structure (i, j, p)
        """

        logger.trace("Looking for illegal transitions started...")

        it = []

        for i in self.shift_types[1:]:
            i_start = dt.combine(date.min, i.get().hour_start)
            i_end = i_start + timedelta(minutes=i.duration)  # do all above in case of overnight shifts
            for j in self.shift_types[1:]:
                if i == j:
                    continue
                j_start = dt.combine(date.min + timedelta(days=1), j.get().hour_start)
                s_delta = j_start - i_end
                s_delta = int(s_delta.total_seconds() // 60)
                if s_delta < (11 * 60):  # break if difference between: i, j is below 11 hours
                    logger.info("Found illegal transition: {} to {}". format(i.get().name, j.get().name))
                    # TODO: think about returning a list instead of tuples (np żeby przechowywać transitions dla więcej niż 2 zmian)
                    it.append((i.id, j.id, 0))

        logger.trace("Looking for illegal transitions ended.")

        return it

    def find_overnight_shifts(self) -> tuple[list[tuple[int, int, int, int, int, int, int]], list[tuple[int, int, int, int, int, int, int]]]:
        """ Determines which shifts are happening overnight.

        Returns:
            a tuple of given structure for each overnight shift constraint - (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
        """

        # FIXME: * kiedyś może trzeba będzie poeksperymentować z karami za nocki, lub damy ustawić to użytkownikowi
        #        * na razie to działa poprawnie tylko w przypadku gdy jest tylko jedna nocna zmiana
        # TODO: przerobić funkcję do weekly constraints żeby mogła przyjmować sumę shiftów

        logger.trace("Looking for overnight shifts started...")

        sc = []
        wsc = []

        for i in self.shift_types:
            start = i.get().hour_start.hour
            end = i.get().hour_end.hour
            # TODO: we should be comparing hours with datetime, just in case sometime we have super long shifts to consider
            if end < start:
                logger.info("Found overnight shift: {}".format(i.get().name))
                # Between 2 and 3 consecutive days of night shifts, 1 and 4 are possible but penalized.
                sc.append((i.get().id, 1, 2, 20, 3, 4, 5))
                # At least 1 night shift per week (penalized). At most 4 (hard).
                # TODO: Maybe consider term assignments here ???
                wsc.append((i.get().id, 0, 1, 2, 3, 4, 0))

        logger.trace("Looking for overnight shifts ended.")

        return sc, wsc

    def get_shift_info_by_id(self, index: int) -> ShiftTypeInfo:
        """ Simple function to quickly get ShiftTypeInfo object from shift id.

        Args:
            index: given shift id
        Returns:
            wanted ShiftTypeInfo object
        """

        return next(x for x in self.shift_types if x.id == index)

    def calculate_total_worktime(self) -> int | float:
        """ Calculates total worktime during month (IN HOURS!), based on cover demands.

            Returns:
                number of hours to share among employees during month (either int or float - depends on shifts duration).
        """

        logger.trace("Calculating total worktime started...")

        total_minutes = 0
        num_month_weekdays = []

        for d in range(len(self.weekly_cover_demands)):
            num_month_weekdays.append(sum([x[1] == d for x in flatten(self.month_by_billing_weeks)]))

        for d in range(len(self.weekly_cover_demands)):
            for s in range(len(self.weekly_cover_demands[d])):  # s for num_month_weekdays, s+1 for shift_types
                if self.shift_types[s + 1] == "-":
                    continue
                total_minutes += num_month_weekdays[d] * self.shift_types[s + 1].duration

        logger.trace("Calculating total worktime ended.")

        return total_minutes / 60

    def prepare_requests(self) -> list:
        """ Fetches employees requests and prepares them to be used later.

        Returns:
            list of employees requests prepared to be added to model in run_algorithm.py.
        """

        logger.trace("Preparing requests started...")

        req = []

        for ei in self.employees:
            for pref in ei.preferences:
                for week in self.month_by_billing_weeks:
                    for d in week:
                        if pref.active_days[d[1]] == "1":
                            req.append((ei.employee.pk, next(st.get().id for st in self.shift_types if pref.shift_type == st.get()), d[0], -1))
                            logger.success("[PREFERENCE] EMP: {:2d} | shift: {} | day: {:2d} ({}) | weight: {:d}".format(
                                ei.employee.pk, next(st.get().name for st in self.shift_types if pref.shift_type == st.get()),
                                d[0], get_letter_for_weekday(d[1]), -1))

        logger.trace("Preparing requests ended.")

        return req

    def prepare_fixed_assignments(self) -> list:
        """ Prepares absent days for each employee to be added to fixed assignments.

        Returns:
            list of absences prepared to be added to fixed assignments.
        """

        logger.trace("Preparing fixes assignments started.")

        fa = []

        for ei in self.employees:
            for d in ei.get_absent_days_in_month(self.month):
                fa.append((ei.employee.pk, 0, d))

        logger.trace("Preparing fixes assignments ended.")

        return fa

    def get_full_time_employees(self) -> list:
        """Filters employees and gets a list of full time employees.

        Returns:
            list of full time employees or empty list if there are no full time employees.
        """
        logger.trace("Getting full-time employees.")

        return [ei for ei in self.employees if ei.job_time == self.job_time]
