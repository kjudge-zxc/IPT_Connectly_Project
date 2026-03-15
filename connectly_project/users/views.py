"""
Views for the Users API.

Handles user registration, authentication, and follow relationships.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication

from .models import User
from .serializers import UserSerializer
from posts.models import Follow
from singletons.logger_singleton import LoggerSingleton

# Initialize logger
logger = LoggerSingleton().get_logger()


class UserListCreate(APIView):
    """
    API endpoint for user management.
    
    GET: Retrieve a list of all users.
    POST: Create a new user with username, email, and password.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """Return all users."""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new user."""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"New user created: {request.data.get('username')}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API endpoint for user authentication.
    
    POST: Authenticate a user with username and password.
    Returns success message if credentials are valid.
    Uses secure password hashing for verification.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user credentials."""
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                logger.info(f"User {username} authenticated successfully")
                return Response({"message": "Authentication successful!"})
            else:
                logger.warning(f"Failed login attempt for user {username}")
                return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


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
    """
    Get a user's followers.
    
    GET /users/{id}/followers/ - List all followers of a user
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return list of users following the specified user."""
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
    """
    Get users that a user is following.
    
    GET /users/{id}/following/ - List all users the specified user follows
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Return list of users that the specified user is following."""
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