"""
Serializers for the Users API.

Handles conversion between User model instances and JSON data.
"""

from rest_framework import serializers
from .models import User


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