# Create your views here.
import calendar
import datetime

import holidays
from django.db.models import Sum
from django.views.generic import TemplateView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import scripts.run_algorithm
from apps.accounts.models import Employee
from apps.organizations.models import Workplace, Unit
from apps.schedules.models import ShiftType, Shift, Schedule, Preference, Absence, Assignment, JobTime
from apps.schedules.serializers import ShiftTypeSerializer, PreferenceSerializer, AbsenceSerializer, \
    AssignmentSerializer, JobTimeSerializer


class ShiftTypeManageView(TemplateView):
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


class JobTimeManageView(TemplateView):
    template_name = 'schedules/jobtime_manage.html'


class AbsenceManageView(TemplateView):
    template_name = 'schedules/absence_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['absence_type'] = Absence.ABSENCE_TYPE
        return context


class ScheduleManageView(TemplateView):
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


# API VIEWS
class ScheduleCreateApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        year = self.request.data.get('year')
        month = self.request.data.get('month')
        workplace_list = self.request.data.get('workplace_list')
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

        time_assignments = Assignment.objects.filter(employee__in=employee_list).filter(start__lte=last_day).filter(
            end__gte=first_day)
        all_assignments = Assignment.objects.filter(employee__in=employee_list).filter(start=None).filter(end=None)
        emp_assignments = {}
        for assignment in time_assignments:
            emp_assignments.setdefault(assignment.employee.id, []).append(assignment)
        for assignment in time_assignments:
            emp_assignments.setdefault(assignment.employee.id, []).append(all_assignments)

        data = scripts.run_algorithm.main_algorithm(schedule_dict, employee_list, shiftType_list, year, month,
                                                    emp_for_workplaces, emp_preferences, emp_absences, emp_assignments)
        for shift in data:
            shift.save()
        return Response()


class ScheduleReportGetApiView(APIView):
    def get(self, request, unit_pk):
        # 127.0.0.1:8000/schedules/api/1/schedule_report_get?year=2022&month=10
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            employee_list = Employee.objects.filter(user_unit__pk=unit_pk).distinct()
            data = {}
            for employee in employee_list:
                days = {}
                days_num = calendar.monthrange(int(year), int(month))[1]
                for x in range(1, days_num + 1):
                    date = datetime.date(int(year), int(month), x).strftime(date_format)
                    days.update({date: []})
                shifts = Shift.objects.filter(employee__pk=employee.pk).filter(
                    schedule__workplace__workplace_unit__pk=unit_pk).filter(
                    schedule__month=month).filter(schedule__year=year).order_by('date')
                for shift in shifts:
                    days[shift.date.strftime(date_format)].append((
                        {
                            'id': shift.id,
                            'shift_type_id': shift.shift_type.id,
                            'shift_type_color': shift.shift_type.color,
                            'shift_type_name': shift.shift_type.name,
                            'workplace_id': shift.shift_type.workplace.id,
                            'workplace_name': shift.shift_type.workplace.name
                        }
                    ))
                first_day = datetime.date(int(year), int(month), 1)
                last_day = datetime.date(int(year), int(month), days_num)
                absences = Absence.objects.filter(employee__pk=employee.pk).filter(start__lte=last_day).filter(
                    end__gte=first_day).values('id', 'start', 'end', 'type')

                data[employee.pk] = {
                    'employee_id': employee.pk,
                    'employee_login': employee.username,
                    'employee_first_name': employee.first_name,
                    'employee_last_name': employee.last_name,
                    'employee_work_hours': employee.job_time,
                    'days': days,
                    'absences': absences,
                }

            pl_holidays = holidays.PL(years=int(year)).keys()
            print(pl_holidays)

            return Response(data=data)


class ScheduleGetApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workplace_pk):
        # 127.0.0.1:8000/schedules/api/2/schedule_get?year=2022&month=5
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            workplace = Workplace.objects.get(id=workplace_pk)
            unit = workplace.workplace_unit
            shifts = Shift.objects.filter(schedule__workplace=workplace).filter(schedule__month=month).filter(
                schedule__year=year).order_by('date')
            shifts_statistic = Shift.objects.filter(schedule__workplace__workplace_unit=unit).filter(
                schedule__month=month).filter(schedule__year=year).order_by('shift_type__hour_start')
            days_num = calendar.monthrange(int(year), int(month))[1]
            days = {}
            statistics = {}

            for x in range(1, days_num + 1):
                date = datetime.date(int(year), int(month), x).strftime(date_format)
                days.update({date: []})

            for shift in shifts_statistic:
                shift_len = datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_end) - \
                            datetime.datetime.combine(datetime.date.min, shift.shift_type.hour_start)
                statistics.setdefault(shift.employee.id, {
                    'hours': 0,
                    'name': shift.employee.first_name + ' ' + shift.employee.last_name,
                    'jobtime': shift.employee.job_time,
                    'shift_type': {},
                    'absence': {}
                })
                statistics[shift.employee.id]['shift_type'].setdefault(shift.shift_type.name, 0)
                statistics[shift.employee.id]['shift_type'][shift.shift_type.name] += 1
                statistics[shift.employee.id]['hours'] += shift_len.seconds / 3600

                if not statistics[shift.employee.id].get(Absence.ABSENCE_TYPE[0][0]):
                    first_day = datetime.date(int(year), int(month), 1)
                    last_day = datetime.date(int(year), int(month), days_num)
                    for ab_type in Absence.ABSENCE_TYPE:
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
                        'time_start': shift.shift_type.hour_start,
                        'time_end': shift.shift_type.hour_end,
                        'name': shift.shift_type.name,
                        'worker': {
                            'id': shift.employee.id,
                            'first_name': shift.employee.first_name,
                            'last_name': shift.employee.last_name,
                        }
                    }
                ))

            response = {
                'unit_id': workplace.workplace_unit.id,
                'workplace_id': workplace.id,
                'unit_name': workplace.workplace_unit.name,
                'workplace_name': workplace.name,
                'days': days,
                'statistics': statistics
            }
            return Response(data=response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ShiftManageApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
                              active_days=v_data['active_days'],
                              demand=v_data['demand'],
                              color=v_data['color'],
                              is_used=v_data['is_used'],
                              workplace=workplace)
        shiftType.save()

    '''def perform_update(self, serializer):
        pass'''


class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if request.query_params.get('employee'):
            queryset = Absence.objects.filter(employee_id=request.query_params.get('employee'))
        else:
            queryset = Absence.objects.all()
        serializer = AbsenceSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]
