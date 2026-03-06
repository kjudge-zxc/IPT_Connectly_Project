from rest_framework import serializers
from .models import User, Post, Comment, Like


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Never return password

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'post_type', 'metadata', 'author', 'created_at', 'comments', 'like_count', 'comment_count']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'post', 'created_at']

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Post not found.")
        return value

    def validate_author(self, value):
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Author not found.")
        return value

    def validate_text(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Comment text cannot be empty.")
        return value

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']

    def validate(self, data):
        """Prevent duplicate likes."""
        if Like.objects.filter(user=data['user'], post=data['post']).exists():
            raise serializers.ValidationError("You have already liked this post.")
        return data
