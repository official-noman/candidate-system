from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Candidate(models.Model):
    # Role Linking (Optional, for Candidate Login)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidate_profile')

    # Basic Info
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    age = models.IntegerField(null=True, blank=True)
    experience_years = models.IntegerField(default=0)
    
    # JSON Field for Experience (Institute: Position)
    previous_experience = models.JSONField(default=dict, blank=True)
    
    # Workflow Status
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('scheduled', 'Interview Scheduled'),
        ('passed', 'Passed (1st Round)'),
        ('rejected', 'Rejected'),
        ('second_round', 'Second Interview Scheduled'),
        ('hired', 'Hired'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='applied')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

class Interview(models.Model):
    INTERVIEW_TYPES = [
        ('1st', 'First Interview'),
        ('2nd', 'Second Interview'),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    interview_date = models.DateTimeField()
    interview_type = models.CharField(max_length=10, choices=INTERVIEW_TYPES, default='1st')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    def __str__(self):
        return f"{self.candidate.name} - {self.interview_date}"