from rest_framework.permissions import BasePermission


class IsPostAuthor(BasePermission):
    """Only allow authors to edit/delete their own posts."""
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only for everyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Write permissions only for author
        return obj.author == request.user


class IsCommentAuthor(BasePermission):
    """Only allow authors to edit/delete their own comments."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.author == request.user