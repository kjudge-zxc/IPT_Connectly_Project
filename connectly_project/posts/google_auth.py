from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from singletons.logger_singleton import LoggerSingleton

logger = LoggerSingleton().get_logger()


@method_decorator(csrf_exempt, name='dispatch')
class GoogleLoginView(SocialLoginView):
    """
    Google OAuth2 Login View.
    
    POST /auth/google/login/
    Body: {"access_token": "google_access_token_here"}
    """
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8000/auth/google/callback/"
    client_class = OAuth2Client
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        logger.info("Google OAuth login attempt")
        try:
            response = super().post(request, *args, **kwargs)
            logger.info("Google OAuth login successful")
            return response
        except Exception as e:
            logger.error(f"Google OAuth login failed: {str(e)}")
            return Response(
                {"error": "Google authentication failed", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class GoogleAuthStatusView(APIView):
    """
    Check if Google OAuth is configured.
    
    GET /auth/google/status/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            "google_oauth_enabled": True,
            "message": "Google OAuth is configured. Use POST /auth/google/login/ with access_token to authenticate."
        })