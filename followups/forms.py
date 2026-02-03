from django import forms
from .models import FollowUp
from django.core.exceptions import ValidationError
from datetime import date


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ['patient_name', 'phone', 'language', 'due_date', 'status', 'notes']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter patient name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+919876543210'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional notes'}),
        }
        help_texts = {
            'phone': 'Format: +<country_code><number> (e.g., +919876543210)',
            'due_date': 'Date when the follow-up is due',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.replace(' ', '').replace('-', '')
            if not phone.startswith('+'):
                raise ValidationError("Phone number must start with + followed by country code")
            if len(phone) < 11 or len(phone) > 16:
                raise ValidationError("Phone number must be between 10-15 digits after country code")
            if not phone[1:].isdigit():
                raise ValidationError("Phone number must contain only digits after +")
        return phone

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            if not self.instance.pk or self.instance.due_date != due_date:
                if due_date < date.today():
                    raise ValidationError("Due date cannot be in the past")
        return due_date

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        due_date = cleaned_data.get('due_date')
        
        if status == 'done' and due_date and due_date < date.today():
            if 'due_date' in self.errors:
                del self.errors['due_date']
        
        return cleaned_data


class FollowUpFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('all', 'All'), ('pending', 'Pending'), ('done', 'Done')],
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    due_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'From'})
    )
    due_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'To'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('due_date_from')
        date_to = cleaned_data.get('due_date_to')
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date must be before or equal to end date")
        return cleaned_data