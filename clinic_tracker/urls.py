"""
URL configuration for clinic_tracker project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('followups.urls')),
]
