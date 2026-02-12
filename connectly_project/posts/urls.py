from django.urls import path
from .views import PostDetailView, ProtectedView, UserListCreate, PostListCreate, CommentListCreate, UserLoginView


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('users/login/', UserLoginView.as_view(), name='user-login'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('protected/', ProtectedView.as_view(), name='protected'),
]
