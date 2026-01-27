from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Link to candidates app URLs
    path('', include('candidates.urls')), 
    
    # Django Built-in Authentication (Login, Logout)
    path('accounts/', include('django.contrib.auth.urls')), 
]

# Serving media files during development (Required for Excel processing)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)