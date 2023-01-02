from datetime import date, datetime as dt, timedelta

from loguru import logger

from apps.accounts.models import Employee
from apps.schedules.models import ShiftType
from scripts.helpers import get_month_by_weeks, get_month_by_billing_weeks, get_letter_for_weekday


class ShiftTypeInfo:
    """
    A class used to keep enhanced information about shifts.

    Attributes:
    -------
    shift_type : ShiftType
        Variable to keep certain ShiftType object (shift).
    duration : int
        The number representing shift durations in minutes.
    id = int
        Shift's id.
    closings : list
        The list of WorkplaceClosing objects containing information about closed days for certain shift.
    closing_days : list
        The list containing days, when workplace is closed and shift unused.

    Methods:
    -------
    get_duration_in_minutes
        Returns shift duration in minutes.
    get_duration_in_hours
        Calculates shift duration in hours.
    prepare_closing_days
        Turns WorkplaceClosing objects into the list of days when shift is unused.
    get_closing_days_in_month
        Fetches all days in certain month, when shift is unused.
    get
        Simple function to quickly get ShiftType object from ShiftTypeInfo object.
    """

    shift_type = ShiftType
    duration = int()
    id = int()

    closings = list()
    closing_days = list()

    def __init__(self, st: ShiftType, index: int()) -> None:
        self.shift_type = st
        self.id = index
        self.duration = (dt.combine(date.min, self.shift_type.hour_end) - dt.combine(date.min, self.shift_type.hour_start)).seconds // 60

        logger.log("ADDED", self)

    def get_duration_in_minutes(self) -> int:
        """ Returns shift duration in minutes.

        Returns:
            int number of minutes representing shift duration.
        """
        return self.duration

    def get_duration_in_hours(self) -> int:
        """ Calculates shift duration in hours.

        Returns:
            int number of hours representing shift duration.
        """
        return self.duration // 60

    def prepare_closing_days(self) -> list:
        """ Turns WorkplaceClosing objects into the list of days when shift is unused.

        Returns:
            list of days when shift is unused.
        """

        logger.trace("Preparing closing days started...")

        cd = []

        for cl in self.closings:
            for i in range((cl.end - cl.start).days + 1):
                inter_date = cl.start + timedelta(days=i)
                cd.append(inter_date)
                logger.log("ADDED", "[CLOSING] SHIFT: {:2d} | DAY: {:2d}".format(self.id, inter_date.day))

        logger.trace("Preparing closing days ended.")

        return cd

    def get_closing_days_in_month(self, month: int, year: int) -> list:
        """ Fetches all days in certain month, when shift is unused.

        Returns:
            list of days, when shift is unused.
        """
        return [d.day for d in self.closing_days if d.month == month and d.year == year]

    def get(self) -> ShiftType:
        """Simple function to quickly get ShiftType object from ShiftTypeInfo object.

        Returns:
            ShiftType object from given ShiftTypeInfo object.
        """
        return self.shift_type

    def __str__(self) -> str:
        return "[SHIFT] ID: {:2d} | {} | {} | DURATION (h): {:.1f} | DEMAND: {:d}".format(
            self.id, self.shift_type.workplace, self.shift_type.name, self.get_duration_in_hours(), self.shift_type.demand)


class EmployeeInfo:
    """
        # TODO: docstrings here
    """
    # Bases: employee and his/her workplaces
    employee = Employee
    workplaces = []

    # Preferences and assignments
    preferences = []
    assignments = []
    term_assignments = []
    negative_indefinite_assignments = []
    positive_indefinite_assignments = []

    # Absences (objects, separated days, time)
    absences = []
    absent_days = []
    absent_time = 0

    # Job time and maximum work time
    desired_job_time = 0
    job_time = 0
    max_work_time = 0

    # Constraint helpers
    allowed_shift_types = {}  # Key: Shift_type object, Value: list of allowed days
    weekly_constraints = []
    work_time_constraint = [0, 0, 0, 0, 0, 0]  # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)

    def __init__(self, emp: Employee, wp: list, pref: list, ab: list, ass: list, jt: int):
        # Preparing bases - employee and workplaces
        self.employee = emp
        self.workplaces = wp

        # Preparing preferences and assignments
        self.preferences = pref
        self.assignments = ass
        self.term_assignments, self.negative_indefinite_assignments, self.positive_indefinite_assignments = self.prepare_assignments()
        if len(self.negative_indefinite_assignments) > 0 and len(self.positive_indefinite_assignments) > 0:
            logger.warning("[WARNING] Both negative and positive indefinite assignments found for employee {:d}".format(self.get().pk))

        # Preparing and modelling absences
        self.absences = ab
        self.absent_days, self.absent_time = self.prepare_absent_days()

        # Calculating and correcting job time
        self.desired_job_time = self.calculate_job_time(jt)
        self.job_time = self.desired_job_time - self.absent_time

        # Logging data
        self.log_employeeinfo_data()

    def calculate_job_time(self, jt) -> int:
        match self.employee.job_time:
            case '1':
                return jt
            case '1/2':
                return jt // 2
            case '1/4':
                return jt // 4
            case '3/4':
                return jt * 3 // 4
            case _:
                logger.warning("Something is wrong with calculating job time for employee {}".format(self.employee.pk))
                return jt

    def prepare_assignments(self):
        ta = []
        nia = []
        pia = []

        for a in self.assignments:
            if a.end is not None and a.start is not None:
                # term assignments
                for i in range((a.end - a.start).days + 1):
                    inter_date = a.start + timedelta(days=i)
                    ta.append((a.shift_type, a.negative_flag, inter_date))
                    logger.log("ADDED", "[ASSIGNMENT] EMP: {:2d} | DAY: {:2d} | ST: {:d} | TYPE: {}".format(
                        a.employee.pk, inter_date.day, a.shift_type.id, "neg" if a.negative_flag else "pos"))
            else:
                # indefinite_assignments
                if a.negative_flag:
                    nia.append(a.shift_type)
                else:
                    pia.append(a.shift_type)
                logger.log("ADDED", "[ASSIGNMENT] EMP: {:2d} | ST: {:d} | TYPE: {}".format(
                    a.employee.pk, a.shift_type.id, "neg" if a.negative_flag else "pos"))

        return ta, nia, pia

    def prepare_absent_days(self) -> (list, int):
        ad = []
        at = 0

        for ab in self.absences:
            at += ab.hours_number
            for i in range((ab.end - ab.start).days + 1):
                inter_date = ab.start + timedelta(days=i)
                ad.append(inter_date)
                logger.log("ADDED", "[ABSENCE] EMP: {:2d} | DAY: {:2d}".format(ab.employee.pk, inter_date.day))

        return ad, at

    def get_absent_days_in_month(self, month: int, year: int) -> list:
        """ Returns days on which given employee is absent """
        return [d.day for d in self.absent_days if d.month == month and d.year == year]

    def get(self) -> Employee:
        return self.employee

    def __str__(self) -> str:
        return "[EMPLOYEE] ID: {:2d} | JT: {:3d} | {} {}".format(self.employee.pk, self.job_time, self.employee.first_name, self.employee.last_name)

    def log_employeeinfo_data(self) -> None:
        logger.log("ADDED", self)
        logger.debug("Workplaces: {}".format(self.workplaces))

        if len(self.preferences) > 0:
            logger.debug("Preferences: {}".format(self.preferences))
        else:
            logger.debug("No preferences!")

        if len(self.term_assignments) > 0:
            logger.debug("Term assignments: {}".format(self.term_assignments))
        else:
            logger.debug("No term assignments")

        if len(self.positive_indefinite_assignments) > 0:
            logger.debug("Positive indefinite assignments: {}".format(self.positive_indefinite_assignments))
        else:
            logger.debug("No positive indefinite assignments")

        if len(self.negative_indefinite_assignments) > 0:
            logger.debug("Negative indefinite assignments: {}".format(self.negative_indefinite_assignments))
        else:
            logger.debug("No negative indefinite assignments")

        if len(self.absences) > 0:
            logger.debug("Absences: {}".format(["{} - {}".format(str(e.start), str(e.end)) for e in self.absences]))
        else:
            logger.debug("No absences")


class Context:
    """
    A class used to keep some bases for algorithm.

    Attributes:
    -------
    employees : list[EmployeeInfo]
        The list containing EmployeeInfo objects with all considered employees
    shift_types : list[ShiftType]
        The list containing ShiftType objects with all considered shifts
    month : int
        The month we generate schedule for.
    year : int
        The year for the month.
    month_by_weeks : list
        The list of list. Primary lists represents month. Sub-lists represent weeks. Elements are tuples (day number, weekday number).
    month_by_billing_weeks : list
        The same stuff as month_by_weeks, however weeks are days 1-7, 8-14, etc..
    weekends : list
        The list containing lists of all adjacent Saturdays and Sundays for given month.
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
    get_employee_by_id
        Returns EmployeeInfo object of given id.
    get_full_time_employees
        Filters employees and gets a list of full time employees.
    """

    # Bases: shifts and employees
    employees = []
    shift_types = []

    # Timing and billing variables
    month = 0
    year = 0
    month_by_weeks = []
    month_by_billing_weeks = []
    weekends = []

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
    ft_job_time = int
    rest_job_time = int

    # Multipliers
    job_time_multiplier = float
    overtime_multiplier = float
    overtime_for_full_timers = bool
    overtime_above_full_time = int

    def __init__(self, emp: list[EmployeeInfo], st: list[ShiftType], year: int, month: int, jt: int, work_for_workplace_closing: dict) -> None:
        """
        Args:
            emp: list of EmployeeInfo objects containing information about employees,
            st - list of ShiftType objects containing information about shifts,
            year - considered year passed from main function,
            month - considered month passed from main function,
            jt - full-time job worktime for given month,
        """

        # Preparing bases: shifts and employees
        self.employees = emp
        self.shift_types = [ShiftTypeInfo(s, s.pk) for s in st]

        # Preparing timing and billing stuff
        self.month = month
        self.year = year
        self.month_by_weeks = get_month_by_weeks(year, month)
        self.month_by_billing_weeks = get_month_by_billing_weeks(year, month)
        self.weekends = [x[-2:] for x in self.month_by_weeks if len(x) == 7]
        self.job_time = jt

        # Searching for illegal transitions and overnight shifts
        self.illegal_transitions = self.find_illegal_transitions()
        self.overnight_shifts = self.find_overnight_shifts()

        for s in self.shift_types:
            if s.get().workplace.id not in work_for_workplace_closing:
                s.closings = []
            else:
                s.closings = work_for_workplace_closing[s.get().workplace.id]
                s.closing_days = s.prepare_closing_days()
                s.get_closing_days_in_month(month, year)

        # Calculating worktime and job time stuff
        self.total_work_time = self.calculate_total_work_time()
        self.ft_job_time = sum(ei.job_time for ei in self.get_full_time_employees())

        # if self.total_work_time < self.ft_job_time:
        #     self.employees = [ei for ei in self.employees if self.job_time == ei.desired_job_time]

        self.total_job_time = sum(ei.job_time for ei in self.employees)
        self.max_work_time = self.calculate_max_work_time()

        self.rest_job_time = self.total_job_time - self.ft_job_time

        # Calculating multipliers
        self.employees = sorted(self.employees, key=lambda e: e.max_work_time)
        self.job_time_multiplier = self.total_work_time / self.total_job_time

        if len(self.get_full_time_employees()) == 0:
            logger.debug("There are no full time employees!")
        elif len(self.employees) == len(self.get_full_time_employees()):
            self.overtime_multiplier = 1
        else:
            self.overtime_multiplier = (self.total_work_time - sum(ei.job_time for ei in self.get_full_time_employees())) \
                                   / (self.total_job_time - sum(ei.job_time for ei in self.get_full_time_employees()))

        # Check if there will be overtime for full time workers
        self.overtime_for_full_timers = sum(min(self.job_time, ei.max_work_time) for ei in self.employees) < self.total_work_time

        # Calculate total overtime above monthly job time
        self.overtime_above_full_time = self.total_work_time - sum(min(self.job_time, ei.max_work_time) for ei in self.employees)

        # Preparing requests and absences
        self.requests = self.prepare_requests()
        self.fixed_assignments = self.prepare_fixed_assignments()

        self.log_context_data()

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
                    logger.debug("Found illegal transition: {} to {}".format(i.get().name, j.get().name))
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
                logger.debug("Found overnight shift: {}".format(i.get().name))
                # Between 2 and 3 consecutive days of night shifts, 1 and 4 are possible but penalized.
                sc.append((i.get().id, 1, 2, 20, 3, 4, 5))
                # At least 1 night shift per week (penalized). At most 4 (hard).
                # nahh
                # wsc.append((i.get().id, 0, 1, 2, 3, 4, 0))

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

    def get_employee_by_id(self, index: int) -> EmployeeInfo:
        """ Simple function to quickly get EmployeeInfo object from shift id.

        Args:
            index: given employee id
        Returns:
            wanted EmployeeInfo object
        """

        return next(x for x in self.employees if x.get().pk == index)

    def calculate_total_work_time(self) -> int:
        """ Calculates total work time during month (IN HOURS!), based on cover demands.

            Returns:
                number of hours to share among employees during month.
        """

        logger.trace("Calculating total work time started...")

        total_minutes = 0

        for s in self.shift_types[1:]:
            for week in self.month_by_billing_weeks:
                for d in week:
                    if d[0] in s.get_closing_days_in_month(self.month, self.year):
                        continue
                    total_minutes += s.duration * s.get().demand

        logger.trace("Calculating total work time ended.")

        return total_minutes // 60

    # TODO: Consider weekend constraints and every other constraint regarding free shifts here, for now we only account for absences
    def calculate_max_work_time(self):
        """ Calculates maximum allowed work time for each employee

        Returns:
            sum of all employees maximum allowed work time
        """

        logger.trace("Calculating max allowed work time started...")

        mwt = 0

        for ei in self.employees:
            for week in get_month_by_billing_weeks(self.year, self.month):
                num_absences = sum(x in ei.get_absent_days_in_month(self.month, self.year) for x in [d[0] for d in week])
                max_week_work_time = 8 * len(week)
                if num_absences > 1:
                    max_week_work_time -= num_absences * 8
                elif len(week) > 3:
                    max_week_work_time -= 8  # Minimum one free shift per 7-day week by default
                ei.max_work_time += max(max_week_work_time, 0)
            logger.info("Max work time for employee {}: {}h".format(ei.get().pk, ei.max_work_time))
            mwt += ei.max_work_time

        logger.trace("Calculating max allowed work time ended.")

        return mwt

    def prepare_requests(self) -> list:
        """ Fetches employees requests and prepares them to be used later.

        Returns:
            list of employees requests prepared to be added to model in run_algorithm.py.
        """

        req = []

        for ei in self.employees:
            for pref in ei.preferences:
                for week in self.month_by_billing_weeks:
                    for d in week:
                        if pref.active_days[d[1]] == "1":
                            req.append((ei.employee.pk, next(st.get().id for st in self.shift_types if pref.shift_type == st.get()), d[0], -1))
                            logger.log("ADDED", "[PREFERENCE] EMP: {:2d} | SHIFT: {} | DAY: {:2d} ({}) | WEIGHT: {:d}".format(
                                ei.employee.pk, next(st.get().name for st in self.shift_types if pref.shift_type == st.get()),
                                d[0], get_letter_for_weekday(d[1]), -1))

        return req

    def prepare_fixed_assignments(self) -> list:
        """ Prepares absent days for each employee to be added to fixed assignments.

        Returns:
            list of absences prepared to be added to fixed assignments.
        """

        fa = []

        for ei in self.employees:
            for d in ei.get_absent_days_in_month(self.month, self.year):
                fa.append((ei.employee.pk, 0, d))

        return fa

    def get_full_time_employees(self) -> list:
        """Filters employees and gets a list of full time employees.

        Returns:
            list of full time employees or empty list if there are no full time employees.
        """

        return [ei for ei in self.employees if ei.desired_job_time == self.job_time]

    def log_context_data(self):
        if not self.employees:
            logger.critical("NO EMPLOYEES!")
        else:
            logger.debug("Employees: {}".format(self.employees))

        if len(self.shift_types) <= 1:  # 1 not 0, because when comparing to 0 it doesn't work - we have a free shift!
            logger.critical("NO SHIFTS!")
        else:
            logger.debug("Shifts: {}".format(self.shift_types))

        logger.debug("Given month: {}".format(self.month))
        logger.debug("Given year: {}".format(self.year))

        logger.debug("Month separated into weeks: {}".format(self.month_by_weeks))
        logger.debug("Month separated into billing weeks: {}".format(self.month_by_billing_weeks))

        logger.debug("Given job time for month: {}".format(self.job_time))

        if self.requests:
            logger.debug("Returned requests {}.".format(self.requests))
        else:
            logger.debug("There are no employees requests")

        if self.fixed_assignments:
            logger.debug("Returned absences {}.".format(self.fixed_assignments))
        else:
            logger.debug("There are no employees absences")

        if self.illegal_transitions:
            logger.debug("Returned illegal transitions {}.".format(self.illegal_transitions))
        else:
            logger.debug("No illegal transitions")

        if self.overnight_shifts:
            logger.debug("Found overnight shifts: {}.".format([s[0] for s in self.overnight_shifts[0]]))
        else:
            logger.debug("No overnight shifts")

        logger.trace("Calculated total worktime: {}".format(self.total_work_time))
        logger.trace("Calculated total job time: {}".format(self.total_job_time))
        logger.trace("Calculated maximum worktime: {}".format(self.max_work_time))

        logger.trace("Calculated job time multiplier: {}".format(self.job_time_multiplier))
        logger.trace("Calculated overtime multiplier {}; for full-timers {}, above full-time {}.".format(
            self.overtime_multiplier, self.overtime_for_full_timers, self.overtime_above_full_time))

        if self.overtime_for_full_timers:
            logger.warning("There might be overtime for full time workers!")
