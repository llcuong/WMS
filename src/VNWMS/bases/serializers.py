from rest_framework import serializers
from bases.models import Status


class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = '__all__'