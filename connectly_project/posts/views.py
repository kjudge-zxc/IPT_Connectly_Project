"""
Views for the Connectly Posts API.

Handles post CRUD operations, comments, likes, and news feed.
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
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory

# Initialize singletons
logger = LoggerSingleton().get_logger()
config = ConfigManager()


class PostListCreate(APIView):
    """
    API endpoint for post management.
    
    GET: Retrieve a list of all posts.
    POST: Create a new post (use /posts/create/ for Factory Pattern creation).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all posts."""
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new post."""
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """
    API endpoint for single post operations.
    
    GET: Retrieve a specific post by ID.
    PUT: Update a post (author only).
    DELETE: Delete a post (author only).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return a specific post."""
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post)
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        """Update a specific post."""
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post)
            serializer = PostSerializer(post, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """Delete a specific post."""
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post)
            post.delete()
            return Response({"message": "Post deleted."}, status=status.HTTP_204_NO_CONTENT)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)


class CreatePostView(APIView):
    """
    Create posts using the Factory Pattern.
    
    POST: Create a new post with type-specific validation.
    Demonstrates Factory design pattern usage.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a post using PostFactory."""
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
            
            logger.info(f"Post created successfully with ID: {post.id}")
            
            return Response({
                'message': 'Post created successfully!',
                'post_id': post.id,
                'post_type': post.post_type
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            logger.error(f"Post creation failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    """
    API endpoint for comment management.
    
    GET: Retrieve a list of all comments.
    POST: Create a new comment on a post.
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


class PostLikeView(APIView):
    """
    API endpoint for liking posts.
    
    POST: Like a post. Requires user ID in request body.
    Prevents duplicate likes using unique_together constraint.
    Uses LoggerSingleton to track like activity.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Like a post."""
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

        like, created = Like.objects.get_or_create(user=user, post=post)

        if created:
            logger.info(f"{user.username} liked post {post.id}")
            return Response({"message": "Post liked successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "You already liked this post."}, status=status.HTTP_200_OK)


class PostCommentCreateView(APIView):
    """
    API endpoint for adding comments to a specific post.
    
    POST: Create a comment on the specified post.
    Requires user ID and text in request body.
    Uses LoggerSingleton to track comment activity.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Add a comment to a post."""
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

        comment = Comment.objects.create(
            text=text,
            author=user,
            post=post
        )

        logger.info(f"{user.username} commented on post {post.id}")

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostCommentsListView(APIView):
    """
    API endpoint for retrieving comments on a post.
    
    GET: Retrieve all comments for a specific post, sorted by newest first.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return all comments for a post."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        comments = Comment.objects.filter(post=post).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FeedView(APIView):
    """
    News Feed endpoint.
    
    GET /feed/ - Get paginated posts sorted by date (newest first)
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of posts per page (default from ConfigManager Singleton)
    - user_id: Filter posts by a specific user (optional)
    - feed_type: Type of feed - 'all', 'following', 'liked' (default: 'all')
    
    Uses ConfigManager Singleton for DEFAULT_PAGE_SIZE setting.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return paginated news feed."""
        # Get query parameters (uses ConfigManager Singleton for default page size)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', config.get_setting('DEFAULT_PAGE_SIZE'))
        user_id = request.query_params.get('user_id')
        feed_type = request.query_params.get('feed_type', 'all')

        # Limit page_size to max 50
        try:
            page_size = min(int(page_size), 50)
        except (ValueError, TypeError):
            page_size = config.get_setting('DEFAULT_PAGE_SIZE')

        # Base queryset - all posts sorted by newest first
        posts = Post.objects.all().order_by('-created_at')

        # Apply filters based on feed_type
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

        elif user_id:
            posts = posts.filter(author_id=user_id)

        # Optimize query - preload related data
        posts = posts.select_related('author').prefetch_related('comments', 'likes')

        # Paginate results
        paginator = Paginator(posts, page_size)

        try:
            paginated_posts = paginator.page(page)
        except PageNotAnInteger:
            paginated_posts = paginator.page(1)
        except EmptyPage:
            paginated_posts = paginator.page(paginator.num_pages)

        serializer = PostSerializer(paginated_posts, many=True)

        response_data = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': paginated_posts.number,
            'page_size': page_size,
            'has_next': paginated_posts.has_next(),
            'has_previous': paginated_posts.has_previous(),
            'results': serializer.data
        }

        logger.info(f"Feed retrieved: page {paginated_posts.number}/{paginator.num_pages}, {paginator.count} total posts")

        return Response(response_data, status=status.HTTP_200_OK)


class ConfigView(APIView):
    """
    View to check and update configuration settings.
    
    Demonstrates Singleton pattern usage with ConfigManager.
    GET: Retrieve all configuration settings.
    POST: Update a configuration setting.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return all configuration settings from Singleton."""
        return Response({
            'settings': config.settings
        })
    
    def post(self, request):
        """Update a configuration setting in Singleton."""
        key = request.data.get('key')
        value = request.data.get('value')
        
        if key:
            config.set_setting(key, value)
            logger.info(f"Config updated: {key} = {value}")
            return Response({
                'message': f'Setting {key} updated successfully',
                'settings': config.settings
            })
        return Response({'error': 'Key is required'}, status=status.HTTP_400_BAD_REQUEST)


class ProtectedView(APIView):
    """
    Protected endpoint requiring token authentication.
    
    GET: Returns success message if user is authenticated.
    Used to verify token-based authentication is working.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return success if authenticated."""
        return Response({"message": "Authenticated!"})