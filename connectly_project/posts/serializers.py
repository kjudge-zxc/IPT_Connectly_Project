"""
Serializers for the Connectly Posts API.

Serializers handle conversion between Django model instances
and JSON data for API requests/responses.
"""

from rest_framework import serializers
from users.models import User
from .models import Post, Comment, Like, Follow


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model.
    
    Includes:
    - Privacy settings (public, private, friends_only)
    - Computed fields for like_count and comment_count
    - Author information
    """
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'post_type', 'privacy', 
            'metadata', 'author', 'author_username', 'created_at', 
            'comments', 'like_count', 'comment_count'
        ]

    def get_like_count(self, obj):
        """Return the total number of likes on this post."""
        return obj.likes.count()

    def get_comment_count(self, obj):
        """Return the total number of comments on this post."""
        return obj.comments.count()

    def validate_privacy(self, value):
        """Validate privacy setting."""
        valid_options = [choice[0] for choice in Post.PRIVACY_CHOICES]
        if value not in valid_options:
            raise serializers.ValidationError(f"Invalid privacy setting. Must be one of: {valid_options}")
        return value


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    
    Includes validation to ensure post and author exist,
    and that comment text is not empty.
    """
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'author_username', 'post', 'created_at']

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