"""
URL configuration for the Posts API.

Post-related endpoints are defined here.
"""

from django.urls import path
from .views import (
    PostListCreate,
    PostDetailView,
    CreatePostView,
    CommentListCreate,
    PostLikeView,
    PostCommentCreateView,
    PostCommentsListView,
    FeedView,
    ConfigView,
    ProtectedView,
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
    
    # Feed endpoint
    path('feed/', FeedView.as_view(), name='feed'),
    
    # Config endpoint (Singleton demo)
    path('config/', ConfigView.as_view(), name='config'),
    
    # Protected endpoint
    path('protected/', ProtectedView.as_view(), name='protected'),
    
    # Google OAuth endpoints
    path('auth/google/login/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/google/status/', GoogleAuthStatusView.as_view(), name='google-status'),
]