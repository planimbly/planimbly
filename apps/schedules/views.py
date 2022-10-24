# Create your views here.
import calendar
import datetime

from django.views.generic import TemplateView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import scripts.run_algorithm
from apps.accounts.models import Employee
from apps.organizations.models import Workplace, Unit
from apps.schedules.models import ShiftType, Shift, Schedule, Preference, Absence
from apps.schedules.serializers import ShiftTypeSerializer, PreferenceSerializer, AbsenceSerializer


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

        shiftType_list = list(ShiftType.objects.filter(workplace_id__in=workplace_list))

        emp_for_workplaces = {}

        for work_id in workplace_list:
            emp_for_workplaces[work_id] = Employee.objects.filter(
                user_workplace__in=Workplace.objects.filter(id__in=[work_id])).distinct().order_by('id')

        employee_list = Employee.objects.filter(user_workplace__in=workplace_query).distinct().order_by('id')

        data = scripts.run_algorithm.main_algorithm(schedule_dict, employee_list, shiftType_list, year, month,
                                                    emp_for_workplaces)
        for shift in data:
            shift.save()
        return Response()


class ScheduleGetApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workplace_pk):
        # 127.0.0.1:8000/schedules/api/2/schedule_get?year=2022&month=5
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%Y-%m-%d'
        if year and month:
            workplace = Workplace.objects.filter(id=workplace_pk).first()
            shifts = Shift.objects.filter(schedule__workplace=workplace).filter(schedule__month=month).filter(
                schedule__year=year).order_by('date')
            days_num = calendar.monthrange(int(year), int(month))[1]
            days = {}
            for x in range(1, days_num + 1):
                date = datetime.date(int(year), int(month), x).strftime(date_format)
                days.update({date: []})
            for shift in shifts:
                days[shift.date.strftime(date_format)].append((
                    {
                        'id': shift.id,
                        'shift_type_id': shift.shift_type.id,
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
                'workplace_id': workplace_pk,
                'days': days
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
            schedule = Schedule.objects.filter(year=date.year).filter(month=date.month).first()
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
