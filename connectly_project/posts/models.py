"""
Models for the Connectly social media application.

This module defines the core data models:
- User: Custom user model with secure password hashing
- Post: Content posts with support for text, image, and video types
- Comment: User comments on posts
- Like: User likes on posts (unique per user-post pair)
- Follow: User follow relationships
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """
    Custom user model for Connectly.
    
    Uses Django's password hashing utilities (Argon2 by default)
    for secure password storage and verification.
    
    Attributes:
        username: Unique username for the user
        email: Unique email address
        password: Hashed password (never stored in plain text)
        created_at: Timestamp when user was created
    """
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        """Hash and store the password using Argon2 algorithm."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify a plain text password against the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Post(models.Model):
    """
    Content post model supporting multiple post types.
    
    Uses Factory Pattern (see factories/post_factory.py) for creation
    with type-specific validation.
    
    Attributes:
        title: Optional title for the post
        content: Main text content of the post
        post_type: Type of post (text, image, or video)
        metadata: JSON field for type-specific data (e.g., file_size, duration)
        author: Foreign key to the User who created the post
        created_at: Timestamp when post was created
    """
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    metadata = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.content[:50]


class Comment(models.Model):
    """
    Comment model for user responses to posts.
    
    Attributes:
        text: The comment content
        author: Foreign key to the User who wrote the comment
        post: Foreign key to the Post being commented on
        created_at: Timestamp when comment was created
    """
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"


class Like(models.Model):
    """
    Like model for user reactions to posts.
    
    Uses unique_together constraint to prevent duplicate likes
    from the same user on the same post.
    
    Attributes:
        user: Foreign key to the User who liked the post
        post: Foreign key to the Post being liked
        created_at: Timestamp when like was created
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"


class Follow(models.Model):
    """
    Follow model for user-to-user relationships.
    
    Enables the "following" feed feature where users can see
    posts from users they follow.
    
    Attributes:
        follower: The User who is following
        following: The User being followed
        created_at: Timestamp when follow relationship was created
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"