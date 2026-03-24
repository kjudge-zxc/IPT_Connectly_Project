"""
Views for the Connectly Posts API.

Handles post CRUD operations, comments, likes, and news feed
with Role-Based Access Control (RBAC) and privacy settings.

Performance optimizations:
- Query optimization with select_related and prefetch_related
- Caching for feed endpoints
- Standardized pagination
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.db.models import Count, Prefetch

from users.models import User
from .models import Post, Comment, Like, Follow
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsAdmin, IsModeratorOrAbove, IsPostAuthorOrAdmin, CanViewPost
from .cache_utils import (
    get_feed_cache_key, get_cached_feed, set_cached_feed,
    invalidate_feed_cache, invalidate_post_cache, get_cache_stats,
    FEED_CACHE_TIMEOUT
)
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


def get_optimized_posts_queryset():
    """
    Return optimized queryset with related data preloaded.
    
    Query Optimization:
    - select_related: For ForeignKey relationships (single query JOIN)
    - prefetch_related: For reverse ForeignKey/ManyToMany (separate query, but cached)
    - annotate: For aggregations (count of likes, comments)
    
    Returns:
        QuerySet: Optimized Post queryset ordered by creation date
    """
    return Post.objects.select_related(
        'author'  # Preload author data in same query
    ).prefetch_related(
        'likes',      # Preload likes
        'comments',   # Preload comments
        Prefetch(
            'comments',
            queryset=Comment.objects.select_related('author'),
            to_attr='prefetched_comments'
        )
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    ).order_by('-created_at')


class PostListCreate(APIView):
    """
    API endpoint for post management with query optimization.
    
    GET: Retrieve a list of all public posts (optimized).
    POST: Create a new post with optional privacy setting.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all public posts with optimized queries."""
        user = get_user_from_request(request)
        
        # Use optimized queryset
        posts = get_optimized_posts_queryset()
        
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
            
            # Invalidate feed cache when new post is created
            invalidate_feed_cache()
            
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
            # Use select_related for optimized query
            post = Post.objects.select_related('author').prefetch_related(
                'likes', 'comments'
            ).get(pk=pk)
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
            post = Post.objects.select_related('author').get(pk=pk)
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
            
            # Invalidate caches
            invalidate_post_cache(pk)
            invalidate_feed_cache()
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a post (author or admin only)."""
        try:
            post = Post.objects.select_related('author').get(pk=pk)
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
        
        # Invalidate caches
        invalidate_post_cache(pk)
        invalidate_feed_cache()
        
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
            
            # Invalidate feed cache
            invalidate_feed_cache()
            
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
    API endpoint for comment management with query optimization.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all comments with optimized queries."""
        # Use select_related for optimized query
        comments = Comment.objects.select_related('author', 'post').all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new comment."""
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            # Invalidate feed cache (comment counts changed)
            invalidate_feed_cache()
            
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
            # Use select_related for optimized query
            comment = Comment.objects.select_related('author', 'post', 'post__author').get(pk=pk)
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
        
        # Invalidate feed cache
        invalidate_feed_cache()
        
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
            post = Post.objects.select_related('author').get(pk=pk)
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
            
            # Invalidate feed cache (like counts changed)
            invalidate_feed_cache()
            
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
            post = Post.objects.select_related('author').get(pk=pk)
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
        
        # Invalidate feed cache
        invalidate_feed_cache()

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
            post = Post.objects.select_related('author').get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        user = get_user_from_request(request)
        
        # Check if user can view the post
        if not post.is_visible_to(user):
            return Response(
                {"error": "You do not have permission to view this post's comments."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Use select_related for optimized query
        comments = Comment.objects.select_related('author').filter(post=post).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FeedView(APIView):
    """
    News Feed endpoint with caching and privacy filtering.
    
    Features:
    - Caching for feed results
    - Query optimization with select_related/prefetch_related
    - Standardized pagination
    - Privacy-aware filtering
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return paginated news feed with caching and privacy filtering."""
        # Get pagination parameters
        page = int(request.query_params.get('page', 1))
        page_size = request.query_params.get('page_size', config.get_setting('DEFAULT_PAGE_SIZE'))
        user_id = request.query_params.get('user_id')
        feed_type = request.query_params.get('feed_type', 'all')

        try:
            page_size = min(int(page_size), 50)
        except (ValueError, TypeError):
            page_size = config.get_setting('DEFAULT_PAGE_SIZE')

        # Get requesting user for privacy checks
        requesting_user = get_user_from_request(request)

        # Generate cache key
        cache_key = get_feed_cache_key(
            user_id=user_id,
            feed_type=feed_type,
            page=page,
            page_size=page_size
        )

        # Try to get cached response
        cached_data = get_cached_feed(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # Use optimized queryset
        posts = get_optimized_posts_queryset()

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
            'cached': False,
            'results': serializer.data
        }

        # Cache the response
        set_cached_feed(cache_key, response_data, FEED_CACHE_TIMEOUT)

        logger.info(f"Feed retrieved: page {page_num}/{total_pages}, {total_count} visible posts")

        return Response(response_data, status=status.HTTP_200_OK)


class CacheStatsView(APIView):
    """
    Endpoint to check and manage cache statistics.
    
    GET: Return cache status and statistics.
    DELETE: Clear all caches (admin only).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return cache statistics."""
        stats = get_cache_stats()
        return Response({
            'cache_stats': stats,
            'message': 'Cache is active'
        })

    def delete(self, request):
        """Clear all caches (admin only)."""
        user = get_user_from_request(request)
        
        if user is None or not user.is_admin():
            return Response(
                {"error": "Admin access required to clear cache."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        invalidate_feed_cache()
        logger.info(f"Cache cleared by admin {user.username}")
        
        return Response({
            'message': 'All caches cleared successfully'
        })


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