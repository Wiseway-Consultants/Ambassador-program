"""
URL configuration for ambassador_program project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from ambassador_program.views import openapi_yaml, GHLview, QRCodeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('user.urls')),
    path('prospects/', include('prospect.urls')),
    path('commission/', include('commission.urls')),
    path('ghl/token/', GHLview.as_view(), name='ghl-token'),
    path('api/schema.yaml', openapi_yaml, name='custom-schema'),
    path(
        'api/redoc/',
        TemplateView.as_view(
            template_name="redoc.html",
            extra_context={"schema_url": "/api/schema.yaml"},  # URL to your custom schema
        ),
        name='redoc',
    ),
    path('qr/static/', QRCodeView.as_view(), name='qr-static'),
]
