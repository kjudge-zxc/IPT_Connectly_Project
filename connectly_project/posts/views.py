"""
Views for the Connectly Posts API.

Handles post CRUD operations, comments, likes, and news feed
with Role-Based Access Control (RBAC) and privacy settings.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from users.models import User
from .models import Post, Comment, Like, Follow
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsAdmin, IsModeratorOrAbove, IsPostAuthorOrAdmin, CanViewPost
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory

# Initialize singletons
logger = LoggerSingleton().get_logger()
config = ConfigManager()


def get_user_from_request(request):
    """
    Helper function to get the Connectly user from request.
    
    Checks for user_id in query params or request data.
    Returns None if no valid user found.
    """
    user_id = request.query_params.get('user_id') or request.data.get('user_id')
    if user_id:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    return None


class PostListCreate(APIView):
    """
    API endpoint for post management.
    
    GET: Retrieve a list of all public posts.
    POST: Create a new post with optional privacy setting.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all public posts (privacy-aware)."""
        user = get_user_from_request(request)
        
        # Get all posts
        posts = Post.objects.all().order_by('-created_at')
        
        # Filter based on privacy settings
        visible_posts = [post for post in posts if post.is_visible_to(user)]
        
        serializer = PostSerializer(visible_posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new post with privacy setting."""
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post created with privacy: {request.data.get('privacy', 'public')}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """
    API endpoint for single post operations with RBAC.
    
    GET: Retrieve a post (respects privacy settings).
    PUT: Update a post (author or admin only).
    DELETE: Delete a post (author or admin only).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return a specific post if user has permission to view it."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user = get_user_from_request(request)
        
        # Check privacy permissions
        if not post.is_visible_to(user):
            logger.warning(f"Access denied to post {pk} for user {user}")
            return Response(
                {"error": "You do not have permission to view this post."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update a post (author or admin only)."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user = get_user_from_request(request)
        
        if user is None:
            return Response({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user can modify the post
        if not (user.is_admin() or post.author_id == user.id):
            logger.warning(f"User {user.username} attempted to update post {pk} without permission")
            return Response(
                {"error": "You do not have permission to update this post."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post {pk} updated by {user.username}")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a post (author or admin only)."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user = get_user_from_request(request)
        
        if user is None:
            return Response({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user can delete the post
        if not (user.is_admin() or post.author_id == user.id):
            logger.warning(f"User {user.username} attempted to delete post {pk} without permission")
            return Response(
                {"error": "You do not have permission to delete this post."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.delete()
        logger.info(f"Post {pk} deleted by {user.username} (role: {user.role})")
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_200_OK)


class CreatePostView(APIView):
    """
    Create posts using the Factory Pattern with privacy settings.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a post using PostFactory with privacy setting."""
        data = request.data
        
        logger.info(f"Creating new post of type: {data.get('post_type', 'text')}")
        
        try:
            author_id = data.get('author')
            try:
                author = User.objects.get(pk=author_id)
            except User.DoesNotExist:
                return Response({'error': 'Author not found'}, status=status.HTTP_400_BAD_REQUEST)

            post = PostFactory.create_post(
                author=author,
                post_type=data.get('post_type', 'text'),
                title=data.get('title', ''),
                content=data.get('content', ''),
                metadata=data.get('metadata', {})
            )
            
            # Set privacy setting
            privacy = data.get('privacy', 'public')
            if privacy in ['public', 'private', 'friends_only']:
                post.privacy = privacy
                post.save()
            
            logger.info(f"Post created with ID: {post.id}, privacy: {post.privacy}")
            
            return Response({
                'message': 'Post created successfully!',
                'post_id': post.id,
                'post_type': post.post_type,
                'privacy': post.privacy
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            logger.error(f"Post creation failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    """
    API endpoint for comment management.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all comments."""
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new comment."""
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDeleteView(APIView):
    """
    API endpoint for deleting comments with RBAC.
    
    DELETE: Delete a comment (comment author, post author, moderator, or admin).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        """Delete a comment with role-based permissions."""
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user = get_user_from_request(request)
        
        if user is None:
            return Response({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions: admin, moderator, comment author, or post author
        can_delete = (
            user.is_admin() or
            user.is_moderator() or
            comment.author_id == user.id or
            comment.post.author_id == user.id
        )
        
        if not can_delete:
            logger.warning(f"User {user.username} attempted to delete comment {pk} without permission")
            return Response(
                {"error": "You do not have permission to delete this comment."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
        logger.info(f"Comment {pk} deleted by {user.username} (role: {user.role})")
        return Response({"message": "Comment deleted successfully."}, status=status.HTTP_200_OK)


class PostLikeView(APIView):
    """
    API endpoint for liking posts with privacy enforcement.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Like a post (only if user can view it)."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Like failed: Post {pk} not found")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get("user")
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can view the post before liking
        if not post.is_visible_to(user):
            return Response(
                {"error": "You cannot like a post you don't have access to."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        like, created = Like.objects.get_or_create(user=user, post=post)

        if created:
            logger.info(f"{user.username} liked post {post.id}")
            return Response({"message": "Post liked successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "You already liked this post."}, status=status.HTTP_200_OK)


class PostCommentCreateView(APIView):
    """
    API endpoint for adding comments with privacy enforcement.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Add a comment to a post (only if user can view it)."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Comment failed: Post {pk} not found")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get("user")
        text = request.data.get("text")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not text:
            return Response({"error": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can view the post before commenting
        if not post.is_visible_to(user):
            return Response(
                {"error": "You cannot comment on a post you don't have access to."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        comment = Comment.objects.create(text=text, author=user, post=post)
        logger.info(f"{user.username} commented on post {post.id}")

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostCommentsListView(APIView):
    """
    API endpoint for retrieving comments on a post.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return all comments for a post (if user can view the post)."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        user = get_user_from_request(request)
        
        # Check if user can view the post
        if not post.is_visible_to(user):
            return Response(
                {"error": "You do not have permission to view this post's comments."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        comments = Comment.objects.filter(post=post).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FeedView(APIView):
    """
    News Feed endpoint with privacy filtering.
    
    Only returns posts the user has permission to view based on privacy settings.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return paginated news feed with privacy filtering."""
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', config.get_setting('DEFAULT_PAGE_SIZE'))
        user_id = request.query_params.get('user_id')
        feed_type = request.query_params.get('feed_type', 'all')

        # Get requesting user for privacy checks
        requesting_user = get_user_from_request(request)

        try:
            page_size = min(int(page_size), 50)
        except (ValueError, TypeError):
            page_size = config.get_setting('DEFAULT_PAGE_SIZE')

        # Base queryset
        posts = Post.objects.all().order_by('-created_at')

        # Apply feed_type filters
        if feed_type == 'following' and user_id:
            try:
                user = User.objects.get(pk=user_id)
                following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
                posts = posts.filter(author_id__in=following_ids)
                logger.info(f"Feed filtered by following for user {user_id}")
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        elif feed_type == 'liked' and user_id:
            try:
                user = User.objects.get(pk=user_id)
                liked_post_ids = Like.objects.filter(user=user).values_list('post_id', flat=True)
                posts = posts.filter(id__in=liked_post_ids)
                logger.info(f"Feed filtered by liked posts for user {user_id}")
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Filter posts based on privacy settings
        visible_posts = [post for post in posts if post.is_visible_to(requesting_user)]

        # Manual pagination for filtered list
        total_count = len(visible_posts)
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

        try:
            page_num = int(page)
            if page_num < 1:
                page_num = 1
            elif page_num > total_pages and total_pages > 0:
                page_num = total_pages
        except (ValueError, TypeError):
            page_num = 1

        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        paginated_posts = visible_posts[start_idx:end_idx]

        serializer = PostSerializer(paginated_posts, many=True)

        response_data = {
            'count': total_count,
            'total_pages': total_pages,
            'current_page': page_num,
            'page_size': page_size,
            'has_next': page_num < total_pages,
            'has_previous': page_num > 1,
            'results': serializer.data
        }

        logger.info(f"Feed retrieved: page {page_num}/{total_pages}, {total_count} visible posts")

        return Response(response_data, status=status.HTTP_200_OK)


class ConfigView(APIView):
    """
    View to check and update configuration settings.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return all configuration settings from Singleton."""
        return Response({'settings': config.settings})
    
    def post(self, request):
        """Update a configuration setting in Singleton (admin only)."""
        user = get_user_from_request(request)
        
        # Only admins can update config
        if user is None or not user.is_admin():
            return Response(
                {"error": "Admin access required to update configuration."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        key = request.data.get('key')
        value = request.data.get('value')
        
        if key:
            config.set_setting(key, value)
            logger.info(f"Config updated by {user.username}: {key} = {value}")
            return Response({
                'message': f'Setting {key} updated successfully',
                'settings': config.settings
            })
        return Response({'error': 'Key is required'}, status=status.HTTP_400_BAD_REQUEST)


class ProtectedView(APIView):
    """
    Protected endpoint requiring token authentication.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return success if authenticated."""
        return Response({"message": "Authenticated!"})