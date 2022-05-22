# Create your views here.
import calendar
import datetime

from django.views.generic import TemplateView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Employee
from apps.organizations.models import Workplace
from apps.schedules.models import ShiftType, Shift
from apps.schedules.serializers import ShiftTypeSerializer


class ShiftTypeManageView(TemplateView):
    template_name = 'schedules/shiftType_manage.html'


class ScheduleManageView(TemplateView):
    template_name = 'schedules/schedule_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workplace_list = Workplace.objects.filter(workplace_unit_id=self.kwargs['unit_pk'])
        context['workplace_list'] = workplace_list
        return context


# API VIEWS
class ScheduleCreateApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        date_start = self.request.data.get('date_start')
        date_end = self.request.data.get('date_end')
        workplace_list = self.request.data.get('workplace_list')
        if date_start and date_end and workplace_list:
            time_format = '%H:%M'
            shiftType_list = ShiftType.objects.filter(workplace_id__in=workplace_list)
            employee_list = Employee.objects.filter(user_workplace__in=workplace_list)
            workplace_dict = dict()
            for obj in shiftType_list:
                shift_dict = {'name': obj.name, 'hour_start': obj.hour_start.strftime(time_format),
                              'hour_end': obj.hour_end.strftime(time_format)}
                workplace_dict.setdefault(obj.workplace_id, {'shifts': []})
                workplace_dict[obj.workplace_id]['shifts'].append(shift_dict)
            for obj in employee_list:
                employee_dict = {'id': obj.id, 'first_name': obj.first_name, 'last_name': obj.last_name}
                for workplace in obj.user_workplace.all():
                    if workplace.id in workplace_dict:
                        workplace_dict[workplace.id].setdefault('employees', [])
                        if employee_dict not in workplace_dict[workplace.id]['employees']:
                            workplace_dict[workplace.id]['employees'].append(employee_dict)
            workplace_dict['date_start'] = date_start
            workplace_dict['date_end'] = date_end
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ShiftGetApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workplace_pk):
        # 127.0.0.1:8000/schedules/api/2/schedule_get?year=2022&month=5
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        date_format = '%y-%m-%d'
        if year and month:
            workplace = Workplace.objects.filter(id=workplace_pk).first()
            shifts = Shift.objects.filter(schedule__workplace=workplace).order_by('date')
            print(shifts)
            days_num = calendar.monthrange(int(year), int(month))[1]
            days = {}
            for x in range(1, days_num + 1):
                date = datetime.date(int(year), int(month), x).strftime(date_format)
                days.update({date: []})
            for shift in shifts:
                days[shift.date.strftime(date_format)].append((
                    {
                        'id': shift.id,
                        'time_start': shift.shift_type.hour_start,
                        'time_end': shift.shift_type.hour_start,
                        'name': shift.shift_type.name,
                        'worker': {
                            'id': shift.employee.id,
                            'first_name': shift.employee.first_name,
                            'last_name': shift.employee.last_name,
                        }
                    }
                ))
            response = {
                'unit_id': shifts.first().schedule.workplace.workplace_unit.id,
                'workplace_id': workplace_pk,
                'days': days
            }
            return Response(data=response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ShiftTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ShiftType.objects.filter(is_archive=False).filter(workplace_id=self.kwargs['workplace_pk'])
        return queryset

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        workplace = Workplace.objects.filter(pk=self.kwargs['workplace_pk']).first()
        shiftType = ShiftType(hour_start=v_data['hour_start'],
                              hour_end=v_data['hour_end'],
                              name=v_data['name'],
                              active_days=v_data['active_days'],
                              is_used=v_data['is_used'],
                              workplace=workplace)
        shiftType.save()

    '''def perform_update(self, serializer):
        pass'''
