"""
URL configuration for the Users API.

All user-related endpoints including role management.
"""

from django.urls import path
from .views import (
    UserListCreate,
    UserLoginView,
    UserRoleUpdateView,
    FollowUserView,
    UserFollowersView,
    UserFollowingView,
)

urlpatterns = [
    path('', UserListCreate.as_view(), name='user-list-create'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),
    path('<int:pk>/follow/', FollowUserView.as_view(), name='follow-user'),
    path('<int:pk>/followers/', UserFollowersView.as_view(), name='user-followers'),
    path('<int:pk>/following/', UserFollowingView.as_view(), name='user-following'),
]