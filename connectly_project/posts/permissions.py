"""
Custom permissions for Role-Based Access Control (RBAC).

This module defines permission classes that enforce:
- Role-based restrictions (admin, moderator, user)
- Privacy settings for posts
- Ownership-based access control
"""

from rest_framework.permissions import BasePermission
from posts.models import Follow


class IsAdmin(BasePermission):
    """
    Permission class that only allows admin users.
    
    Use this for sensitive operations like:
    - Deleting any post or comment
    - Managing user roles
    - Accessing admin-only endpoints
    """
    message = "Admin access required."

    def has_permission(self, request, view):
        """Check if request user is an admin."""
        user = getattr(request, 'connectly_user', None)
        if user is None:
            return False
        return user.is_admin()


class IsModeratorOrAbove(BasePermission):
    """
    Permission class that allows moderators and admins.
    
    Use this for moderation operations like:
    - Editing any post or comment
    - Viewing reported content
    """
    message = "Moderator or admin access required."

    def has_permission(self, request, view):
        """Check if request user is a moderator or admin."""
        user = getattr(request, 'connectly_user', None)
        if user is None:
            return False
        return user.is_moderator_or_above()


class IsPostAuthorOrAdmin(BasePermission):
    """
    Permission class for post operations.
    
    - Read access: Everyone (respecting privacy settings)
    - Write/Delete access: Post author or admin only
    """
    message = "You do not have permission to modify this post."

    def has_object_permission(self, request, view, obj):
        """Check if user can modify the post."""
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        user = getattr(request, 'connectly_user', None)
        if user is None:
            return False
        
        # Admins can modify any post
        if user.is_admin():
            return True
        
        # Authors can modify their own posts
        return obj.author_id == user.id


class IsCommentAuthorOrAdmin(BasePermission):
    """
    Permission class for comment operations.
    
    - Read access: Everyone
    - Write/Delete access: Comment author, post author, or admin
    """
    message = "You do not have permission to modify this comment."

    def has_object_permission(self, request, view, obj):
        """Check if user can modify the comment."""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        user = getattr(request, 'connectly_user', None)
        if user is None:
            return False
        
        # Admins can modify any comment
        if user.is_admin():
            return True
        
        # Moderators can delete comments
        if user.is_moderator() and request.method == 'DELETE':
            return True
        
        # Comment author can modify their own comment
        if obj.author_id == user.id:
            return True
        
        # Post author can delete comments on their post
        if request.method == 'DELETE' and obj.post.author_id == user.id:
            return True
        
        return False


class CanViewPost(BasePermission):
    """
    Permission class that enforces post privacy settings.
    
    Privacy levels:
    - public: Anyone can view
    - private: Only owner and admins
    - friends_only: Owner, followers, and admins
    """
    message = "You do not have permission to view this post."

    def has_object_permission(self, request, view, obj):
        """Check if user can view the post based on privacy settings."""
        user = getattr(request, 'connectly_user', None)
        return obj.is_visible_to(user)