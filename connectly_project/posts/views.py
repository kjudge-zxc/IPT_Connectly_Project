from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Post, Comment, Like
from .serializers import UserSerializer, PostSerializer, CommentSerializer, LikeSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .permissions import IsPostAuthor, IsCommentAuthor
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory


# Initialize logger
logger = LoggerSingleton().get_logger()
config = ConfigManager()


class UserListCreate(APIView):
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
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    ## permission_classes = [AllowAny] ## For testing

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
    permission_classes = [IsAuthenticatedOrReadOnly, IsPostAuthor]

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
            self.check_object_permissions(request, post)  # Check if user is author
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
            self.check_object_permissions(request, post)  # Check if user is author
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
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]  # Change to IsAuthenticated for production

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
    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        comments = Comment.objects.filter(post=post).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)