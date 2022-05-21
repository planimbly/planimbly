# Create your views here.
from django.views.generic import TemplateView
from rest_framework import viewsets, permissions
from rest_framework.views import APIView

from apps.organizations.models import Workplace  # , Unit
from apps.schedules.models import ShiftType, Schedule
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

    def post(self, request, *args, **kwargs):
        context = super(ScheduleManageView, self).get_context_data()
        return self.render_to_response(context=context)


# API VIEWS
class ShiftGetApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, unit_pk):
        # unit = Unit.objects.filter(id=unit_pk).first()
        workplace = Workplace.objects.filter(id=2).first()
        schedule = Schedule(date_start="2022-05-16", date_end="2022-05-23", workplace=workplace)
        schedule.save()
        print('a')
        '''workplace_list = Workplace.objects.filter(workplace_unit=unit)
        shift_dict = {}
        for workplace in workplace_list:
        grouped = dict()
        for obj in Shift.objects.filter().all():
            grouped.setdefault(obj.schedule, []).append(obj)'''


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
                              is_algorithm=v_data['is_algorithm'],
                              workplace=workplace)
        shiftType.save()

    '''def perform_update(self, serializer):
        pass'''
