import datetime

from rest_framework import serializers

from .models import ShiftType, Preference, Absence, Assignment, JobTime, FreeDay
from ..accounts.models import Employee
from ..accounts.serializers import EmployeeSerializer


class JobTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTime
        fields = ['id', 'year', 'january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december']


class FreeDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = FreeDay
        fields = ['id', 'day', 'name', 'organization']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class ShiftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftType
        fields = ['id', 'hour_start', 'hour_end', 'name', 'shift_code', 'workplace', 'demand', 'color', 'active_days',
                  'is_used']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, data):
        """Check if shift takes 8 hours"""
        shift_len = datetime.datetime.combine(datetime.date.min, data['hour_end']) - datetime.datetime.combine(
            datetime.date.min, data['hour_start'])
        shift_len = shift_len.seconds / 3600
        if shift_len != 8.0 and data['is_used'] is True:
            raise serializers.ValidationError("Aktywne zmiany muszą być ośmiogodzinne!")
        return data


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['id', 'shift_type', 'employee', 'active_days']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, data):
        """Check if user in shift_type workplace"""
        if data['shift_type'].workplace not in data['employee'].user_workplace.all():
            raise serializers.ValidationError("Użytkownik nie jest przypisany do jednostki")
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['shift_type_obj'] = ShiftTypeSerializer(ShiftType.objects.get(pk=data['shift_type'])).data
        return data


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'shift_type', 'employee', 'start', 'end', 'negative_flag']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['shift_type_obj'] = ShiftTypeSerializer(ShiftType.objects.get(pk=data['shift_type'])).data
        return data


class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = ['id', 'start', 'end', 'employee', 'type', 'hours_number']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['employee_obj'] = EmployeeSerializer(Employee.objects.get(pk=data['employee'])).data
        data['employee_first_name'] = EmployeeSerializer(Employee.objects.get(pk=data['employee'])).data['first_name']
        data['employee_last_name'] = EmployeeSerializer(Employee.objects.get(pk=data['employee'])).data['last_name']
        data['employee_username'] = EmployeeSerializer(Employee.objects.get(pk=data['employee'])).data['username']
        return data
