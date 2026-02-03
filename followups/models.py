from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    clinic_code = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.clinic_code:
            from .utils import generate_clinic_code
            self.clinic_code = generate_clinic_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.clinic_code})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} - {self.clinic.name}"


class FollowUp(models.Model):
    LANGUAGE_CHOICES = [('en', 'English'), ('hi', 'Hindi')]
    STATUS_CHOICES = [('pending', 'Pending'), ('done', 'Done')]

    phone_validator = RegexValidator(
        regex=r'^\+\d{10,15}$',
        message="Phone number must start with + and contain 10-15 digits"
    )

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='followups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_followups')
    patient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    notes = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    public_token = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        indexes = [
            models.Index(fields=['clinic', 'status']),
            models.Index(fields=['due_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.public_token:
            from .utils import generate_public_token
            self.public_token = generate_public_token()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_name} - {self.due_date} ({self.status})"

    def get_public_url(self):
        return f"/p/{self.public_token}/"

    @property
    def view_count(self):
        return self.public_views.count()


class PublicViewLog(models.Model):
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='public_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.followup.patient_name} - {self.viewed_at}"