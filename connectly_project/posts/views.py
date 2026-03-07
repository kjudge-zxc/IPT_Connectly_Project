from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Post, Comment, Like, Follow
from .serializers import UserSerializer, PostSerializer, CommentSerializer, LikeSerializer, FollowSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .permissions import IsPostAuthor, IsCommentAuthor
from rest_framework.authentication import TokenAuthentication
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory


# Initialize logger
logger = LoggerSingleton().get_logger()
config = ConfigManager()


class UserListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return Response({"message": "Authentication successful!"})
            else:
                return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class PostDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post)
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
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
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post)
            post.delete()
            return Response({"message": "Post deleted."}, status=status.HTTP_204_NO_CONTENT)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)


class ProtectedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authenticated!"})


class CreatePostView(APIView):
    """Create posts using the Factory Pattern."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
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


class ConfigView(APIView):
    """View to check and update configuration settings (Singleton demo)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all configuration settings."""
        return Response({
            'settings': config.settings
        })
    
    def post(self, request):
        """Update a configuration setting."""
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


class PostLikeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
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
    - page_size: Number of posts per page (default: 10, max: 50)
    - user_id: Filter posts by a specific user (optional)
    - feed_type: Type of feed - 'all', 'following', 'liked' (default: 'all')
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        # Get query parameters
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', config.get_setting('DEFAULT_PAGE_SIZE') or 10)
        user_id = request.query_params.get('user_id')
        feed_type = request.query_params.get('feed_type', 'all')

        # Limit page_size to max 50
        try:
            page_size = min(int(page_size), 50)
        except (ValueError, TypeError):
            page_size = 10

        # Base queryset - all posts sorted by newest first
        posts = Post.objects.all().order_by('-created_at')

        # Apply filters based on feed_type
        if feed_type == 'following' and user_id:
            # Get posts from users that the specified user follows
            try:
                user = User.objects.get(pk=user_id)
                following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
                posts = posts.filter(author_id__in=following_ids)
                logger.info(f"Feed filtered by following for user {user_id}")
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        elif feed_type == 'liked' and user_id:
            # Get posts that the specified user has liked
            try:
                user = User.objects.get(pk=user_id)
                liked_post_ids = Like.objects.filter(user=user).values_list('post_id', flat=True)
                posts = posts.filter(id__in=liked_post_ids)
                logger.info(f"Feed filtered by liked posts for user {user_id}")
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_id:
            # Filter posts by specific author
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

        # Serialize the posts
        serializer = PostSerializer(paginated_posts, many=True)

        # Build response with pagination info
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


class FollowUserView(APIView):
    """
    Follow/Unfollow a user.
    
    POST /users/{id}/follow/ - Follow a user
    DELETE /users/{id}/follow/ - Unfollow a user
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Follow a user."""
        follower_id = request.data.get('follower_id')

        if not follower_id:
            return Response({"error": "follower_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            follower = User.objects.get(pk=follower_id)
        except User.DoesNotExist:
            return Response({"error": "Follower user not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            following = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User to follow not found."}, status=status.HTTP_404_NOT_FOUND)

        if follower == following:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=follower, following=following)

        if created:
            logger.info(f"{follower.username} started following {following.username}")
            return Response({
                "message": f"You are now following {following.username}."
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "message": f"You are already following {following.username}."
            }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Unfollow a user."""
        follower_id = request.data.get('follower_id')

        if not follower_id:
            return Response({"error": "follower_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            follower = User.objects.get(pk=follower_id)
        except User.DoesNotExist:
            return Response({"error": "Follower user not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            following = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User to unfollow not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            follow = Follow.objects.get(follower=follower, following=following)
            follow.delete()
            logger.info(f"{follower.username} unfollowed {following.username}")
            return Response({
                "message": f"You have unfollowed {following.username}."
            }, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            return Response({
                "error": f"You are not following {following.username}."
            }, status=status.HTTP_400_BAD_REQUEST)


class UserFollowersView(APIView):
    """Get a user's followers."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        followers = Follow.objects.filter(following=user).select_related('follower')
        follower_users = [f.follower for f in followers]
        serializer = UserSerializer(follower_users, many=True)

        return Response({
            "user": user.username,
            "followers_count": len(follower_users),
            "followers": serializer.data
        }, status=status.HTTP_200_OK)


class UserFollowingView(APIView):
    """Get users that a user is following."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        following = Follow.objects.filter(follower=user).select_related('following')
        following_users = [f.following for f in following]
        serializer = UserSerializer(following_users, many=True)

        return Response({
            "user": user.username,
            "following_count": len(following_users),
            "following": serializer.data
        }, status=status.HTTP_200_OK)