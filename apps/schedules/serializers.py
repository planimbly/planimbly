from rest_framework import serializers

from .models import ShiftType, Preference


class ShiftTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ShiftType
        fields = ['id', 'hour_start', 'hour_end', 'name', 'active_days', 'is_used']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class PreferenceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Preference
        fields = ['id', 'shift_type', 'employee', 'active_days']
        extra_kwargs = {
            'id': {'read_only': True}
        }
