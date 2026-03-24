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
    Role field defaults to 'user' for new registrations.
    """
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.CharField(read_only=True)  # Role cannot be set via API by default

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'created_at']

    def create(self, validated_data):
        """Create a new user with hashed password and default role."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user roles (admin only).
    
    Only allows updating the role field.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'role']
        read_only_fields = ['id', 'username']

    def validate_role(self, value):
        """Validate that role is a valid choice."""
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Invalid role. Must be one of: {valid_roles}")
        return value