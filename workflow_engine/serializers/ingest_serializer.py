from django.http import JsonResponse
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import IntegerField

class IngestSerializer(ModelSerializer):
    id = IntegerField(read_only=True)

    def create(self, validated_data):
        return


