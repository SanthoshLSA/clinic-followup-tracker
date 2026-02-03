import secrets
import string


def generate_clinic_code(length=10):
    from .models import Clinic
    chars = string.ascii_uppercase + string.digits
    for _ in range(100):
        code = 'CLINIC-' + ''.join(secrets.choice(chars) for _ in range(length))
        if not Clinic.objects.filter(clinic_code=code).exists():
            return code
    raise ValueError("Failed to generate unique clinic code")


def generate_public_token(length=32):
    from .models import FollowUp
    for _ in range(100):
        token = secrets.token_urlsafe(length)[:length]
        if not FollowUp.objects.filter(public_token=token).exists():
            return token
    raise ValueError("Failed to generate unique public token")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')