import calendar
import datetime
from django.test import TestCase
from django.core.management import call_command

from .link_scripts.context import Context, ShiftTypeInfo, EmployeeInfo
from ..accounts.models import Employee
from ..organizations.models import Workplace, WorkplaceClosing
from .models import ShiftType, Preference, Absence, Assignment


class algorithm_test_case(TestCase):
    fixtures = ['database_ver1.json']

    def setUp(self):
        call_command('create_groups')

    def create_emp_info(self, user, workplace_list, jobtime):
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

    def create_context(self, unit, workplace_list, year, month, jobtime):
        first_day = datetime.date(int(year), int(month), 1)
        last_day = datetime.date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])

        work_for_workplace_closing = {}
        for work_id in workplace_list:
            work_for_workplace_closing[work_id] = WorkplaceClosing.objects.filter(start__lte=last_day).filter(
                end__gte=first_day).filter(workplace_id=work_id)

        emp_info = []
        for user in Employee.objects.filter(user_unit=1):
            emp_info.append(self.create_emp_info(user=user, workplace_list=workplace_list, jobtime=jobtime))

        shiftType_list = list(
            ShiftType.objects.filter(workplace_id__in=workplace_list).filter(is_used=True).filter(is_archive=False))

        return Context(emp_info, shiftType_list, year=year, month=month, jt=jobtime, work_for_workplace_closing=work_for_workplace_closing)

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
        emp_info = self.create_emp_info(user=user, workplace_list=[1, 2], jobtime=168)

        self.assertEqual(emp_info.get(), user)
        self.assertEqual(emp_info.get_absent_days_in_month(12, 2022), [30, 31])
        self.assertNotEqual(emp_info.calculate_job_time(168), 84)
        user.job_time = '1/2'
        self.assertEqual(emp_info.calculate_job_time(168), 84)

    def test_context(self):
        ctx = self.create_context(unit=1, workplace_list=[1, 2], year=2022, month=12, jobtime=168)

        self.assertEqual(ctx.calculate_total_work_time(), 688)
        self.assertEqual(ctx.calculate_max_work_time(), 3856)
        self.assertGreaterEqual(ctx.calculate_max_work_time(), ctx.calculate_total_work_time())
        self.assertEqual(ctx.get_shift_info_by_id(1).shift_type,
                         ShiftType.objects.get(name='M', workplace=1))
        self.assertEqual(ctx.get_employee_by_id(3).employee,
                         Employee.objects.get(pk='3'))
