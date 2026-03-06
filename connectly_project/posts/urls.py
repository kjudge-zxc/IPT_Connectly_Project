from django.urls import path
from .views import (
    PostDetailView, 
    ProtectedView, 
    UserListCreate, 
    PostListCreate, 
    CommentListCreate, 
    UserLoginView,
    CreatePostView,
    ConfigView,
    PostLikeView,
    PostCommentCreateView,
    PostCommentsListView,
)


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('users/login/', UserLoginView.as_view(), name='user-login'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('posts/create/', CreatePostView.as_view(), name='create-post'),
    path('config/', ConfigView.as_view(), name='config'),
    path('posts/<int:pk>/like/', PostLikeView.as_view(), name='post-like'),
    path('posts/<int:pk>/comment/', PostCommentCreateView.as_view(), name='post-comment'),
    path('posts/<int:pk>/comments/', PostCommentsListView.as_view(), name='post-comments'), 
]