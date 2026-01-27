from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Candidate(models.Model):
    """Model representing a job candidate in the recruitment system."""
    
    # Relationships
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidate_profile',
        help_text=_("Associated user account for candidate portal access")
    )

    # Basic Information
    name = models.CharField(_("Full Name"), max_length=255, db_index=True)
    email = models.EmailField(_("Email Address"), unique=True, db_index=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        _("Phone Number"),
        validators=[phone_regex],
        max_length=17
    )
    age = models.PositiveIntegerField(
        _("Age"),
        null=True,
        blank=True,
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    experience_years = models.PositiveIntegerField(
        _("Years of Experience"),
        default=0,
        validators=[MaxValueValidator(50)]
    )
    
    # Experience Details
    previous_experience = models.JSONField(
        _("Previous Experience"),
        default=dict,
        blank=True,
        help_text=_("JSON structure: {'institute_name': 'position'}")
    )
    
    # Workflow Status
    class Status(models.TextChoices):
        APPLIED = 'applied', _('Applied')
        SCHEDULED = 'scheduled', _('Interview Scheduled')
        PASSED = 'passed', _('Passed (1st Round)')
        REJECTED = 'rejected', _('Rejected')
        SECOND_ROUND = 'second_round', _('Second Interview Scheduled')
        HIRED = 'hired', _('Hired')
    
    status = models.CharField(
        _("Application Status"),
        max_length=50,
        choices=Status.choices,
        default=Status.APPLIED,
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def __repr__(self):
        return f"<Candidate: {self.name} - {self.email}>"


class Interview(models.Model):
    """Model representing an interview session for a candidate."""
    
    class InterviewType(models.TextChoices):
        FIRST = '1st', _('First Interview')
        SECOND = '2nd', _('Second Interview')
    
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', _('Upcoming')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    # Relationships
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name=_("Candidate")
    )
    
    # Interview Details
    interview_date = models.DateTimeField(_("Interview Date & Time"), db_index=True)
    interview_type = models.CharField(
        _("Interview Type"),
        max_length=10,
        choices=InterviewType.choices,
        default=InterviewType.FIRST
    )
    status = models.CharField(
        _("Interview Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.UPCOMING,
        db_index=True
    )
    notes = models.TextField(_("Interview Notes"), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        ordering = ['-interview_date']
        verbose_name = _("Interview")
        verbose_name_plural = _("Interviews")
        indexes = [
            models.Index(fields=['candidate', 'interview_date']),
            models.Index(fields=['status', 'interview_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'interview_date', 'interview_type'],
                name='unique_candidate_interview'
            )
        ]

    def __str__(self):
        return f"{self.candidate.name} - {self.get_interview_type_display()} on {self.interview_date.strftime('%Y-%m-%d %H:%M')}"

    def __repr__(self):
        return f"<Interview: {self.candidate.name} - {self.interview_type} - {self.status}>"

