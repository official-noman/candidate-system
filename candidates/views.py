"""
Candidate Management System - Views Module

Author: Noman Mahmud
Last Updated: 2026-01-27
"""

import logging
import re
from typing import Optional

import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CandidateForm, ExcelUploadForm, ScheduleForm
from .models import Candidate, Interview

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# ACCESS CONTROL & DECORATORS
# ============================================================================

def is_admin(user: User) -> bool:
    """
    Check if user has admin privileges.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is superuser, False otherwise
    """
    return user.is_authenticated and user.is_superuser


def is_staff(user: User) -> bool:
    """
    Check if user has staff privileges.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is staff or superuser, False otherwise
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ============================================================================
# DASHBOARD VIEW
# ============================================================================

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """
    Main dashboard view with role-based content.
    
    - Candidates see their application status
    - Staff/Admin see system statistics and interview lists
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered dashboard template
    """
    try:
        # Candidate view - show only their profile
        if not is_staff(request.user):
            profile = Candidate.objects.filter(user=request.user).select_related('user').first()
            
            if not profile:
                logger.warning(f"No profile found for user: {request.user.username}")
                messages.warning(
                    request,
                    "No candidate profile found. Please contact HR if you believe this is an error."
                )
            
            return render(request, 'candidates/candidate_status.html', {
                'profile': profile
            })
        
        # Staff/Admin view - show statistics and lists
        context = {
            'total_candidates': Candidate.objects.count(),
            'hired_count': Candidate.objects.filter(status='hired').count(),
            'rejected_count': Candidate.objects.filter(status='rejected').count(),
            'upcoming_count': Interview.objects.filter(status='upcoming').count(),
            'upcoming_interviews': Interview.objects.filter(
                status='upcoming'
            ).select_related('candidate').order_by('interview_date')[:5],
            'completed_interviews': Interview.objects.filter(
                status='completed'
            ).select_related('candidate').order_by('-interview_date')[:5],
        }
        
        logger.info(f"Dashboard accessed by staff user: {request.user.username}")
        return render(request, 'candidates/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error for user {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading the dashboard. Please try again.")
        return render(request, 'candidates/dashboard.html', {})


# ============================================================================
# EXCEL UPLOAD & BULK IMPORT
# ============================================================================

@login_required
@user_passes_test(is_staff, login_url='/login/')
@require_http_methods(["GET", "POST"])
def upload_excel(request: HttpRequest) -> HttpResponse:
    """
    Upload and process Excel file containing candidate data.
    
    Creates User accounts and Candidate profiles from Excel data.
    Phone numbers are cleaned (digits only) for password creation.
    
    Expected Excel columns:
        - Name: Full name
        - Email: Email address (required, unique)
        - Phone: Phone number (any format)
        - Age: Age (optional)
        - Experience (Years): Years of experience (optional)
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Upload form or redirect to candidate list
    """
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['file'])
                
                # Validate required columns
                required_columns = ['Name', 'Email', 'Phone']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    messages.error(
                        request,
                        f"Missing required columns: {', '.join(missing_columns)}"
                    )
                    return render(request, 'candidates/upload.html', {'form': form})
                
                success_count = 0
                error_count = 0
                errors = []
                
                with transaction.atomic():
                    for index, row in df.iterrows():
                        try:
                            # Clean and validate email
                            email = str(row.get('Email', '')).strip().lower()
                            if not email or email == 'nan':
                                error_count += 1
                                errors.append(f"Row {index + 2}: Missing email")
                                continue
                            
                            # Clean phone number
                            raw_phone = str(row.get('Phone', '')).strip()
                            cleaned_phone = re.sub(r'\D', '', raw_phone)
                            
                            if not cleaned_phone:
                                error_count += 1
                                errors.append(f"Row {index + 2}: Missing phone number")
                                continue
                            
                            # Extract name
                            name = str(row.get('Name', 'Unknown')).strip()
                            if name == 'nan':
                                name = 'Unknown'
                            
                            # Create or update user
                            user, created = User.objects.get_or_create(
                                username=email,
                                defaults={
                                    'email': email,
                                    'first_name': name.split()[0] if name != 'Unknown' else 'Unknown',
                                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                                }
                            )
                            
                            # Set password (cleaned phone digits)
                            user.set_password(cleaned_phone)
                            user.save()
                            
                            # Create or update candidate profile
                            Candidate.objects.update_or_create(
                                email=email,
                                defaults={
                                    'user': user,
                                    'name': name,
                                    'phone': raw_phone,  # Store original format for display
                                    'age': int(row.get('Age')) if pd.notna(row.get('Age')) else None,
                                    'experience_years': int(row.get('Experience (Years)', 0)) if pd.notna(row.get('Experience (Years)')) else 0,
                                    'status': 'applied'
                                }
                            )
                            
                            success_count += 1
                            
                        except Exception as row_error:
                            error_count += 1
                            errors.append(f"Row {index + 2}: {str(row_error)}")
                            logger.error(f"Error processing row {index + 2}: {str(row_error)}")
                
                # Show results
                if success_count > 0:
                    messages.success(
                        request,
                        f"Successfully imported {success_count} candidate(s)."
                    )
                    logger.info(f"Excel upload: {success_count} candidates imported by {request.user.username}")
                
                if error_count > 0:
                    messages.warning(
                        request,
                        f"Failed to import {error_count} row(s). Check logs for details."
                    )
                    # Show first 5 errors
                    for error in errors[:5]:
                        messages.error(request, error)
                
                return redirect('candidate_list', status_filter='all')
                
            except Exception as e:
                logger.error(f"Excel upload error: {str(e)}", exc_info=True)
                messages.error(
                    request,
                    f"Error processing file: {str(e)}. Please check file format and try again."
                )
        else:
            messages.error(request, "Invalid form submission. Please check the file and try again.")
    
    else:
        form = ExcelUploadForm()
    
    return render(request, 'candidates/upload.html', {'form': form})


# ============================================================================
# CANDIDATE LIST & FILTERING
# ============================================================================

@login_required
@user_passes_test(is_staff, login_url='/login/')
def candidate_list(request: HttpRequest, status_filter: str) -> HttpResponse:
    """
    Display filtered list of candidates.
    
    Args:
        request: HTTP request object
        status_filter: Filter by status ('all', 'hired', 'rejected', 'passed', etc.)
        
    Returns:
        HttpResponse: Rendered candidate list template
    """
    valid_filters = ['all', 'hired', 'rejected', 'passed', 'applied', 'scheduled', 'second_round']
    
    if status_filter not in valid_filters:
        logger.warning(f"Invalid filter attempted: {status_filter}")
        status_filter = 'all'
    
    try:
        if status_filter == 'all':
            candidates = Candidate.objects.all().select_related('user').order_by('-id')
        else:
            candidates = Candidate.objects.filter(
                status=status_filter
            ).select_related('user').order_by('-id')
        
        # Add search functionality
        search_query = request.GET.get('search', '').strip()
        if search_query:
            candidates = candidates.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        context = {
            'candidates': candidates,
            'filter': status_filter,
            'search_query': search_query,
            'total_count': candidates.count()
        }
        
        return render(request, 'candidates/candidate_list.html', context)
        
    except Exception as e:
        logger.error(f"Candidate list error: {str(e)}", exc_info=True)
        messages.error(request, "Error loading candidate list.")
        return render(request, 'candidates/candidate_list.html', {
            'candidates': [],
            'filter': status_filter
        })


# ============================================================================
# INTERVIEW SCHEDULING
# ============================================================================

@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_http_methods(["GET", "POST"])
def schedule_interview(request: HttpRequest) -> HttpResponse:
    """
    Schedule interviews for candidates.
    
    Supports:
        - Individual selection (checkboxes)
        - Range selection (e.g., "1-10")
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Schedule form or redirect to upcoming interviews
    """
    candidates = Candidate.objects.filter(status='applied').order_by('id')
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        selected_ids = request.POST.getlist('candidate_ids')
        range_input = request.POST.get('range_input', '').strip()
        
        if form.is_valid():
            interview_date = form.cleaned_data['interview_date']
            targets = []
            
            try:
                # Range-based selection
                if range_input:
                    try:
                        start, end = map(int, range_input.split('-'))
                        
                        if start < 1 or end < start:
                            raise ValueError("Invalid range")
                        
                        targets = Candidate.objects.filter(
                            id__range=(start, end),
                            status='applied'
                        )
                        
                        if not targets.exists():
                            messages.warning(request, f"No candidates found in range {start}-{end}")
                            return redirect('schedule_interview')
                    
                    except ValueError:
                        messages.error(request, "Invalid range format. Use format: 1-10")
                        return redirect('schedule_interview')
                
                # Individual selection
                elif selected_ids:
                    targets = Candidate.objects.filter(
                        id__in=selected_ids,
                        status='applied'
                    )
                    
                    if not targets.exists():
                        messages.warning(request, "Selected candidates are not available for scheduling")
                        return redirect('schedule_interview')
                
                else:
                    messages.warning(request, "Please select candidates or specify a range")
                    return redirect('schedule_interview')
                
                # Schedule interviews
                if targets:
                    with transaction.atomic():
                        scheduled_count = 0
                        
                        for candidate in targets:
                            candidate.status = 'scheduled'
                            candidate.save()
                            
                            Interview.objects.create(
                                candidate=candidate,
                                interview_date=interview_date,
                                status='upcoming'
                            )
                            
                            scheduled_count += 1
                        
                        messages.success(
                            request,
                            f"Successfully scheduled {scheduled_count} interview(s) for {interview_date.strftime('%B %d, %Y at %I:%M %p')}"
                        )
                        
                        logger.info(
                            f"Interviews scheduled: {scheduled_count} candidates by {request.user.username}"
                        )
                        
                        return redirect('upcoming_interviews')
            
            except Exception as e:
                logger.error(f"Interview scheduling error: {str(e)}", exc_info=True)
                messages.error(request, "Error scheduling interviews. Please try again.")
                return redirect('schedule_interview')
        
        else:
            messages.error(request, "Invalid form data. Please check the date and try again.")
    
    else:
        form = ScheduleForm()
    
    context = {
        'candidates': candidates,
        'form': form,
        'total_candidates': candidates.count()
    }
    
    return render(request, 'candidates/schedule.html', context)


# ============================================================================
# INTERVIEW MANAGEMENT
# ============================================================================

@login_required
@user_passes_test(is_staff, login_url='/login/')
def upcoming_interviews(request: HttpRequest) -> HttpResponse:
    """
    Display list of upcoming interviews.
    
    Automatically moves past interviews to 'completed' status.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered upcoming interviews template
    """
    try:
        now = timezone.now()
        
        # Auto-move past interviews to completed
        updated_count = Interview.objects.filter(
            interview_date__lt=now,
            status='upcoming'
        ).update(status='completed')
        
        if updated_count > 0:
            logger.info(f"Auto-moved {updated_count} interviews to completed status")
        
        # Get upcoming interviews
        interviews = Interview.objects.filter(
            status='upcoming'
        ).select_related('candidate').order_by('interview_date')
        
        context = {
            'interviews': interviews,
            'total_count': interviews.count()
        }
        
        return render(request, 'candidates/upcoming.html', context)
        
    except Exception as e:
        logger.error(f"Upcoming interviews error: {str(e)}", exc_info=True)
        messages.error(request, "Error loading upcoming interviews.")
        return render(request, 'candidates/upcoming.html', {'interviews': []})


@login_required
@user_passes_test(is_staff, login_url='/login/')
def download_phones(request: HttpRequest) -> HttpResponse:
    """
    Download phone numbers of candidates with upcoming interviews.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Text file with phone numbers
    """
    try:
        upcoming = Interview.objects.filter(
            status='upcoming'
        ).select_related('candidate')
        
        phones = "\n".join([
            str(interview.candidate.phone)
            for interview in upcoming
            if interview.candidate.phone
        ])
        
        response = HttpResponse(phones, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="upcoming_interview_phones.txt"'
        
        logger.info(f"Phone list downloaded by {request.user.username}")
        
        return response
        
    except Exception as e:
        logger.error(f"Phone download error: {str(e)}", exc_info=True)
        messages.error(request, "Error downloading phone numbers.")
        return redirect('upcoming_interviews')


@login_required
@user_passes_test(is_staff, login_url='/login/')
def completed_interviews(request: HttpRequest) -> HttpResponse:
    """
    Display completed interviews categorized by candidate status.
    
    Categories:
        - Pending: Awaiting decision
        - Passed: Moved to next round or hired
        - Rejected: Not selected
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered completed interviews template
    """
    try:
        now = timezone.now()
        
        # Auto-move past interviews
        Interview.objects.filter(
            interview_date__lt=now,
            status='upcoming'
        ).update(status='completed')
        
        # Get completed interviews
        base_qs = Interview.objects.filter(
            status='completed'
        ).select_related('candidate').order_by('-interview_date')
        
        context = {
            'pending_list': base_qs.filter(
                candidate__status__in=['scheduled', 'applied']
            ),
            'passed_list': base_qs.filter(
                candidate__status__in=['passed', 'second_round', 'hired']
            ),
            'rejected_list': base_qs.filter(
                candidate__status='rejected'
            ),
        }
        
        return render(request, 'candidates/completed.html', context)
        
    except Exception as e:
        logger.error(f"Completed interviews error: {str(e)}", exc_info=True)
        messages.error(request, "Error loading completed interviews.")
        return render(request, 'candidates/completed.html', {})


@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_POST
def mark_interview(request: HttpRequest, interview_id: int, action: str) -> HttpResponse:
    """
    Mark interview result (passed/rejected).
    
    Args:
        request: HTTP request object
        interview_id: Interview ID
        action: 'passed' or 'rejected'
        
    Returns:
        HttpResponse: Redirect to completed interviews
    """
    try:
        interview = get_object_or_404(Interview, id=interview_id)
        
        if action == 'passed':
            interview.candidate.status = 'passed'
            messages.success(request, f"{interview.candidate.name} marked as PASSED")
        elif action == 'rejected':
            interview.candidate.status = 'rejected'
            messages.success(request, f"{interview.candidate.name} marked as REJECTED")
        else:
            messages.error(request, "Invalid action")
            return redirect('completed_interviews')
        
        interview.candidate.save()
        
        logger.info(
            f"Interview {interview_id} marked as {action} by {request.user.username}"
        )
        
    except Exception as e:
        logger.error(f"Mark interview error: {str(e)}", exc_info=True)
        messages.error(request, "Error updating interview result.")
    
    return redirect('completed_interviews')


# ============================================================================
# SECOND ROUND & HIRING
# ============================================================================

@login_required
@user_passes_test(is_admin, login_url='/login/')
def second_round_list(request: HttpRequest) -> HttpResponse:
    """
    Display candidates who passed first round.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered second round candidates template
    """
    try:
        candidates = Candidate.objects.filter(
            status='passed'
        ).select_related('user').order_by('-id')
        
        context = {
            'candidates': candidates,
            'total_count': candidates.count()
        }
        
        return render(request, 'candidates/second_round.html', context)
        
    except Exception as e:
        logger.error(f"Second round list error: {str(e)}", exc_info=True)
        messages.error(request, "Error loading second round candidates.")
        return render(request, 'candidates/second_round.html', {'candidates': []})


@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_POST
def schedule_second_round(request: HttpRequest, candidate_id: int) -> HttpResponse:
    """
    Schedule second round interview for a candidate.
    
    Args:
        request: HTTP request object
        candidate_id: Candidate ID
        
    Returns:
        HttpResponse: Redirect to upcoming interviews
    """
    try:
        candidate = get_object_or_404(Candidate, id=candidate_id)
        
        # Update status
        candidate.status = 'second_round'
        candidate.save()
        
        # Create interview (2 days from now)
        interview_date = timezone.now() + timezone.timedelta(days=2)
        
        Interview.objects.create(
            candidate=candidate,
            interview_date=interview_date,
            interview_type='2nd',
            status='upcoming'
        )
        
        messages.success(
            request,
            f"Second round scheduled for {candidate.name} on {interview_date.strftime('%B %d, %Y')}"
        )
        
        logger.info(f"Second round scheduled for candidate {candidate_id} by {request.user.username}")
        
    except Exception as e:
        logger.error(f"Second round scheduling error: {str(e)}", exc_info=True)
        messages.error(request, "Error scheduling second round interview.")
    
    return redirect('upcoming_interviews')


@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_POST
def hire_candidate(request: HttpRequest, candidate_id: int) -> HttpResponse:
    """
    Mark candidate as hired.
    
    Args:
        request: HTTP request object
        candidate_id: Candidate ID
        
    Returns:
        HttpResponse: Redirect to hired candidates list
    """
    try:
        candidate = get_object_or_404(Candidate, id=candidate_id)
        candidate.status = 'hired'
        candidate.save()
        
        messages.success(request, f" {candidate.name} has been hired!")
        
        logger.info(f"Candidate {candidate_id} hired by {request.user.username}")
        
    except Exception as e:
        logger.error(f"Hire candidate error: {str(e)}", exc_info=True)
        messages.error(request, "Error hiring candidate.")
    
    return redirect('candidate_list', status_filter='hired')


# ============================================================================
# CRUD OPERATIONS
# ============================================================================

@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_http_methods(["GET", "POST"])
def candidate_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Edit candidate information.
    
    Args:
        request: HTTP request object
        pk: Candidate primary key
        
    Returns:
        HttpResponse: Edit form or redirect to candidate list
    """
    try:
        candidate = get_object_or_404(Candidate, pk=pk)
        
        if request.method == 'POST':
            form = CandidateForm(request.POST, instance=candidate)
            
            if form.is_valid():
                form.save()
                messages.success(request, f"Successfully updated {candidate.name}'s information")
                logger.info(f"Candidate {pk} updated by {request.user.username}")
                return redirect('candidate_list', status_filter='all')
            else:
                messages.error(request, "Invalid data. Please check the form and try again.")
        else:
            form = CandidateForm(instance=candidate)
        
        context = {
            'form': form,
            'candidate': candidate
        }
        
        return render(request, 'candidates/candidate_edit.html', context)
        
    except Exception as e:
        logger.error(f"Candidate edit error: {str(e)}", exc_info=True)
        messages.error(request, "Error editing candidate.")
        return redirect('candidate_list', status_filter='all')


@login_required
@user_passes_test(is_admin, login_url='/login/')
@require_POST
def delete_candidate(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Delete candidate and associated user account.
    
    Args:
        request: HTTP request object
        pk: Candidate primary key
        
    Returns:
        HttpResponse: Redirect to previous page or dashboard
    """
    try:
        candidate = get_object_or_404(Candidate, pk=pk)
        candidate_name = candidate.name
        
        # Delete will cascade to user if configured
        candidate.delete()
        
        messages.success(request, f"Successfully deleted {candidate_name}")
        logger.info(f"Candidate {pk} deleted by {request.user.username}")
        
    except Exception as e:
        logger.error(f"Candidate delete error: {str(e)}", exc_info=True)
        messages.error(request, "Error deleting candidate.")
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ============================================================================
# PUBLIC CANDIDATE STATUS CHECK
# ============================================================================

def check_candidate_status(request: HttpRequest) -> HttpResponse:
    """
    Public endpoint for candidates to check their status.
    
    Authentication via email + phone number (digits only).
    No login required - uses authenticate() to verify credentials.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Redirect to dashboard or login page
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        input_phone = request.POST.get('phone', '').strip()
        
        try:
            # Clean phone number (remove all non-digit characters)
            cleaned_phone = re.sub(r'\D', '', input_phone)
            
            # Validate inputs
            if not email or not cleaned_phone:
                messages.error(
                    request,
                    " Please provide both email and phone number."
                )
                return redirect('login')
            
            # Authenticate user
            user = authenticate(request, username=email, password=cleaned_phone)
            
            if user is not None:
                # Check if user has candidate profile
                if not hasattr(user, 'candidate') and not Candidate.objects.filter(user=user).exists():
                    messages.error(
                        request,
                        " No candidate profile found for this account."
                    )
                    return redirect('login')
                
                # Successful authentication
                auth_login(request, user)
                
                messages.success(
                    request,
                    f" Welcome {user.first_name}! Redirecting to your dashboard..."
                )
                
                logger.info(f"Candidate status check: successful login for {email}")
                
                return redirect('dashboard')
            
            else:
                # Failed authentication
                messages.error(
                    request,
                    " Invalid credentials! Please check your email and phone number. "
                    "Enter phone as digits only (e.g., 12125556789)."
                )
                
                logger.warning(f"Candidate status check: failed login attempt for {email}")
                
                return redirect('login')
        
        except Exception as e:
            logger.error(f"Candidate status check error: {str(e)}", exc_info=True)
            messages.error(
                request,
                "An error occurred. Please try again or contact support."
            )
            return redirect('login')
    
    # GET request - redirect to login
    return redirect('login')