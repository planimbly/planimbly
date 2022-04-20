from django.contrib.auth import get_user_model
from django.http import request
from rest_framework import viewsets, permissions

from apps.accounts.models import Employee
from apps.accounts.serializers import EmployeeSerializer
from apps.organizations.views import send_user_activation_mail


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.all().filter(user_org=self.request.user.user_org) \
            .exclude(id=self.request.user.id)
        return queryset

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        password = Employee.objects.make_random_password()
        employee = get_user_model().objects.create_user(v_data['email'], v_data['username'],
                                                        v_data['first_name'], v_data['last_name'], password,
                                                        self.request.user.user_org, False)
        send_user_activation_mail(employee, self.request)
