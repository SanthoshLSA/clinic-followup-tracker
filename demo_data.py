"""
Script to generate demo data for the Clinic Follow-up Tracker.

Usage:
    python manage.py shell < demo_data.py
"""
from django.contrib.auth.models import User
from followups.models import Clinic, UserProfile, FollowUp
from datetime import date, timedelta

print("\n" + "="*60)
print("Creating Demo Data for Clinic Follow-up Tracker")
print("="*60 + "\n")

# Create clinics
print("Creating clinics...")
clinic1 = Clinic.objects.create(name="City General Hospital")
clinic2 = Clinic.objects.create(name="Sunshine Medical Center")
print(f" Created: {clinic1}")
print(f" Created: {clinic2}\n")

# Create users
print("Creating users...")
user1 = User.objects.create_user(
    username='doctor1',
    email='doctor1@cityhospital.com',
    password='demo123',
    first_name='Dr. Sarah',
    last_name='Johnson'
)
print(f" Created user: {user1.username} (password: demo123)")

user2 = User.objects.create_user(
    username='doctor2',
    email='doctor2@sunshine.com',
    password='demo123',
    first_name='Dr. Michael',
    last_name='Chen'
)
print(f" Created user: {user2.username} (password: demo123)\n")

# Link users to clinics
print("Linking users to clinics...")
profile1 = UserProfile.objects.create(user=user1, clinic=clinic1)
profile2 = UserProfile.objects.create(user=user2, clinic=clinic2)
print(f" {user1.username} → {clinic1.name}")
print(f" {user2.username} → {clinic2.name}\n")

# Create follow-ups for clinic1
print(f"Creating follow-ups for {clinic1.name}...")
followups_clinic1 = [
    {
        'patient_name': 'John Smith',
        'phone': '+919876543210',
        'language': 'en',
        'notes': 'Post-surgery checkup. Bring previous reports.',
        'due_date': date.today() + timedelta(days=2),
        'status': 'pending'
    },
    {
        'patient_name': 'Priya Sharma',
        'phone': '+919876543211',
        'language': 'hi',
        'notes': 'रक्त परीक्षण के परिणामों की समीक्षा',
        'due_date': date.today() + timedelta(days=5),
        'status': 'pending'
    },
    {
        'patient_name': 'Robert Brown',
        'phone': '+919876543212',
        'language': 'en',
        'notes': 'Diabetes management follow-up',
        'due_date': date.today() + timedelta(days=7),
        'status': 'pending'
    },
    {
        'patient_name': 'Amit Kumar',
        'phone': '+919876543213',
        'language': 'hi',
        'notes': '',
        'due_date': date.today() - timedelta(days=2),
        'status': 'done'
    },
]

for data in followups_clinic1:
    followup = FollowUp.objects.create(
        clinic=clinic1,
        created_by=user1,
        **data
    )
    print(f" {followup.patient_name} - {followup.due_date}")

# Create follow-ups for clinic2
print(f"\nCreating follow-ups for {clinic2.name}...")
followups_clinic2 = [
    {
        'patient_name': 'Emily Davis',
        'phone': '+919876543214',
        'language': 'en',
        'notes': 'Annual health checkup',
        'due_date': date.today() + timedelta(days=3),
        'status': 'pending'
    },
    {
        'patient_name': 'Rahul Verma',
        'phone': '+919876543215',
        'language': 'hi',
        'notes': 'एक्स-रे रिपोर्ट लाएं',
        'due_date': date.today() + timedelta(days=10),
        'status': 'pending'
    },
    {
        'patient_name': 'Sarah Wilson',
        'phone': '+919876543216',
        'language': 'en',
        'notes': 'Physical therapy session',
        'due_date': date.today() + timedelta(days=14),
        'status': 'pending'
    },
]

for data in followups_clinic2:
    followup = FollowUp.objects.create(
        clinic=clinic2,
        created_by=user2,
        **data
    )
    print(f" {followup.patient_name} - {followup.due_date}")

print("\n" + "="*60)
print("Demo Data Created Successfully!")
print("="*60 + "\n")

print("Login Credentials:")
print("-" * 60)
print(f"Username: doctor1 | Password: demo123 | Clinic: {clinic1.name}")
print(f"Username: doctor2 | Password: demo123 | Clinic: {clinic2.name}")
print("-" * 60 + "\n")

print("You can now:")
print("1. Login at http://localhost:8000/login/")
print("2. View dashboard at http://localhost:8000/dashboard/")
print("3. Access admin at http://localhost:8000/admin/")
print("\nNote: Create a superuser separately for admin access")
print("python manage.py createsuperuser\n")
