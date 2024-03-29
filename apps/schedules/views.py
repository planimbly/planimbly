# Create your views here.
import calendar
import copy
import datetime

import holidays
from django.conf import settings
from django.db.models import Sum
from django.views.generic import TemplateView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

import scripts.run_algorithm
from apps.accounts.models import Employee
from apps.organizations.models import Workplace, Unit, Organization, WorkplaceClosing, Message
from apps.schedules.models import ShiftType, Shift, Schedule, Preference, Absence, Assignment, JobTime, FreeDay, \
    AlgorithmTask
from apps.schedules.serializers import ShiftTypeSerializer, PreferenceSerializer, AbsenceSerializer, \
    AssignmentSerializer, JobTimeSerializer, FreeDaySerializer
from apps.schedules.tasks import run_algorithm
from planimbly.permissions import GroupRequiredMixin, Issupervisor, Isemployee


def free_days(year, month):
    pl_holidays = list(holidays.PL(years=year).keys())
    free_days = list(FreeDay.objects.filter(day__year=year).filter(day__month=month).values_list('day', flat=True))

    pl_holidays = list(filter(lambda x: x.month == month, pl_holidays))
    free_days.extend(pl_holidays)
    return free_days


def convert_to_float(frac_str):
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac


class ShiftTypeManageView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/shiftType_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_org = self.request.user.user_org
        if not Workplace.objects.filter(workplace_unit__unit_org=user_org).exists():
            context['is_any_workplace'] = False
            return context
        units = Unit.objects.filter(unit_org=user_org)
        select_unit = list(units.values(
            'id', 'name'))
        workplace_list = Workplace.objects.filter(workplace_unit__in=units)
        select_workplace = dict()
        for obj in workplace_list:
            select_workplace.setdefault(obj.workplace_unit_id, []).append({"id": obj.id, "name": obj.name})

        context['default_unit'] = select_unit[0]['id']
        context['select_unit'] = select_unit
        context['select_workplace'] = select_workplace
        context['is_any_workplace'] = True
        return context


class JobTimeManageView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/jobtime_manage.html'


class ScheduleGeneratingView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/schedule_generating.html'


class AbsenceManageView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/absence_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['absence_type'] = Absence.ABSENCE_TYPE
        return context


class ScheduleManageView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/schedule_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_org = self.request.user.user_org
        if not Workplace.objects.filter(workplace_unit__unit_org=self.request.user.user_org).exists():
            context['is_any_workplace'] = False
            return context
        units = Unit.objects.filter(unit_org=user_org)
        select_unit = list(units.values(
            'id', 'name'))
        workplace_list = Workplace.objects.filter(workplace_unit__in=units)
        select_workplace = dict()
        for obj in workplace_list:
            select_workplace.setdefault(obj.workplace_unit_id, []).append({"id": obj.id, "name": obj.name})

        context['default_unit'] = select_unit[0]['id']
        context['select_unit'] = select_unit
        context['select_workplace'] = select_workplace
        context['is_any_workplace'] = True
        return context


class EmployeeScheduleView(GroupRequiredMixin, TemplateView):
    template_name = 'schedules/employee_schedule.html'
    group_required = ['employee']


# API VIEWS


class ScheduleCreateApiView(APIView):
    permission_classes = [Issupervisor]

    def post(self, request):
        year = self.request.data.get('year')
        month = self.request.data.get('month')
        workplace_list = self.request.data.get('workplace_list')
        org_id = request.user.user_org_id
        username = request.user.username
        if settings.USE_HUEY:
            run_algorithm(year, month, org_id, workplace_list, username)

        else:
            if not year or not month or not workplace_list:
                return Response(status=status.HTTP_400_BAD_REQUEST)

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

            employee_list = Employee.objects.filter(user_workplace__in=workplace_query).exclude(is_supervisor=True).exclude(
                    groups__name='supervisor').exclude(is_superuser=True).distinct().order_by('id')
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

            response = scripts.run_algorithm.main_algorithm(schedule_dict, employee_list, shiftType_list, year, month,
                                                            emp_for_workplaces, emp_preferences, emp_absences,
                                                            emp_assignments, jobtime, work_for_workplace_closing,
                                                            shifts_before, shifts_after, username)
            if response.get('status'):
                for workplace in workplace_query:
                    old_schedule = Schedule.objects.filter(year=year).filter(month=month).filter(
                        workplace=workplace).first()
                    if old_schedule is not None:
                        old_schedule.delete()
                for schedule in schedule_dict:
                    schedule_dict[schedule].save()
                data = response.get('data')
                for shift in data:
                    shift.save()
            else:
                org = Organization.objects.get(id=org_id)
                message = Message(organization=org, content="Nie udało się wygenerować nowego grafiku",
                                  type='SCHEDULE')
                message.save()
            '''for workplace in workplace_query:
                old_schedule = Schedule.objects.filter(year=year).filter(month=month).filter(
                    workplace=workplace).first()
                if old_schedule is not None:
                    old_schedule.message = "Nie udało się wygenerować nowego grafiku"
                    old_schedule.save()
                else:
                    schedule = schedule_dict[workplace.id]
                    schedule.message = "Nie udało się wygenerować nowego grafiku"
                    schedule.save()'''

        return Response()


class ScheduleReportGetApiView(APIView):
    def get(self, request, unit_pk):
        # 127.0.0.1:8000/schedules/api/1/schedule_report_get?year=2022&month=10
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            employee_list_pk = Shift.objects.filter(schedule__month=month).filter(schedule__year=year).filter(
                schedule__workplace__workplace_unit__pk=unit_pk).values_list('employee_id', flat=True).distinct()
            employee_list = Employee.objects.filter(pk__in=employee_list_pk)
            data = {'employees': {}}
            for employee in employee_list:
                days = {}
                days_num = calendar.monthrange(int(year), int(month))[1]
                for x in range(1, days_num + 1):
                    date = datetime.date(int(year), int(month), x).strftime(date_format)
                    days.update({date: []})
                shifts = Shift.objects.select_related('shift_type__workplace').filter(employee__pk=employee.pk).filter(
                    schedule__workplace__workplace_unit__pk=unit_pk).filter(
                    schedule__month=month).filter(schedule__year=year).order_by('date')
                for shift in shifts:
                    days[shift.date.strftime(date_format)].append((
                        {
                            'id': shift.id,
                            'shift_type_id': shift.shift_type.id,
                            'shift_type_color': shift.shift_type.color,
                            'shift_type_name': shift.shift_type.name,
                            'shift_code': shift.shift_type.shift_code,
                            'workplace_id': shift.shift_type.workplace.id,
                            'workplace_name': shift.shift_type.workplace.name
                        }
                    ))
                first_day = datetime.date(int(year), int(month), 1)
                last_day = datetime.date(int(year), int(month), days_num)
                absences = Absence.objects.filter(employee__pk=employee.pk).filter(start__lte=last_day).filter(
                    end__gte=first_day).values('id', 'start', 'end', 'type')

                data['employees'][employee.pk] = {
                    'employee_id': employee.pk,
                    'employee_login': employee.username,
                    'employee_first_name': employee.first_name,
                    'employee_last_name': employee.last_name,
                    'employee_work_hours': employee.job_time,
                    'days': days,
                    'absences': absences,
                }

            data['free_days'] = free_days(int(year), int(month))

            return Response(data=data)


class ScheduleEmployeeGetApiView(APIView):
    permisson_classes = [Isemployee]

    def get(self, request, employee_pk):
        # 127.0.0.1:8000/schedules/api/3/schedule_employee_get?year=2023&month=1
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:

            days_num = calendar.monthrange(int(year), int(month))[1]
            days = {}
            for x in range(1, days_num + 1):
                date = datetime.date(int(year), int(month), x).strftime(date_format)
                days.update({date: []})
            shifts = Shift.objects.filter(employee_id=employee_pk).filter(schedule__month=month).filter(
                schedule__year=year).order_by('date')

            for shift in shifts:
                days[shift.date.strftime(date_format)].append((
                    {
                        'id': shift.id,
                        'shift_type_id': shift.shift_type.id,
                        'shift_type_color': shift.shift_type.color,
                        'shift_code': shift.shift_type.shift_code,
                        'time_start': shift.shift_type.hour_start,
                        'time_end': shift.shift_type.hour_end,
                        'name': shift.shift_type.name,
                    }
                ))
            data = {'days': days
                    }
            return Response(data=data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ScheduleGetApiView(APIView):
    permission_classes = [Issupervisor]

    def get(self, request, workplace_pk):
        # 127.0.0.1:8000/schedules/api/2/schedule_get?year=2023&month=1
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            workplace = Workplace.objects.get(id=workplace_pk)
            unit = workplace.workplace_unit
            shifts = Shift.objects.select_related('employee').select_related('shift_type').filter(
                schedule__workplace=workplace).filter(schedule__month=month).filter(
                schedule__year=year).order_by('date')
            shifts_statistic = Shift.objects.select_related('employee').select_related('shift_type').filter(
                schedule__workplace__workplace_unit=unit).filter(
                schedule__month=month).filter(schedule__year=year).order_by('employee__order_number',
                                                                            'shift_type__hour_start')
            shifts_types = list(Shift.objects.filter(schedule__workplace__workplace_unit=unit).filter(
                schedule__month=month).filter(schedule__year=year).values_list('shift_type__name',
                                                                               flat=True).distinct())

            days_num = calendar.monthrange(int(year), int(month))[1]
            days = {}
            statistics = {}

            for x in range(1, days_num + 1):
                date = datetime.date(int(year), int(month), x).strftime(date_format)
                days.update({date: []})

            jobtime = JobTime.objects.filter(year=int(year)).values_list(
                calendar.month_name[int(month)].lower(), flat=True).first()
            if jobtime is None:
                jobtime = 160
            for shift in shifts_statistic:
                shift_len = datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_end) - \
                            datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_start)
                statistics.setdefault(shift.employee.id, {
                    'hours': 0,
                    'order_number': shift.employee.order_number,
                    'name': shift.employee.first_name + ' ' + shift.employee.last_name,
                    'jobtime': convert_to_float(shift.employee.job_time) * jobtime,
                    'shift_type': {},
                    'absence': {}
                })
                statistics[shift.employee.id]['hours'] += shift_len.seconds / 3600

                if not statistics[shift.employee.id].get('shift_type'):
                    for shift_type in shifts_types:
                        statistics[shift.employee.id]['shift_type'][shift_type] = 0

                statistics[shift.employee.id]['shift_type'][shift.shift_type.name] += 1

                if Absence.ABSENCE_TYPE[0][0] not in statistics[shift.employee.id]:
                    first_day = datetime.date(int(year), int(month), 1)
                    last_day = datetime.date(int(year), int(month), days_num)
                    for ab_type in Absence.ABSENCE_TYPE:
                        # TODO ZMIENIJSZY LICZBĘ QUERY Z ~30 do 1
                        h_sum = Absence.objects.filter(employee=shift.employee).filter(start__lte=last_day).filter(
                            end__gte=first_day).filter(type=ab_type[0]).aggregate(Sum('hours_number'))[
                            'hours_number__sum']
                        statistics[shift.employee.id][ab_type[0]] = h_sum
            for shift in shifts:
                days[shift.date.strftime(date_format)].append((
                    {
                        'id': shift.id,
                        'shift_type_id': shift.shift_type.id,
                        'shift_type_color': shift.shift_type.color,
                        'shift_code': shift.shift_type.shift_code,
                        'time_start': shift.shift_type.hour_start,
                        'time_end': shift.shift_type.hour_end,
                        'name': shift.shift_type.name,
                        'worker': {
                            'id': shift.employee.id,
                            'first_name': shift.employee.first_name,
                            'last_name': shift.employee.last_name,
                            'order_number': shift.employee.order_number,
                        }
                    }
                ))
            message = Message.objects.filter(organization=request.user.user_org).filter(type='SCHEDULE')
            content = None
            if message.exists() is True:
                content = message.first().content
                message.delete()

            response = {
                'unit_id': workplace.workplace_unit.id,
                'workplace_id': workplace.id,
                'unit_name': workplace.workplace_unit.name,
                'workplace_name': workplace.name,
                'days': days,
                'statistics': statistics,
                'free_days': free_days(int(year), int(month)),
                'jobtime': jobtime,
                'message': content
            }
            return Response(data=response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ScheduleUnitGetApiView(APIView):
    permission_classes = [Issupervisor]

    def get(self, request, unit_pk):
        # 127.0.0.1:8000/schedules/api/1/schedule_unit_get?year=2023&month=1
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            workplace_list = Workplace.objects.filter(workplace_unit_id=unit_pk)
            workplace_list_pk = list(workplace_list.values_list(flat=True))

            shifts = Shift.objects.select_related('employee').select_related('shift_type').select_related(
                'schedule__workplace').filter(schedule__workplace_id__in=workplace_list_pk).filter(
                schedule__month=month).filter(
                schedule__year=year).order_by('date')
            shifts_statistic = Shift.objects.select_related('employee').select_related('shift_type').filter(
                schedule__workplace__workplace_unit_id=unit_pk).filter(
                schedule__month=month).filter(schedule__year=year).order_by('employee__order_number',
                                                                            'shift_type__hour_start')
            shifts_types = list(Shift.objects.filter(schedule__workplace__workplace_unit_id=unit_pk).filter(
                schedule__month=month).filter(schedule__year=year).values_list('shift_type__name',
                                                                               flat=True).distinct())

            days_num = calendar.monthrange(int(year), int(month))[1]

            workplace_days = {}
            statistics = {}

            for workplace in workplace_list:
                workplace_days[workplace.id] = {'days': {}}
                for x in range(1, days_num + 1):
                    date = datetime.date(int(year), int(month), x).strftime(date_format)
                    workplace_days[workplace.id]['days'].update({date: []})

            jobtime = JobTime.objects.filter(year=int(year)).values_list(
                calendar.month_name[int(month)].lower(), flat=True).first()
            if jobtime is None:
                jobtime = 160

            for shift in shifts_statistic:
                shift_len = datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_end) - \
                            datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_start)
                statistics.setdefault(shift.employee.id, {
                    'hours': 0,
                    'order_number': shift.employee.order_number,
                    'name': shift.employee.first_name + ' ' + shift.employee.last_name,
                    'jobtime': convert_to_float(shift.employee.job_time) * jobtime,
                    'shift_type': {},
                    'absence': {}
                })
                statistics[shift.employee.id]['hours'] += shift_len.seconds / 3600

                if not statistics[shift.employee.id].get('shift_type'):
                    for shift_type in shifts_types:
                        statistics[shift.employee.id]['shift_type'][shift_type] = 0

                statistics[shift.employee.id]['shift_type'][shift.shift_type.name] += 1

                if Absence.ABSENCE_TYPE[0][0] not in statistics[shift.employee.id]:
                    first_day = datetime.date(int(year), int(month), 1)
                    last_day = datetime.date(int(year), int(month), days_num)
                    for ab_type in Absence.ABSENCE_TYPE:
                        # TODO ZMIENIJSZY LICZBĘ QUERY Z ~30 do 1
                        h_sum = Absence.objects.filter(employee=shift.employee).filter(start__lte=last_day).filter(
                            end__gte=first_day).filter(type=ab_type[0]).aggregate(Sum('hours_number'))[
                            'hours_number__sum']
                        statistics[shift.employee.id][ab_type[0]] = h_sum

            for shift in shifts:
                workplace_days[shift.schedule.workplace.id]['days'][shift.date.strftime(date_format)].append((
                    {
                        'id': shift.id,
                        'shift_type_id': shift.shift_type.id,
                        'shift_type_color': shift.shift_type.color,
                        'shift_code': shift.shift_type.shift_code,
                        'time_start': shift.shift_type.hour_start,
                        'time_end': shift.shift_type.hour_end,
                        'name': shift.shift_type.name,
                        'worker': {
                            'id': shift.employee.id,
                            'first_name': shift.employee.first_name,
                            'last_name': shift.employee.last_name,
                            'order_number': shift.employee.order_number,
                        }
                    }
                ))
            respone_table = []
            for workplace, value in workplace_days.items():
                workplace_obj = workplace_list.filter(id=workplace).first()
                data = {
                    'unit_id': workplace_obj.workplace_unit.id,
                    'workplace_id': workplace_obj.id,
                    'unit_name': workplace_obj.workplace_unit.name,
                    'workplace_name': workplace_obj.name,
                    'days': value.get('days'),
                    'statistics': statistics,
                    'free_days': free_days(int(year), int(month)),
                    'jobtime': jobtime,
                }
                respone_table.append(
                    {'schedule': data, 'workplace': {'id': workplace_obj.id, 'name': workplace_obj.name},
                     'date': {'month': month, 'year': year}})
            '''response = {
                'unit_id': unit.id,
                # 'workplace_id': workplace.id,
                'unit_name': unit.name,
                # 'workplace_name': workplace.name,
                'workplace_days': workplace_days,
                'statistics': statistics,
                'free_days': free_days(int(year), int(month)),
                'jobtime': jobtime,
            }'''
            return Response(data=respone_table)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ShiftManageApiView(APIView):
    permission_classes = [Issupervisor]

    def post(self, request):
        date = datetime.date.fromisoformat(self.request.data.get("Date"))
        employee = self.request.data.get("Employee")
        shift_type = self.request.data.get("Shift_type")
        workplace = self.request.data.get("Workplace")
        if date and employee and shift_type and workplace:
            schedule = Schedule.objects.filter(year=date.year).filter(month=date.month).filter(
                workplace=workplace).first()
            shift_type = ShiftType.objects.filter(pk=shift_type).first()
            employee = Employee.objects.filter(pk=employee).first()
            if not shift_type or not employee:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if not schedule:
                workplace = Workplace.objects.filter(pk=workplace).first()
                if not workplace:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                schedule = Schedule(year=date.year, month=date.month, workplace=workplace)
                schedule.save()
            Shift(date=date, employee=employee, schedule=schedule, shift_type=shift_type).save()

        return Response()

    def put(self, request):
        employee = self.request.data.get("Employee")
        shift = self.request.data.get("Shift")
        if shift and employee:
            shift = Shift.objects.filter(pk=shift).first()
            employee = Employee.objects.filter(pk=employee).first()
            if not shift or not employee:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shift.employee = employee
            shift.save()
        return Response()

    def delete(self, request):
        shift = self.request.data.get("Shift")
        if shift:
            Shift.objects.filter(pk=shift).delete()
        return Response()


class PreferenceViewSet(viewsets.ModelViewSet):
    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('employee'):
            queryset = Preference.objects.filter(employee_id=request.query_params.get('employee'))
        else:
            queryset = Preference.objects.all()
        serializer = PreferenceSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ShiftTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftTypeSerializer
    permission_classes = [Issupervisor]

    def get_queryset(self):
        queryset = ShiftType.objects.filter(is_archive=False).filter(workplace_id=self.kwargs['workplace_pk'])
        return queryset

    # TODO Zmienić update na działający
    def perform_create(self, serializer):
        v_data = serializer.validated_data
        workplace = Workplace.objects.filter(pk=self.kwargs['workplace_pk']).first()
        shiftType = ShiftType(hour_start=v_data['hour_start'],
                              hour_end=v_data['hour_end'],
                              name=v_data['name'],
                              shift_code=v_data['shift_code'],
                              active_days=v_data['active_days'],
                              demand=v_data['demand'],
                              color=v_data['color'],
                              is_used=v_data['is_used'],
                              workplace=workplace)
        shiftType.save()

    def perform_update(self, serializer):
        v_data = serializer.validated_data
        og_shift_Type = ShiftType.objects.get(pk=self.kwargs['pk'])
        if og_shift_Type.hour_start != v_data['hour_start'] or og_shift_Type.hour_end != v_data['hour_end']:
            new_shift_type = copy.copy(og_shift_Type)
            for attr, value in v_data.items():
                setattr(new_shift_type, attr, value)
            new_shift_type.pk = None
            new_shift_type.save()
            og_shift_Type.is_archive = True
            og_shift_Type.save()
        else:
            for attr, value in v_data.items():
                setattr(og_shift_Type, attr, value)
            og_shift_Type.save()

    def perform_destroy(self, instance):
        instance.is_archive = True
        instance.save()


class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('employee'):
            queryset = Absence.objects.filter(employee_id=request.query_params.get('employee'))
        else:
            queryset = Absence.objects.all()
        queryset = queryset.filter(employee__user_org_id=request.user.user_org_id)
        serializer = AbsenceSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('employee'):
            queryset = Assignment.objects.filter(employee_id=request.query_params.get('employee'))
        else:
            queryset = Assignment.objects.all()
        serializer = AssignmentSerializer(queryset, many=True)
        return Response(serializer.data)


class JobTimeViewSet(viewsets.ModelViewSet):
    queryset = JobTime.objects.all()
    serializer_class = JobTimeSerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('year'):
            queryset = JobTime.objects.filter(year=int(request.query_params.get('year'))).filter(
                organization_id=request.user.user_org_id)
        else:
            queryset = JobTime.objects.filter(organization_id=request.user.user_org_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        organization = Organization.objects.get(pk=self.request.user.user_org_id)
        jobtime = JobTime(organization=organization, year=v_data.get('year'), january=v_data.get('january'),
                          february=v_data.get('february'), march=v_data.get('march'),
                          april=v_data.get('april'), may=v_data.get('may'), june=v_data.get('june'),
                          july=v_data.get('july'), august=v_data.get('august'), september=v_data.get('september'),
                          october=v_data.get('october'), november=v_data.get('november'),
                          december=v_data.get('december'))
        jobtime.save()


class FreeDayViewSet(viewsets.ModelViewSet):
    queryset = FreeDay.objects.all()
    serializer_class = FreeDaySerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('year'):
            queryset = FreeDay.objects.filter(day__year=int(request.query_params.get('year'))).filter(
                organization_id=request.user.user_org_id)
        else:
            queryset = FreeDay.objects.filter(organization_id=request.user.user_org_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        organization = Organization.objects.get(pk=self.request.user.user_org_id)
        freeday = FreeDay(organization=organization, name=v_data.get('name'), day=v_data.get('day'))
        freeday.save()


class CheckAlgorithmView(APIView):

    def get(self, request):
        a_task = AlgorithmTask.objects.filter(organization_id=request.user.user_org_id).exists()
        task_status = False
        if a_task:
            task_status = True
        return Response(status=status.HTTP_200_OK, data={'task_status': task_status})
