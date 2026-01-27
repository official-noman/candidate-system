from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Link to candidates app URLs
    path('', include('candidates.urls')), 
    
    # Django Built-in Authentication (Login, Logout)
    path('accounts/', include('django.contrib.auth.urls')), 
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='home'),
]

# Serving media files during development (Required for Excel processing)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)