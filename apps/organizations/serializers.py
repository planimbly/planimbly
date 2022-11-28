from rest_framework import serializers

from .models import Unit, Workplace, WorkplaceClosing


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name']
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


class WorkplaceClosingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkplaceClosing
        fields = ['id', 'start', 'end', 'workplace']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workplace_obj'] = WorkplaceSerializer(Workplace.objects.get(pk=data['workplace'])).data
        return data
