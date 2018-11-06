from django.http import JsonResponse

class IngestSerializer(Serializer):
    id = IntegerField(read_only=True)

    def create(self, validated_data):
        return


