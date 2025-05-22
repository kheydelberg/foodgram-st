from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import uuid

# CHECKED


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):

            format, imgstr = data.split(';base64,')

            ext = format.split('/')[-1]

            decoded_file = base64.b64decode(imgstr)

            file_name = f"{uuid.uuid4()}.{ext}"

            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)
