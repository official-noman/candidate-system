# candidates/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # মেইন ড্যাশবোর্ড (অ্যাডমিন/স্টাফ/ক্যান্ডিডেট সবার জন্য এন্ট্রি পয়েন্ট)
    path('', views.dashboard, name='dashboard'),

    # ক্যান্ডিডেট স্ট্যাটাস চেক (লগইন ছাড়া এক্সেসযোগ্য)
    path('check-status/', views.check_candidate_status, name='check_candidate_status'),

    # এক্সেল আপলোড
    path('upload/', views.upload_excel, name='upload_excel'),

    # ক্যান্ডিডেট লিস্ট এবং ফিল্টার
    path('candidates/<str:status_filter>/', views.candidate_list, name='candidate_list'),

    # ইন্টারভিউ ম্যানেজমেন্ট
    path('schedule/', views.schedule_interview, name='schedule_interview'),
    path('interviews/upcoming/', views.upcoming_interviews, name='upcoming_interviews'),
    path('interviews/completed/', views.completed_interviews, name='completed_interviews'),
    
    # রেজাল্ট আপডেট
    path('mark/<int:interview_id>/<str:action>/', views.mark_interview, name='mark_interview'),
    path('download-phones/', views.download_phones, name='download_phones'),

    # সেকেন্ড রাউন্ড এবং হায়ার
    path('second-round/', views.second_round_list, name='second_round_list'),
    path('schedule-second/<int:candidate_id>/', views.schedule_second_round, name='schedule_second'),
    path('hire/<int:candidate_id>/', views.hire_candidate, name='hire_candidate'),

    # CRUD অপারেশন
    path('delete/<int:pk>/', views.delete_candidate, name='delete_candidate'),
    path('candidate/edit/<int:pk>/', views.candidate_edit, name='candidate_edit'),
]