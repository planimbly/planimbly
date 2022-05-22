from rest_framework import serializers

from .models import ShiftType


class ShiftTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ShiftType
        fields = ['id', 'hour_start', 'hour_end', 'name', 'active_days', 'is_used']
        extra_kwargs = {
            'id': {'read_only': True}
        }
