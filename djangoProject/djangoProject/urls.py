from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('website.urls', 'website'), namespace='website')),
    path('', include('django_prometheus.urls')),
]
