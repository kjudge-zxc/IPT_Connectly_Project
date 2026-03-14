"""
Serializers for the Connectly API.

Serializers handle conversion between Django model instances
and JSON data for API requests/responses.
"""

from rest_framework import serializers
from .models import User, Post, Comment, Like, Follow


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Handles user creation with secure password hashing.
    Password field is write-only (never returned in responses).
    """
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'created_at']

    def create(self, validated_data):
        """Create a new user with hashed password."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model.
    
    Includes computed fields for like_count and comment_count
    to avoid additional API calls for this common data.
    """
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'post_type', 'metadata', 'author', 'created_at', 'comments', 'like_count', 'comment_count']

    def get_like_count(self, obj):
        """Return the total number of likes on this post."""
        return obj.likes.count()

    def get_comment_count(self, obj):
        """Return the total number of comments on this post."""
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    
    Includes validation to ensure post and author exist,
    and that comment text is not empty.
    """
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'post', 'created_at']

    def validate_post(self, value):
        """Validate that the post exists."""
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Post not found.")
        return value

    def validate_author(self, value):
        """Validate that the author exists."""
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Author not found.")
        return value

    def validate_text(self, value):
        """Validate that comment text is not empty."""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Comment text cannot be empty.")
        return value


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for Like model.
    
    Includes validation to prevent duplicate likes
    (same user liking the same post twice).
    """
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']

    def validate(self, data):
        """Prevent duplicate likes from the same user on the same post."""
        if Like.objects.filter(user=data['user'], post=data['post']).exists():
            raise serializers.ValidationError("You have already liked this post.")
        return data


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for Follow model.
    
    Includes readable usernames for both follower and following users.
    Validates that users cannot follow themselves or duplicate follows.
    """
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_username', 'following', 'following_username', 'created_at']

    def validate(self, data):
        """Prevent self-following and duplicate follow relationships."""
        if data['follower'] == data['following']:
            raise serializers.ValidationError("You cannot follow yourself.")
        if Follow.objects.filter(follower=data['follower'], following=data['following']).exists():
            raise serializers.ValidationError("You are already following this user.")
        return data