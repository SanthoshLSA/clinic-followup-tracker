from django.contrib import admin
from .models import Clinic, UserProfile, FollowUp, PublicViewLog


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'clinic_code', 'created_at']
    readonly_fields = ['clinic_code', 'created_at']
    search_fields = ['name', 'clinic_code']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'clinic']
    list_filter = ['clinic']
    search_fields = ['user__username', 'clinic__name']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'phone', 'clinic', 'due_date', 'status', 'language']
    list_filter = ['status', 'language', 'clinic', 'due_date']
    search_fields = ['patient_name', 'phone']
    readonly_fields = ['public_token', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'


@admin.register(PublicViewLog)
class PublicViewLogAdmin(admin.ModelAdmin):
    list_display = ['followup', 'viewed_at', 'ip_address']
    list_filter = ['viewed_at']
    readonly_fields = ['followup', 'viewed_at', 'user_agent', 'ip_address']
    
    def has_add_permission(self, request):
        return False