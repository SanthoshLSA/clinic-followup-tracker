"""
Django app configuration for followups application.
"""
from django.apps import AppConfig


class FollowupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'followups'
    verbose_name = 'Clinic Follow-ups'
