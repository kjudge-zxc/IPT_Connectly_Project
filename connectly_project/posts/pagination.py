"""
Custom pagination classes for the Connectly API.

This module provides pagination classes for standardized
API responses with detailed pagination metadata.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination for list endpoints.
    
    Features:
    - Configurable page size via query parameter
    - Maximum page size limit for performance
    - Detailed pagination metadata in response
    
    Attributes:
        page_size: Default number of items per page (20)
        page_size_query_param: Query parameter to customize page size
        max_page_size: Maximum allowed page size (50)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        """
        Return pagination metadata with results.
        
        Returns:
            Response with count, total_pages, current_page,
            page_size, navigation flags, and results.
        """
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'has_next': self.page.has_next(),
            'has_previous': self.page.has_previous(),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class FeedPagination(PageNumberPagination):
    """
    Pagination specifically for the news feed endpoint.
    
    Uses ConfigManager settings as defaults and provides
    feed-specific pagination response format.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        """Return feed-specific pagination response."""
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'has_next': self.page.has_next(),
            'has_previous': self.page.has_previous(),
            'results': data
        })