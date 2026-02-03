"""
Comprehensive test suite for the clinic follow-up tracker application.

Tests cover:
1. Unique clinic_code generation
2. Unique public_token generation
3. Dashboard login requirement
4. Cross-clinic access blocking
5. PublicViewLog creation
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta

from .models import Clinic, UserProfile, FollowUp, PublicViewLog
from .utils import generate_clinic_code, generate_public_token


class ModelTests(TestCase):
    """Test cases for data models."""
    
    def test_unique_clinic_code_generation(self):
        """
        Test that clinic_code is unique across multiple clinics.
        
        Requirement: Unique generation of clinic_code
        """
        # Create multiple clinics
        clinic1 = Clinic.objects.create(name="Clinic A")
        clinic2 = Clinic.objects.create(name="Clinic B")
        clinic3 = Clinic.objects.create(name="Clinic C")
        
        # Verify all clinic codes are unique
        codes = [clinic1.clinic_code, clinic2.clinic_code, clinic3.clinic_code]
        self.assertEqual(len(codes), len(set(codes)), "Clinic codes must be unique")
        
        # Verify format (should start with CLINIC-)
        for code in codes:
            self.assertTrue(code.startswith('CLINIC-'))
            self.assertEqual(len(code), 17)  # CLINIC- (7) + 10 chars
    
    def test_unique_public_token_generation(self):
        """
        Test that public_token is unique across multiple follow-ups.
        
        Requirement: Unique generation of public_token
        """
        # Setup
        clinic = Clinic.objects.create(name="Test Clinic")
        user = User.objects.create_user(username='doctor', password='pass')
        UserProfile.objects.create(user=user, clinic=clinic)
        
        # Create multiple follow-ups
        followup1 = FollowUp.objects.create(
            clinic=clinic,
            created_by=user,
            patient_name="Patient 1",
            phone="+919876543210",
            language="en",
            due_date=date.today() + timedelta(days=1),
            status="pending"
        )
        
        followup2 = FollowUp.objects.create(
            clinic=clinic,
            created_by=user,
            patient_name="Patient 2",
            phone="+919876543211",
            language="hi",
            due_date=date.today() + timedelta(days=2),
            status="pending"
        )
        
        followup3 = FollowUp.objects.create(
            clinic=clinic,
            created_by=user,
            patient_name="Patient 3",
            phone="+919876543212",
            language="en",
            due_date=date.today() + timedelta(days=3),
            status="done"
        )
        
        # Verify all tokens are unique
        tokens = [
            followup1.public_token,
            followup2.public_token,
            followup3.public_token
        ]
        self.assertEqual(len(tokens), len(set(tokens)), "Public tokens must be unique")
        
        # Verify token length
        for token in tokens:
            self.assertEqual(len(token), 32)
    
    def test_clinic_str_representation(self):
        """Test string representation of Clinic model."""
        clinic = Clinic.objects.create(name="City Hospital")
        expected = f"City Hospital ({clinic.clinic_code})"
        self.assertEqual(str(clinic), expected)
    
    def test_followup_view_count_property(self):
        """Test that view_count property returns correct count."""
        # Setup
        clinic = Clinic.objects.create(name="Test Clinic")
        user = User.objects.create_user(username='doctor', password='pass')
        UserProfile.objects.create(user=user, clinic=clinic)
        
        followup = FollowUp.objects.create(
            clinic=clinic,
            created_by=user,
            patient_name="Test Patient",
            phone="+919876543210",
            language="en",
            due_date=date.today() + timedelta(days=1),
            status="pending"
        )
        
        # Initially should be 0
        self.assertEqual(followup.view_count, 0)
        
        # Create some view logs
        PublicViewLog.objects.create(followup=followup, ip_address="192.168.1.1")
        PublicViewLog.objects.create(followup=followup, ip_address="192.168.1.2")
        PublicViewLog.objects.create(followup=followup, ip_address="192.168.1.3")
        
        # Should now be 3
        self.assertEqual(followup.view_count, 3)


class ViewTests(TestCase):
    """Test cases for views and access control."""
    
    def setUp(self):
        """Set up test data."""
        # Create two clinics
        self.clinic1 = Clinic.objects.create(name="Clinic One")
        self.clinic2 = Clinic.objects.create(name="Clinic Two")
        
        # Create users for each clinic
        self.user1 = User.objects.create_user(username='doctor1', password='pass123')
        self.user2 = User.objects.create_user(username='doctor2', password='pass123')
        
        # Link users to clinics
        UserProfile.objects.create(user=self.user1, clinic=self.clinic1)
        UserProfile.objects.create(user=self.user2, clinic=self.clinic2)
        
        # Create follow-ups for each clinic
        self.followup1 = FollowUp.objects.create(
            clinic=self.clinic1,
            created_by=self.user1,
            patient_name="Patient A",
            phone="+919876543210",
            language="en",
            due_date=date.today() + timedelta(days=1),
            status="pending"
        )
        
        self.followup2 = FollowUp.objects.create(
            clinic=self.clinic2,
            created_by=self.user2,
            patient_name="Patient B",
            phone="+919876543211",
            language="hi",
            due_date=date.today() + timedelta(days=2),
            status="pending"
        )
        
        self.client = Client()
    
    def test_dashboard_requires_login(self):
        """
        Test that dashboard requires authentication.
        
        Requirement: Dashboard requires login
        """
        response = self.client.get(reverse('dashboard'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_accessible_after_login(self):
        """Test that authenticated users can access dashboard."""
        self.client.login(username='doctor1', password='pass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Follow-ups Dashboard')
    
    def test_cross_clinic_access_blocked_in_dashboard(self):
        """
        Test that users only see their own clinic's follow-ups.
        
        Requirement: Cross-clinic access is blocked
        """
        # Login as user1 (Clinic One)
        self.client.login(username='doctor1', password='pass123')
        response = self.client.get(reverse('dashboard'))
        
        # Should see own follow-up
        self.assertContains(response, "Patient A")
        
        # Should NOT see other clinic's follow-up
        self.assertNotContains(response, "Patient B")
    
    def test_cross_clinic_edit_blocked(self):
        """
        Test that users cannot edit follow-ups from other clinics.
        
        Requirement: Cross-clinic access is blocked
        """
        # Login as user1 (Clinic One)
        self.client.login(username='doctor1', password='pass123')
        
        # Try to edit followup2 (belongs to Clinic Two)
        url = reverse('edit_followup', kwargs={'pk': self.followup2.pk})
        response = self.client.get(url)
        
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_cross_clinic_mark_done_blocked(self):
        """
        Test that users cannot mark done follow-ups from other clinics.
        
        Requirement: Cross-clinic access is blocked
        """
        # Login as user1 (Clinic One)
        self.client.login(username='doctor1', password='pass123')
        
        # Try to mark done followup2 (belongs to Clinic Two)
        url = reverse('mark_done', kwargs={'pk': self.followup2.pk})
        response = self.client.post(url)
        
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_public_view_creates_log(self):
        """
        Test that accessing public page creates a PublicViewLog.
        
        Requirement: Public page creates a PublicViewLog
        """
        # Get initial count
        initial_count = PublicViewLog.objects.filter(followup=self.followup1).count()
        self.assertEqual(initial_count, 0)
        
        # Access public page (no login required)
        url = reverse('public_view', kwargs={'token': self.followup1.public_token})
        response = self.client.get(url)
        
        # Should be accessible
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Patient A")
        
        # Should create a log entry
        final_count = PublicViewLog.objects.filter(followup=self.followup1).count()
        self.assertEqual(final_count, 1)
        
        # Verify log details
        log = PublicViewLog.objects.filter(followup=self.followup1).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.followup, self.followup1)
    
    def test_public_view_multiple_visits(self):
        """
        Test that multiple visits create multiple log entries.
        
        Requirement: Public page creates a PublicViewLog
        """
        url = reverse('public_view', kwargs={'token': self.followup1.public_token})
        
        # Access page 3 times
        self.client.get(url)
        self.client.get(url)
        self.client.get(url)
        
        # Should have 3 log entries
        count = PublicViewLog.objects.filter(followup=self.followup1).count()
        self.assertEqual(count, 3)
    
    def test_login_view_redirects_authenticated_users(self):
        """Test that authenticated users are redirected from login page."""
        self.client.login(username='doctor1', password='pass123')
        response = self.client.get(reverse('login'))
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
    
    def test_create_followup_requires_login(self):
        """Test that creating follow-up requires authentication."""
        url = reverse('create_followup')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class UtilityTests(TestCase):
    """Test cases for utility functions."""
    
    def test_generate_clinic_code_format(self):
        """Test clinic code generation format."""
        code = generate_clinic_code()
        
        # Should start with CLINIC-
        self.assertTrue(code.startswith('CLINIC-'))
        
        # Should be 17 characters total
        self.assertEqual(len(code), 17)
        
        # Characters after CLINIC- should be alphanumeric
        suffix = code.replace('CLINIC-', '')
        self.assertTrue(suffix.isalnum())
    
    def test_generate_public_token_format(self):
        """Test public token generation format."""
        token = generate_public_token()
        
        # Should be 32 characters
        self.assertEqual(len(token), 32)
        
        # Should be URL-safe
        import string
        allowed = string.ascii_letters + string.digits + '-_'
        self.assertTrue(all(c in allowed for c in token))


class FormTests(TestCase):
    """Test cases for form validation."""
    
    def test_phone_validation(self):
        """Test phone number validation in FollowUpForm."""
        from .forms import FollowUpForm
        
        # Valid phone numbers
        valid_phones = [
            '+919876543210',
            '+12125551234',
            '+447911123456',
        ]
        
        for phone in valid_phones:
            form_data = {
                'patient_name': 'Test Patient',
                'phone': phone,
                'language': 'en',
                'due_date': date.today() + timedelta(days=1),
                'status': 'pending',
                'notes': ''
            }
            form = FollowUpForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Phone {phone} should be valid")
        
        # Invalid phone numbers
        invalid_phones = [
            '9876543210',  # Missing +
            '+91 9876543210',  # Has space
            '+91-9876543210',  # Has dash
            '+91987654',  # Too short
            'invalid',  # Not numeric
        ]
        
        for phone in invalid_phones:
            form_data = {
                'patient_name': 'Test Patient',
                'phone': phone,
                'language': 'en',
                'due_date': date.today() + timedelta(days=1),
                'status': 'pending',
                'notes': ''
            }
            form = FollowUpForm(data=form_data)
            self.assertFalse(form.is_valid(), f"Phone {phone} should be invalid")
    
    def test_due_date_validation(self):
        """Test due date validation (should not be in past for new entries)."""
        from .forms import FollowUpForm
        
        # Past date should be invalid for new follow-ups
        past_data = {
            'patient_name': 'Test Patient',
            'phone': '+919876543210',
            'language': 'en',
            'due_date': date.today() - timedelta(days=1),
            'status': 'pending',
            'notes': ''
        }
        form = FollowUpForm(data=past_data)
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)
        
        # Future date should be valid
        future_data = {
            'patient_name': 'Test Patient',
            'phone': '+919876543210',
            'language': 'en',
            'due_date': date.today() + timedelta(days=1),
            'status': 'pending',
            'notes': ''
        }
        form = FollowUpForm(data=future_data)
        self.assertTrue(form.is_valid())
