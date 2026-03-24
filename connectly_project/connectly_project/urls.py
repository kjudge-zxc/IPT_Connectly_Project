"""
URL configuration for connectly_project.

Routes are organized by app:
- /users/ - User management endpoints (users app)
- /posts/ - Post and feed endpoints (posts app)
- /auth/ - Authentication endpoints (dj-rest-auth)
"""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),  # DRF login/logout
    
    # App URLs
    path('users/', include('users.urls')),              # Users app URLs
    path('posts/', include('posts.urls')),              # Posts app URLs
    
    # Auth endpoints
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/social/', include('allauth.socialaccount.urls')),
]