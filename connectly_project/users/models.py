"""
User model for the Connectly social media application.

This module defines the User model with secure password hashing
and role-based access control (RBAC).
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """
    Custom user model for Connectly with RBAC support.
    
    Attributes:
        username: Unique username for the user
        email: Unique email address
        password: Hashed password (never stored in plain text)
        role: User role for access control (admin, moderator, user)
        created_at: Timestamp when user was created
    """
    
    # Role choices for RBAC
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('user', 'User'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'posts_user'

    def set_password(self, raw_password):
        """Hash and store the password using configured algorithm."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify a plain text password against the stored hash."""
        return check_password(raw_password, self.password)

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'

    def is_moderator(self):
        """Check if user has moderator role."""
        return self.role == 'moderator'

    def is_moderator_or_above(self):
        """Check if user has moderator or admin role."""
        return self.role in ['admin', 'moderator']

    def __str__(self):
        return f"{self.username} ({self.role})"