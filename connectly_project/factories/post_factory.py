"""
Post Factory Pattern Implementation.

Provides a factory method for creating different types of posts
with type-specific validation rules.

Usage:
    from factories.post_factory import PostFactory
    post = PostFactory.create_post(
        author=user,
        post_type='image',
        title='My Photo',
        content='Check this out!',
        metadata={'file_size': 1024}
    )
"""

from posts.models import Post


class PostFactory:
    """
    Factory class for creating Post instances.
    
    Implements the Factory design pattern to centralize post creation
    logic and enforce type-specific validation rules.
    """
    
    @staticmethod
    def create_post(author, post_type, title='', content='', metadata=None):
        """
        Create a new post with type-specific validation.
        
        Args:
            author: User instance who is creating the post
            post_type: Type of post ('text', 'image', or 'video')
            title: Optional title for the post
            content: Main text content of the post
            metadata: Dictionary with type-specific data
                     - image posts require 'file_size'
                     - video posts require 'duration'
        
        Returns:
            Post: The created Post instance
            
        Raises:
            ValueError: If post_type is invalid or required metadata is missing
        """
        if metadata is None:
            metadata = {}

        # Validate post type against allowed choices
        valid_types = [choice[0] for choice in Post.POST_TYPES]
        if post_type not in valid_types:
            raise ValueError(f"Invalid post type. Must be one of: {valid_types}")

        # Validate type-specific metadata requirements
        if post_type == 'image' and 'file_size' not in metadata:
            raise ValueError("Image posts require 'file_size' in metadata")
        if post_type == 'video' and 'duration' not in metadata:
            raise ValueError("Video posts require 'duration' in metadata")

        return Post.objects.create(
            author=author,
            title=title,
            content=content,
            post_type=post_type,
            metadata=metadata
        )