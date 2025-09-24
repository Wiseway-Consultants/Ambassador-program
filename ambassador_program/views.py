from os import path

from django.conf import settings
from django.http import HttpResponse


def openapi_yaml(request):
    filepath = path.join(settings.BASE_DIR, "staticfiles", "openapi.yaml")
    with open(filepath, "r") as f:
        return HttpResponse(f.read(), content_type="application/yaml")
