from django.urls import path, include
from rest_framework import routers

from apps.schedules.views import ShiftTypeManageView, ShiftTypeViewSet, ScheduleManageView, ShiftGetApiView, \
    ScheduleCreateApiView

router = routers.DefaultRouter()
router.register(r'shiftType', ShiftTypeViewSet, basename='shiftType')

urlpatterns = [
    path('<int:workplace_pk>/shiftType_manage/', ShiftTypeManageView.as_view(), name="shiftType_manage"),
    path('<int:unit_pk>/schedule_manage/', ScheduleManageView.as_view(), name="schedule_manage"),

    # API urls
    path('api/schedule_create/', ScheduleCreateApiView.as_view(), name='schedule_create'),
    path('api/<int:workplace_pk>/', include(router.urls)),
    path('api/<int:workplace_pk>/schedule_get/', ShiftGetApiView.as_view(),
         name='schedule_get')
]
