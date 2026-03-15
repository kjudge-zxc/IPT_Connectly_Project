"""
User model for the Connectly social media application.

This module defines the User model with secure password hashing.
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """
    Custom user model for Connectly.
    
    Uses Django's password hashing utilities (Argon2/PBKDF2)
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

    class Meta:
        db_table = 'posts_user'  # Keep the same table name to avoid migration issues

    def set_password(self, raw_password):
        """Hash and store the password using configured algorithm."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify a plain text password against the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username