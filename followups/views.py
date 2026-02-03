from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from .models import FollowUp, PublicViewLog
from .forms import FollowUpForm, FollowUpFilterForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import get_client_ip, get_user_agent
import csv
from django.http import HttpResponse


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'followups/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def export_followups_csv(request):
    """Export follow-ups to CSV file."""
    try:
        user_clinic = request.user.profile.clinic
    except:
        messages.error(request, 'Your account is not linked to any clinic.')
        return redirect('dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="followups_{user_clinic.clinic_code}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Patient Name', 'Phone', 'Language', 'Due Date', 
        'Status', 'Notes', 'Public Token', 'View Count', 'Created At'
    ])
    
    followups = (
    FollowUp.objects
    .filter(clinic=user_clinic)
    .select_related('created_by', 'clinic')
    .prefetch_related('public_views')
    .order_by('-due_date', '-created_at')
)


    
    for followup in followups:
        writer.writerow([
            followup.patient_name,
            followup.phone,
            followup.get_language_display(),
            followup.due_date.strftime('%Y-%m-%d'),
            followup.get_status_display(),
            followup.notes,
            followup.public_token,
            followup.views,
            followup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response

@login_required
def dashboard(request):
    try:
        user_clinic = request.user.profile.clinic
    except:
        messages.error(request, 'Your account is not linked to any clinic. Please contact admin.')
        return render(request, 'followups/no_clinic.html')
    
    followups = (
    FollowUp.objects
    .filter(clinic=user_clinic)
    .select_related('created_by', 'clinic')
    .prefetch_related('public_views')
    .order_by('-due_date', '-created_at')
)

    
    filter_form = FollowUpFilterForm(request.GET)
    
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        due_date_from = filter_form.cleaned_data.get('due_date_from')
        due_date_to = filter_form.cleaned_data.get('due_date_to')
        
        if status and status != 'all':
            followups = followups.filter(status=status)
        if due_date_from:
            followups = followups.filter(due_date__gte=due_date_from)
        if due_date_to:
            followups = followups.filter(due_date__lte=due_date_to)
    
    total_count = followups.count()
    pending_count = followups.filter(status='pending').count()
    done_count = followups.filter(status='done').count()
    followups = followups.annotate(views=Count('public_views'))
    
    # Pagination
    paginator = Paginator(followups, 10)  
    page = request.GET.get('page', 1)
    
    try:
        followups_page = paginator.page(page)
    except PageNotAnInteger:
        followups_page = paginator.page(1)
    except EmptyPage:
        followups_page = paginator.page(paginator.num_pages)
    
    context = {
        'followups': followups_page,
        'filter_form': filter_form,
        'total_count': total_count,
        'pending_count': pending_count,
        'done_count': done_count,
        'clinic': user_clinic,
        'paginator': paginator,
    }
    
    return render(request, 'followups/dashboard.html', context)


@login_required
def create_followup(request):
    try:
        user_clinic = request.user.profile.clinic
    except:
        messages.error(request, 'Your account is not linked to any clinic.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.clinic = user_clinic
            followup.created_by = request.user
            followup.save()
            messages.success(request, f'Follow-up for {followup.patient_name} created successfully!')
            return redirect('dashboard')
    else:
        form = FollowUpForm()
    
    context = {
        'form': form,
        'title': 'Create Follow-up',
        'button_text': 'Create',
    }
    return render(request, 'followups/followup_form.html', context)


@login_required
def edit_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    
    try:
        user_clinic = request.user.profile.clinic
        if followup.clinic != user_clinic:
            return HttpResponseForbidden("You don't have permission to edit this follow-up.")
    except:
        messages.error(request, 'Your account is not linked to any clinic.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FollowUpForm(request.POST, instance=followup)
        if form.is_valid():
            form.save()
            messages.success(request, f'Follow-up for {followup.patient_name} updated successfully!')
            return redirect('dashboard')
    else:
        form = FollowUpForm(instance=followup)
    
    context = {
        'form': form,
        'followup': followup,
        'title': 'Edit Follow-up',
        'button_text': 'Update',
    }
    return render(request, 'followups/followup_form.html', context)


@login_required
@require_http_methods(["POST"])
def mark_done(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    
    try:
        user_clinic = request.user.profile.clinic
        if followup.clinic != user_clinic:
            return HttpResponseForbidden("You don't have permission to modify this follow-up.")
    except:
        messages.error(request, 'Your account is not linked to any clinic.')
        return redirect('dashboard')
    
    followup.status = 'done'
    followup.save()
    messages.success(request, f'Follow-up for {followup.patient_name} marked as done!')
    return redirect('dashboard')


def public_view(request, token):
    followup = get_object_or_404(FollowUp, public_token=token)
    
    PublicViewLog.objects.create(
        followup=followup,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    instructions = {
        'en': {
            'title': 'Follow-up Appointment Reminder',
            'greeting': f'Hello {followup.patient_name},',
            'message': f'This is a reminder for your follow-up appointment scheduled on {followup.due_date.strftime("%B %d, %Y")}.',
            'status': 'Status',
            'clinic': 'Clinic',
            'contact': 'For any queries, please contact the clinic.',
        },
        'hi': {
            'title': 'फॉलो-अप अपॉइंटमेंट रिमाइंडर',
            'greeting': f'नमस्ते {followup.patient_name},',
            'message': f'यह आपकी {followup.due_date.strftime("%d %B, %Y")} को निर्धारित फॉलो-अप अपॉइंटमेंट की याद दिलाने के लिए है।',
            'status': 'स्थिति',
            'clinic': 'क्लिनिक',
            'contact': 'किसी भी प्रश्न के लिए, कृपया क्लिनिक से संपर्क करें।',
        }
    }
    
    lang = followup.language
    context = {
        'followup': followup,
        'instructions': instructions.get(lang, instructions['en']),
    }
    return render(request, 'followups/public_view.html', context)