from rest_framework import serializers

from .models import Unit, Workplace


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'allow_preferences']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class WorkplaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Workplace
        fields = ['id', 'name']
        extra_kwargs = {
            'id': {'read_only': True}
        }
