import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    A Django REST Framework field for handling image uploads
    through raw post data. It uses base64 for encoding and decoding
    the contents of the file.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_, imgstr = data.split(';base64,')
            ext = format_.split('/')[-1]
            decoded_file = base64.b64decode(imgstr)
            file_name = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)
