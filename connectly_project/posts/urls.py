"""
URL configuration for the Posts API.

Post-related endpoints with RBAC support and caching.
"""

from django.urls import path
from .views import (
    PostListCreate,
    PostDetailView,
    CreatePostView,
    CommentListCreate,
    CommentDeleteView,
    PostLikeView,
    PostCommentCreateView,
    PostCommentsListView,
    FeedView,
    ConfigView,
    ProtectedView,
    CacheStatsView,
)
from .google_auth import GoogleLoginView, GoogleAuthStatusView

urlpatterns = [
    # Post endpoints
    path('', PostListCreate.as_view(), name='post-list-create'),
    path('create/', CreatePostView.as_view(), name='create-post'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:pk>/like/', PostLikeView.as_view(), name='post-like'),
    path('<int:pk>/comment/', PostCommentCreateView.as_view(), name='post-comment'),
    path('<int:pk>/comments/', PostCommentsListView.as_view(), name='post-comments'),
    
    # Comment endpoints
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDeleteView.as_view(), name='comment-delete'),
    
    # Feed endpoint
    path('feed/', FeedView.as_view(), name='feed'),
    
    # Cache management endpoint
    path('cache/stats/', CacheStatsView.as_view(), name='cache-stats'),
    
    # Config endpoint (admin only for POST)
    path('config/', ConfigView.as_view(), name='config'),
    
    # Protected endpoint
    path('protected/', ProtectedView.as_view(), name='protected'),
    
    # Google OAuth endpoints
    path('auth/google/login/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/google/status/', GoogleAuthStatusView.as_view(), name='google-status'),
]