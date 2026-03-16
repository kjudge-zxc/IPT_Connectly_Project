"""
Models for the Connectly posts and interactions.

This module defines:
- Post: Content posts with privacy settings and multiple post types
- Comment: User comments on posts
- Like: User likes on posts (unique per user-post pair)
- Follow: User follow relationships
"""

from django.db import models
from users.models import User


class Post(models.Model):
    """
    Content post model with privacy settings and multiple post types.
    
    Privacy Settings:
    - public: Visible to everyone
    - private: Visible only to the post owner (and admins)
    - friends_only: Visible to followers of the post owner (and admins)
    
    Attributes:
        title: Optional title for the post
        content: Main text content of the post
        post_type: Type of post (text, image, or video)
        privacy: Privacy setting (public, private, friends_only)
        metadata: JSON field for type-specific data
        author: Foreign key to the User who created the post
        created_at: Timestamp when post was created
    """
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends_only', 'Friends Only'),
    ]

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    metadata = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_visible_to(self, user):
        """
        Check if this post is visible to the given user.
        
        Args:
            user: User instance or None (for anonymous users)
            
        Returns:
            bool: True if user can view this post
        """
        # Public posts are visible to everyone
        if self.privacy == 'public':
            return True
        
        # No user provided (anonymous) - can only see public posts
        if user is None:
            return False
        
        # Admins can see everything
        if user.is_admin():
            return True
        
        # Post owner can always see their own posts
        if self.author_id == user.id:
            return True
        
        # Private posts - only owner and admins
        if self.privacy == 'private':
            return False
        
        # Friends only - check if user follows the post author
        if self.privacy == 'friends_only':
            return Follow.objects.filter(follower=user, following=self.author).exists()
        
        return False

    def __str__(self):
        return f"{self.title or self.content[:50]} ({self.privacy})"


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