from django.urls import path, include
from rest_framework import routers

from apps.schedules.views import ShiftTypeManageView, ShiftTypeViewSet, ScheduleManageView, ScheduleGetApiView, \
    ScheduleCreateApiView, ShiftManageApiView, PreferenceViewSet, AbsenceViewSet, AbsenceManageView, \
    ScheduleReportGetApiView, AssignmentViewSet, JobTimeViewSet, JobTimeManageView, FreeDayViewSet, CheckAlgorithmView, \
    ScheduleGeneratingView, ScheduleEmployeeGetApiView, ScheduleUnitGetApiView, EmployeeScheduleView

shiftType_router = routers.DefaultRouter()
shiftType_router.register(r'shiftType', ShiftTypeViewSet, basename='shiftType')
router = routers.DefaultRouter()
router.register(r'preference', PreferenceViewSet, basename='preference')
router.register(r'absence', AbsenceViewSet, basename='absence')
router.register(r'assignment', AssignmentViewSet, basename='assignment')
router.register(r'jobtime', JobTimeViewSet, basename='jobtime')
router.register(r'freeday', FreeDayViewSet, basename='freeday')

urlpatterns = [
    path('shiftType_manage/', ShiftTypeManageView.as_view(), name="shiftType_manage"),
    path('schedule_manage/', ScheduleManageView.as_view(), name="schedule_manage"),
    path('absence_manage/', AbsenceManageView.as_view(), name="absence_manage"),
    path('jobtime_manage/', JobTimeManageView.as_view(), name="jobtime_manage"),
    path('schedule_generating/', ScheduleGeneratingView.as_view(), name="schedule_generating"),
    path('employee_schedule/', EmployeeScheduleView.as_view(), name="employee_schedule"),
    # API urls
    path('api/check_algorithm/', CheckAlgorithmView.as_view(), name="check_algorithm"),
    path('api/schedule_create/', ScheduleCreateApiView.as_view(), name='schedule_create'),
    path('api/<int:workplace_pk>/', include(shiftType_router.urls)),
    path('api/', include(router.urls)),
    path('api/shift_manage/', ShiftManageApiView.as_view(), name='shift_manage'),
    path('api/<int:workplace_pk>/schedule_get/', ScheduleGetApiView.as_view(),
         name='schedule_get'),
    path('api/<int:unit_pk>/schedule_unit_get/', ScheduleUnitGetApiView.as_view(),
         name='schedule_unit_get'),
    path('api/<int:employee_pk>/schedule_employee_get/', ScheduleEmployeeGetApiView.as_view(),
         name='schedule_employee_get'),
    path('api/<int:unit_pk>/schedule_report_get/', ScheduleReportGetApiView.as_view(),
         name='schedule_report_get')

]
