from django import forms

from .models import Organization
from ..accounts.models import Employee


class OrganizationCreateForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'


class ManagerCreateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['email', 'username', 'first_name', 'last_name', 'order_number', 'job_time']
