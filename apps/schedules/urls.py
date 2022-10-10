from django.urls import path, include
from rest_framework import routers

from apps.schedules.views import ShiftTypeManageView, ShiftTypeViewSet, ScheduleManageView, ScheduleGetApiView, \
    ScheduleCreateApiView, ShiftManageApiView

router = routers.DefaultRouter()
router.register(r'shiftType', ShiftTypeViewSet, basename='shiftType')

urlpatterns = [
    path('shiftType_manage/', ShiftTypeManageView.as_view(), name="shiftType_manage"),
    path('schedule_manage/', ScheduleManageView.as_view(), name="schedule_manage"),

    # API urls
    path('api/schedule_create/', ScheduleCreateApiView.as_view(), name='schedule_create'),
    path('api/<int:workplace_pk>/', include(router.urls)),
    path('api/shift_manage/', ShiftManageApiView.as_view(), name='shift_manage'),
    path('api/<int:workplace_pk>/schedule_get/', ScheduleGetApiView.as_view(),
         name='schedule_get')
]
