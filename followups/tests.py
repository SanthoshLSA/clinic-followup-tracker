from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta

from followups.models import Clinic, UserProfile, FollowUp, PublicViewLog


class ModelTests(TestCase):
    
    def test_unique_clinic_code_generation(self):
        """Test that clinic_code is unique across multiple clinics."""
        clinic1 = Clinic.objects.create(name="Clinic A")
        clinic2 = Clinic.objects.create(name="Clinic B")
        clinic3 = Clinic.objects.create(name="Clinic C")
        
        codes = [clinic1.clinic_code, clinic2.clinic_code, clinic3.clinic_code]
        self.assertEqual(len(codes), len(set(codes)), "Clinic codes must be unique")
        
        for code in codes:
            self.assertTrue(code.startswith('CLINIC-'))
            self.assertEqual(len(code), 17)
    
    def test_unique_public_token_generation(self):
        """Test that public_token is unique across multiple follow-ups."""
        clinic = Clinic.objects.create(name="Test Clinic")
        user = User.objects.create_user(username='doctor', password='pass')
        UserProfile.objects.create(user=user, clinic=clinic)
        
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
        
        tokens = [followup1.public_token, followup2.public_token, followup3.public_token]
        self.assertEqual(len(tokens), len(set(tokens)), "Public tokens must be unique")
        
        for token in tokens:
            self.assertEqual(len(token), 32)


class ViewTests(TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.clinic1 = Clinic.objects.create(name="Clinic One")
        self.clinic2 = Clinic.objects.create(name="Clinic Two")
        
        self.user1 = User.objects.create_user(username='doctor1', password='pass123')
        self.user2 = User.objects.create_user(username='doctor2', password='pass123')
        
        UserProfile.objects.create(user=self.user1, clinic=self.clinic1)
        UserProfile.objects.create(user=self.user2, clinic=self.clinic2)
        
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
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_accessible_after_login(self):
        """Test that authenticated users can access dashboard."""
        self.client.login(username='doctor1', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_cross_clinic_access_blocked_in_dashboard(self):
        """Test that users only see their own clinic's follow-ups."""
        self.client.login(username='doctor1', password='pass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertContains(response, "Patient A")
        self.assertNotContains(response, "Patient B")
    
    def test_cross_clinic_edit_blocked(self):
        """Test that users cannot edit follow-ups from other clinics."""
        self.client.login(username='doctor1', password='pass123')
        url = reverse('edit_followup', kwargs={'pk': self.followup2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
    
    def test_public_view_creates_log(self):
        """Test that accessing public page creates a PublicViewLog."""
        initial_count = PublicViewLog.objects.filter(followup=self.followup1).count()
        self.assertEqual(initial_count, 0)
        
        url = reverse('public_view', kwargs={'token': self.followup1.public_token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Patient A")
        
        final_count = PublicViewLog.objects.filter(followup=self.followup1).count()
        self.assertEqual(final_count, 1)