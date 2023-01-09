from django.contrib.auth import get_user_model
from rest_framework import serializers


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_supervisor', 'job_time', 'user_unit',
                  'user_workplace', 'order_number']
        extra_kwargs = {
            'id': {'read_only': True},
            'user_unit': {'read_only': True},
            'user_workplace': {'read_only': True},
        }
        depth = 1


class EmailEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'first_name', 'last_name', 'order_number', 'job_time']
