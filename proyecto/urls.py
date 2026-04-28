"""
URL configuration for proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from tienda import views as tienda_views
from tienda.api import api

urlpatterns = [
    path('', tienda_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('tienda/', include('tienda.urls')),
    path('api/', api.urls)
]

if settings.DEBUG and not settings.S3_ENABLE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
