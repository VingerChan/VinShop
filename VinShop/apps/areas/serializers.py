from rest_framework import serializers
from apps.areas.models import Area
class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id','name']
