from rest_framework import serializers

from .models import ShiftType, Preference, Absence


class ShiftTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ShiftType
        fields = ['id', 'hour_start', 'hour_end', 'name', 'active_days', 'is_used']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class PreferenceSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """Check if user in shift_type workplace"""
        if data['shift_type'].workplace not in data['employee'].user_workplace.all():
            raise serializers.ValidationError("User is not assigned to workplace")
        return data

    class Meta:
        model = Preference
        fields = ['id', 'shift_type', 'employee', 'active_days']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = ['id', 'start', 'end', 'employee', 'type', 'hours_number']
