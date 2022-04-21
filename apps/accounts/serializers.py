from django.contrib.auth import get_user_model
from rest_framework import serializers


class EmployeeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'first_name', 'last_name', ]
        extra_kwargs = {
            'id': {'read_only': True}
        }
