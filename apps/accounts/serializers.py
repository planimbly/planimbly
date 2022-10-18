from django.contrib.auth import get_user_model
from rest_framework import serializers


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'job_time', 'user_unit', 'user_workplace']
        extra_kwargs = {
            'id': {'read_only': True},
            'user_unit': {'read_only': True},
            'user_workplace': {'read_only': True},
        }
        depth = 1
