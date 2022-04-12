from django.shortcuts import render

# Create your views here.
from django.views import View
from rest_framework import viewsets, permissions

from apps.accounts.models import Employee
from apps.accounts.serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]