import calendar
import datetime
from django.test import TestCase
from django.core.management import call_command

from scripts.context import Context, ShiftTypeInfo, EmployeeInfo
from scripts.run_algorithm import main_algorithm
from ..accounts.models import Employee
from ..organizations.models import Workplace, WorkplaceClosing
from .models import ShiftType, Preference, Absence, Assignment, Schedule, JobTime, Shift


def run_algorithm_test(year, month, org_id, workplace_list, username):
    workplace_query = Workplace.objects.filter(id__in=workplace_list)
    schedule_dict = dict()

    for workplace in workplace_query:
        schedule = Schedule(year=year, month=month,
                            workplace=workplace)
        # schedule.save()
        schedule_dict.setdefault(workplace.id, schedule)

    shiftType_list = list(
        ShiftType.objects.filter(workplace_id__in=workplace_list).filter(is_used=True).filter(is_archive=False))

    emp_for_workplaces = {}

    for work_id in workplace_list:
        emp_for_workplaces[work_id] = Employee.objects.filter(
            user_workplace__in=Workplace.objects.filter(id__in=[work_id])).exclude(is_supervisor=True).exclude(
            groups__name='supervisor').exclude(is_superuser=True).distinct().order_by('id')

    employee_list = Employee.objects.filter(user_workplace__in=workplace_query).distinct().order_by('id').exclude(is_supervisor=True)
    preferences = Preference.objects.filter(employee__in=employee_list)

    # Sprawdzamy pierwszą datę w miesiącu i ostatnią
    first_day = datetime.date(int(year), int(month), 1)
    last_day = datetime.date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])

    absences = Absence.objects.filter(employee__in=employee_list).filter(start__lte=last_day).filter(
        end__gte=first_day)
    emp_preferences = {}
    for preference in preferences:
        emp_preferences.setdefault(preference.employee.id, []).append(preference)

    emp_absences = {}
    for absence in absences:
        emp_absences.setdefault(absence.employee.id, []).append(absence)

    term_assignments = Assignment.objects.filter(employee__in=employee_list).filter(start__lte=last_day).filter(
        end__gte=first_day)
    general_assignments = Assignment.objects.filter(employee__in=employee_list).filter(start=None).filter(
        end=None)

    emp_assignments = {}
    for assignment in term_assignments:
        emp_assignments.setdefault(assignment.employee.id, []).append(assignment)

    for assignment in general_assignments:
        emp_assignments.setdefault(assignment.employee.id, []).append(assignment)

    work_for_workplace_closing = {}
    for work_id in workplace_list:
        work_for_workplace_closing[work_id] = WorkplaceClosing.objects.filter(start__lte=last_day).filter(
            end__gte=first_day).filter(workplace_id=work_id)

    jobtime = JobTime.objects.filter(year=int(year)).values_list(calendar.month_name[month].lower(),
                                                                 flat=True).first()

    seven_before = first_day - datetime.timedelta(days=7)
    seven_after = last_day + datetime.timedelta(days=7)

    shifts_before = {}
    shifts_after = {}

    shifts_b = Shift.objects.filter(date__gte=seven_before).filter(date__lt=first_day).filter(
        schedule__workplace_id__in=workplace_list).order_by('date')
    shifts_a = Shift.objects.filter(date__gt=last_day).filter(date__lte=seven_after).filter(
        schedule__workplace_id__in=workplace_list).order_by('date')

    for shift in shifts_b:
        shifts_before.setdefault(shift.date, []).append(shift)
    for shift in shifts_a:
        shifts_after.setdefault(shift.date, []).append(shift)

    response = main_algorithm(schedule_dict, employee_list, shiftType_list, year, month,
                              emp_for_workplaces, emp_preferences, emp_absences,
                              emp_assignments, jobtime, work_for_workplace_closing,
                              shifts_before, shifts_after, username)

    return response


def create_emp_info(user, workplace_list, jobtime):
    emp_for_workplaces = {}
    for work_id in workplace_list:
        emp_for_workplaces[work_id] = Employee.objects.filter(
            user_workplace__in=Workplace.objects.filter(id__in=[work_id])).exclude(is_supervisor=True).exclude(
            groups__name='supervisor').exclude(is_superuser=True).distinct().order_by('id')

    return EmployeeInfo(emp=user,
                        wp=[wp for wp in emp_for_workplaces if user in emp_for_workplaces[wp]],
                        pref=Preference.objects.filter(employee=user.pk),
                        ab=Absence.objects.filter(employee=user.pk),
                        ass=Assignment.objects.filter(employee=user.pk),
                        jt=168)


def create_context(unit, workplace_list, year, month, jobtime):
    first_day = datetime.date(int(year), int(month), 1)
    last_day = datetime.date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])

    work_for_workplace_closing = {}
    for work_id in workplace_list:
        work_for_workplace_closing[work_id] = WorkplaceClosing.objects.filter(start__lte=last_day).filter(
            end__gte=first_day).filter(workplace_id=work_id)

    emp_info = []
    for user in Employee.objects.filter(user_unit=1):
        emp_info.append(create_emp_info(user=user, workplace_list=workplace_list, jobtime=jobtime))

    shiftType_list = list(
        ShiftType.objects.filter(workplace_id__in=workplace_list).filter(is_used=True).filter(is_archive=False))

    return Context(emp_info, shiftType_list, year=year, month=month, jt=jobtime, work_for_workplace_closing=work_for_workplace_closing)


class algorithm_components_test_case(TestCase):
    fixtures = ['database_component.json']

    def setUp(self):
        call_command('create_groups')

    def test_data(self):
        user = Employee.objects.get(username='jandob12')
        self.assertEqual(user.username, 'jandob12')

    def test_shift_type_info(self):
        st = ShiftType.objects.get(name='M', workplace=1)
        sti = ShiftTypeInfo(st=st, index=1)

        self.assertEqual(sti.get_duration_in_hours(), 8)
        self.assertEqual(sti.get_duration_in_minutes(), 480)

    def test_employee_info(self):
        user = Employee.objects.get(username='jandob12')
        emp_info = create_emp_info(user=user, workplace_list=[1, 2], jobtime=168)

        self.assertEqual(emp_info.get(), user)
        self.assertEqual(emp_info.get_absent_days_in_month(12, 2022), [30, 31])
        self.assertNotEqual(emp_info.calculate_job_time(168), 84)
        user.job_time = '1/2'
        self.assertEqual(emp_info.calculate_job_time(168), 84)

    def test_context(self):
        ctx = create_context(unit=1, workplace_list=[1, 2], year=2022, month=12, jobtime=168)

        self.assertEqual(ctx.calculate_total_work_time(), 688)
        self.assertEqual(ctx.calculate_max_work_time(), 3856)
        self.assertGreaterEqual(ctx.calculate_max_work_time(), ctx.calculate_total_work_time())
        self.assertEqual(ctx.get_shift_info_by_id(1).shift_type,
                         ShiftType.objects.get(name='M', workplace=1))
        self.assertEqual(ctx.get_employee_by_id(3).employee,
                         Employee.objects.get(pk='3'))


class algorithm_test_case_optimal(TestCase):
    fixtures = ['database_optimal.json']

    def setUp(self):
        call_command('create_groups')

    def test_main_algorithm(self):
        response = run_algorithm_test(year=2022, month=12, org_id=1, workplace_list=[1, 2], username='admin')

        self.assertEqual(response['status_full'], 'OPTIMAL')


class algorithm_test_case_infeasible(TestCase):
    fixtures = ['database_infeasible.json']

    def setUp(self):
        call_command('create_groups')

    def test_main_algorithm(self):
        response = run_algorithm_test(year=2022, month=12, org_id=1, workplace_list=[1, 2], username='admin')

        self.assertEqual(response['status_full'], 'INFEASIBLE')
