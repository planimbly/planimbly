from django import forms
from django.db.models import Q
from django.forms import formset_factory, inlineformset_factory

from ..accounts.models import Employee
from .models import Organization


class OrganizationCreateForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'


class ManagerCreateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['email', 'username', 'first_name', 'last_name']
