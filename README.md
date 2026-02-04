# Clinic Follow-Up Tracker Application

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SanthoshLSA/clinic-followup-tracker.git
cd clinic_followup_tracker
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. MySQL Configuration

Create a MySQL database:

```sql
CREATE DATABASE clinic_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'clinic_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON clinic_tracker.* TO 'clinic_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Update Database Settings

Edit `clinic_tracker/settings.py` and update the DATABASES configuration:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'clinic_tracker',
        'USER': 'clinic_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Run Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

### Creating Clinics and User Profiles

**Option 1: Using Django Admin**

1. Login to admin panel at `http://localhost:8000/admin`
2. Create a Clinic (name will auto-generate a unique clinic_code)
3. Create a UserProfile linking a User to the Clinic

**Option 2: Using Django Shell**

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from followups.models import Clinic, UserProfile

# Create clinic
clinic = Clinic.objects.create(name="City General Hospital")
print(f"Clinic Code: {clinic.clinic_code}")

# Create user
user = User.objects.create_user(
    username='doctor1',
    email='doctor1@clinic.com',
    password='securepass123'
)

# Link user to clinic
profile = UserProfile.objects.create(user=user, clinic=clinic)
print(f"User {user.username} linked to {clinic.name}")
```

## Running Tests

Run all tests:

```bash
python manage.py test followups
```

Run with verbose output:

```bash
python manage.py test followups --verbosity=2
```

## CSV Import

### Format

Create a CSV file with the following columns:

```csv
patient_name,phone,language,notes,due_date,status
John Doe,+919876543210,en,First visit follow-up,2024-12-25,pending
Jane Smith,+919876543211,hi,Lab results review,2024-12-26,pending
```

### Import Command

```bash
python manage.py import_followups --csv sample.csv --username doctor1
```

**Parameters:**
- `--csv`: Path to CSV file
- `--username`: Username of the user who will own the follow-ups

**Sample CSV file is included in the repository as `sample.csv`**

## Application Usage

### Login

Navigate to `http://localhost:8000/login/` and use your credentials.

### Dashboard

- View all follow-ups for your clinic
- Filter by status (All/Pending/Done)
- Filter by due date range
- See summary statistics
- Access public tracking links
- View number of public page visits

### Create Follow-up

1. Click "Add New Follow-up"
2. Fill in patient details
3. Set due date and status
4. Submit

### Edit Follow-up

1. Click "Edit" on any follow-up
2. Update details
3. Save changes

### Mark as Done

Click "Mark as Done" button on pending follow-ups.

### Public Tracking Page

Share the public link with patients:
- Format: `http://localhost:8000/p/<public_token>/`
- No login required
- Shows instructions in patient's language (English/Hindi)
- Each visit is logged automatically

### View Logs

View logs in Django Admin:
- Navigate to "Public view logs"
- See timestamp, IP address, and user agent for each visit

## Key Features Implementation

### Security

- CSRF protection on all forms
- Login required decorators
- Clinic-based data isolation
- Secure token generation using Python's `secrets` module

### Database

- Unique constraints on clinic_code and public_token
- Foreign key relationships with proper cascading
- Indexed fields for better query performance

### Code Quality

- PEP 8 compliant
- Comprehensive docstrings
- Type hints where applicable
- DRY principles
- Separation of concerns

### Testing

Tests cover:
1. Unique clinic_code generation
2. Unique public_token generation
3. Login requirement for dashboard
4. Cross-clinic access blocking
5. PublicViewLog creation
