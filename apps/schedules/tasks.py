import calendar
import datetime

from huey import signals
from huey.contrib import djhuey as huey
from huey.contrib.djhuey import db_task

import scripts.run_algorithm
from apps.accounts.models import Employee
from apps.organizations.models import Workplace, WorkplaceClosing
from apps.schedules.models import ShiftType, Schedule, Preference, Absence, Assignment, JobTime, AlgorithmTask, Shift


@db_task()
def run_algorithm(year, month, user_id, workplace_list):

    workplace_query = Workplace.objects.filter(id__in=workplace_list)
    schedule_dict = dict()
    # Sprawdzamy czy istnieją już jakieś grafiki, jeżeli tak usuwamy wszystkie
    for workplace in workplace_query:
        old_schedule = Schedule.objects.filter(year=year).filter(month=month).filter(workplace=workplace).first()
        if old_schedule is not None:
            old_schedule.delete()
        schedule = Schedule(year=year, month=month,
                            workplace=workplace)
        schedule.save()
        schedule_dict.setdefault(workplace.id, schedule)

    shiftType_list = list(ShiftType.objects.filter(workplace_id__in=workplace_list).filter(is_used=True))

    emp_for_workplaces = {}

    for work_id in workplace_list:
        emp_for_workplaces[work_id] = Employee.objects.filter(
            user_workplace__in=Workplace.objects.filter(id__in=[work_id])).distinct().order_by('id')

    employee_list = Employee.objects.filter(user_workplace__in=workplace_query).distinct().order_by('id')
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
    general_assignments = Assignment.objects.filter(employee__in=employee_list).filter(start=None).filter(end=None)

    emp_assignments = {}
    for assignment in term_assignments:
        emp_assignments.setdefault(assignment.employee.id, []).append(assignment)

    for assignment in general_assignments:
        emp_assignments.setdefault(assignment.employee.id, []).append(assignment)

    work_for_workplace_closing = {}
    for work_id in workplace_list:
        work_for_workplace_closing[work_id] = WorkplaceClosing.objects.filter(start__lte=last_day).filter(
            end__gte=first_day).filter(workplace_id=work_id)
    jobtime = JobTime.objects.filter(year=int(year)).values_list(calendar.month_name[month].lower(), flat=True).first()

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

    data = scripts.run_algorithm.main_algorithm(schedule_dict, employee_list, shiftType_list, year, month,
                                                emp_for_workplaces, emp_preferences, emp_absences,
                                                emp_assignments, jobtime, work_for_workplace_closing,
                                                shifts_before, shifts_after)
    for shift in data['data']:
        shift.save()
    return


@huey.signal(signals.SIGNAL_ERROR, signals.SIGNAL_COMPLETE, signals.SIGNAL_CANCELED)
def task_ended_handler(signal, task, exc=None):
    user_org_id = Employee.objects.get(pk=task.args[2]).user_org_id
    a_task = AlgorithmTask.objects.get(organization_id=user_org_id, process_pid=task.id)
    if a_task:
        a_task.delete()


@huey.signal(signals.SIGNAL_EXECUTING)
def task_ended(signal, task):
    user_org_id = Employee.objects.get(pk=task.args[2]).user_org_id
    a_task = AlgorithmTask(organization_id=user_org_id, process_pid=task.id)
    a_task.save()
