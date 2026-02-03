"""
Management command to import follow-ups from CSV file.

Usage:
    python manage.py import_followups --csv sample.csv --username doctor1
"""
import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from followups.models import FollowUp


class Command(BaseCommand):
    """
    Import follow-ups from a CSV file.
    
    CSV Format:
        patient_name,phone,language,notes,due_date,status
    
    All fields except 'notes' are required.
    """
    help = 'Import follow-ups from a CSV file'

    def add_arguments(self, parser):
        """Define command arguments."""
        parser.add_argument(
            '--csv',
            type=str,
            required=True,
            help='Path to the CSV file'
        )
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username of the user who will own the follow-ups'
        )

    def handle(self, *args, **options):
        """Execute the import command."""
        csv_file = options['csv']
        username = options['username']
        
        # Validate user exists and has a clinic
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        try:
            clinic = user.profile.clinic
        except:
            raise CommandError(f'User "{username}" is not linked to any clinic')
        
        # Track statistics
        created_count = 0
        skipped_count = 0
        errors = []
        
        # Open and read CSV file
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate CSV headers
                required_fields = {'patient_name', 'phone', 'language', 'due_date', 'status'}
                csv_fields = set(reader.fieldnames)
                
                if not required_fields.issubset(csv_fields):
                    missing = required_fields - csv_fields
                    raise CommandError(
                        f'CSV file is missing required columns: {", ".join(missing)}'
                    )
                
                self.stdout.write(self.style.SUCCESS(
                    f'Processing CSV file: {csv_file}'
                ))
                self.stdout.write(f'Importing for user: {username} ({clinic.name})\n')
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Validate and create follow-up
                        with transaction.atomic():
                            followup = self._create_followup(row, user, clinic)
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Row {row_num}: Created follow-up for {followup.patient_name}'
                                )
                            )
                    
                    except Exception as e:
                        skipped_count += 1
                        error_msg = f'✗ Row {row_num}: {str(e)}'
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(error_msg))
        
        except FileNotFoundError:
            raise CommandError(f'File not found: {csv_file}')
        
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
        
        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Import completed!'))
        self.stdout.write(f'Total rows processed: {created_count + skipped_count}')
        self.stdout.write(self.style.SUCCESS(f'Successfully created: {created_count}'))
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (errors): {skipped_count}'))
        
        self.stdout.write('=' * 60)

    def _create_followup(self, row, user, clinic):
        """
        Create a follow-up from CSV row data.
        
        Args:
            row: Dictionary containing CSV row data
            user: User object who will own the follow-up
            clinic: Clinic object to associate with
            
        Returns:
            Created FollowUp object
            
        Raises:
            ValueError: If validation fails
        """
        # Extract and validate fields
        patient_name = row.get('patient_name', '').strip()
        phone = row.get('phone', '').strip()
        language = row.get('language', '').strip().lower()
        notes = row.get('notes', '').strip()
        due_date_str = row.get('due_date', '').strip()
        status = row.get('status', '').strip().lower()
        
        # Validate required fields
        if not patient_name:
            raise ValueError('patient_name is required')
        
        if not phone:
            raise ValueError('phone is required')
        
        if not language:
            raise ValueError('language is required')
        
        if not due_date_str:
            raise ValueError('due_date is required')
        
        if not status:
            raise ValueError('status is required')
        
        # Validate language
        if language not in ['en', 'hi']:
            raise ValueError(f'Invalid language "{language}". Must be "en" or "hi"')
        
        # Validate status
        if status not in ['pending', 'done']:
            raise ValueError(f'Invalid status "{status}". Must be "pending" or "done"')
        
        # Validate and parse phone
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            raise ValueError('Phone must start with +')
        
        if not phone[1:].isdigit():
            raise ValueError('Phone must contain only digits after +')
        
        if len(phone) < 11 or len(phone) > 16:
            raise ValueError('Phone must be 10-15 digits after country code')
        
        # Parse due date
        try:
            # Try multiple date formats
            for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    due_date = datetime.strptime(due_date_str, date_format).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(
                    f'Invalid date format "{due_date_str}". Use YYYY-MM-DD'
                )
        except Exception as e:
            raise ValueError(f'Invalid due_date: {str(e)}')
        
        # Create follow-up
        followup = FollowUp.objects.create(
            clinic=clinic,
            created_by=user,
            patient_name=patient_name,
            phone=phone,
            language=language,
            notes=notes,
            due_date=due_date,
            status=status
        )
        
        return followup
