"""
Django Admin configuration for recruitment application.
Provides enhanced admin interface for Candidate and Interview models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
import json

from .models import Candidate, Interview


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Candidate model with filtering and display options."""
    
    # List Display Configuration
    list_display = (
        'id',
        'name',
        'email',
        'phone',
        'age',
        'experience_years',
        'status_badge',
        'interview_count',
        'display_experience',
        'created_at'
    )
    
    list_display_links = ('id', 'name')
    
    # Filtering and Search
    list_filter = (
        'status',
        'experience_years',
        'created_at',
        'updated_at',
    )
    
    search_fields = (
        'name',
        'email',
        'phone',
        'previous_experience',
    )
    
    # Ordering and Pagination
    ordering = ('-created_at',)
    list_per_page = 25
    
    # Date Hierarchy
    date_hierarchy = 'created_at'
    
    # Readonly Fields
    readonly_fields = (
        'created_at',
        'updated_at',
        'formatted_experience',
    )
    
    # Fieldsets for Organized Form Layout
    fieldsets = (
        (_('Personal Information'), {
            'fields': ('user', 'name', 'email', 'phone', 'age'),
            'classes': ('wide',)
        }),
        (_('Professional Information'), {
            'fields': ('experience_years', 'previous_experience', 'formatted_experience'),
            'classes': ('wide',)
        }),
        (_('Application Status'), {
            'fields': ('status',),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Actions
    actions = [
        'mark_as_scheduled',
        'mark_as_passed',
        'mark_as_rejected',
        'mark_as_hired',
    ]
    
    # Custom Display Methods
    @admin.display(description=_('Status'), ordering='status')
    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'applied': '#6c757d',
            'scheduled': '#0dcaf0',
            'passed': '#198754',
            'rejected': '#dc3545',
            'second_round': '#fd7e14',
            'hired': '#20c997',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description=_('Interviews'))
    def interview_count(self, obj):
        """Display count of interviews with link."""
        count = obj.interviews.count()
        if count > 0:
            url = reverse('admin:recruitment_interview_changelist') + f'?candidate__id__exact={obj.id}'
            return format_html('<a href="{}">{} Interview(s)</a>', url, count)
        return '0'
    
    @admin.display(description=_('Previous Experience'))
    def display_experience(self, obj):
        """Display previous experience in compact format."""
        if not obj.previous_experience:
            return format_html('<em style="color: #6c757d;">No experience data</em>')
        
        try:
            exp_items = []
            for company, position in obj.previous_experience.items():
                exp_items.append(f"{position} @ {company}")
            return format_html('<br>'.join(exp_items))
        except (AttributeError, TypeError):
            return format_html('<em style="color: #dc3545;">Invalid format</em>')
    
    @admin.display(description=_('Experience Details'))
    def formatted_experience(self, obj):
        """Display formatted JSON experience for readonly field."""
        if not obj.previous_experience:
            return _("No experience data")
        try:
            return json.dumps(obj.previous_experience, indent=2)
        except (TypeError, ValueError):
            return _("Invalid JSON format")
    
    # Custom Actions
    @admin.action(description=_('Mark as Interview Scheduled'))
    def mark_as_scheduled(self, request, queryset):
        """Bulk action to mark candidates as scheduled."""
        updated = queryset.update(status='scheduled')
        self.message_user(request, _(f'{updated} candidate(s) marked as scheduled.'))
    
    @admin.action(description=_('Mark as Passed'))
    def mark_as_passed(self, request, queryset):
        """Bulk action to mark candidates as passed."""
        updated = queryset.update(status='passed')
        self.message_user(request, _(f'{updated} candidate(s) marked as passed.'))
    
    @admin.action(description=_('Mark as Rejected'))
    def mark_as_rejected(self, request, queryset):
        """Bulk action to mark candidates as rejected."""
        updated = queryset.update(status='rejected')
        self.message_user(request, _(f'{updated} candidate(s) marked as rejected.'))
    
    @admin.action(description=_('Mark as Hired'))
    def mark_as_hired(self, request, queryset):
        """Bulk action to mark candidates as hired."""
        updated = queryset.update(status='hired')
        self.message_user(request, _(f'{updated} candidate(s) marked as hired.'))
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and annotations."""
        qs = super().get_queryset(request)
        return qs.select_related('user').annotate(
            total_interviews=Count('interviews')
        )


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Interview model with scheduling features."""
    
    # List Display Configuration
    list_display = (
        'id',
        'candidate_link',
        'interview_date',
        'interview_type_badge',
        'status_badge',
        'is_upcoming',
        'notes_preview',
        'created_at'
    )
    
    list_display_links = ('id', 'interview_date')
    
    # Filtering and Search
    list_filter = (
        'status',
        'interview_type',
        'interview_date',
        'created_at',
    )
    
    search_fields = (
        'candidate__name',
        'candidate__email',
        'notes',
    )
    
    # Ordering and Pagination
    ordering = ('-interview_date',)
    list_per_page = 25
    
    # Date Hierarchy
    date_hierarchy = 'interview_date'
    
    # Readonly Fields
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    
    # Autocomplete
    autocomplete_fields = ['candidate']
    
    # Fieldsets
    fieldsets = (
        (_('Interview Details'), {
            'fields': ('candidate', 'interview_date', 'interview_type'),
            'classes': ('wide',)
        }),
        (_('Status & Notes'), {
            'fields': ('status', 'notes'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Actions
    actions = [
        'mark_as_completed',
        'mark_as_cancelled',
    ]
    
    # Custom Display Methods
    @admin.display(description=_('Candidate'), ordering='candidate__name')
    def candidate_link(self, obj):
        """Display candidate name with link to their profile."""
        url = reverse('admin:recruitment_candidate_change', args=[obj.candidate.id])
        return format_html('<a href="{}">{}</a>', url, obj.candidate.name)
    
    @admin.display(description=_('Type'), ordering='interview_type')
    def interview_type_badge(self, obj):
        """Display interview type with badge."""
        colors = {
            '1st': '#0d6efd',
            '2nd': '#6f42c1',
        }
        color = colors.get(obj.interview_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_interview_type_display()
        )
    
    @admin.display(description=_('Status'), ordering='status')
    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'upcoming': '#0dcaf0',
            'completed': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description=_('Timing'), boolean=True)
    def is_upcoming(self, obj):
        """Indicate if interview is in the future."""
        return obj.interview_date > timezone.now()
    
    @admin.display(description=_('Notes Preview'))
    def notes_preview(self, obj):
        """Display truncated notes."""
        if obj.notes:
            preview = obj.notes[:50]
            if len(obj.notes) > 50:
                preview += '...'
            return preview
        return format_html('<em style="color: #6c757d;">No notes</em>')
    
    # Custom Actions
    @admin.action(description=_('Mark as Completed'))
    def mark_as_completed(self, request, queryset):
        """Bulk action to mark interviews as completed."""
        updated = queryset.update(status='completed')
        self.message_user(request, _(f'{updated} interview(s) marked as completed.'))
    
    @admin.action(description=_('Mark as Cancelled'))
    def mark_as_cancelled(self, request, queryset):
        """Bulk action to mark interviews as cancelled."""
        updated = queryset.update(status='cancelled')
        self.message_user(request, _(f'{updated} interview(s) marked as cancelled.'))
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('candidate')

