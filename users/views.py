from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

from .models import User, UserType
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserTypeSerializer
)
from activities.services.activity_logger import ActivityLogger


# Helper function for getting client IP
def get_client_ip(request):
    """Get client IP address for logging"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Custom Token View with Email Login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # LOGGING: Login activity
        if response.status_code == 200:
            # Successful login
            user_email = request.data.get('email', 'unknown')
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                user = None

            ActivityLogger.log_user_authentication(
                user=user,
                house=None,
                action='login',
                result={
                    'success': True,
                    'user_id': str(user.id) if user else None,
                },
                email=user_email,
                source='api',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        else:
            # Failed login
            user_email = request.data.get('email', 'unknown')
            ActivityLogger.log_user_authentication(
                user=None,
                house=None,
                action='login_failed',
                result={
                    'success': False,
                    'error_message': 'Invalid credentials',
                },
                email=user_email,
                source='api',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                log_level='warning'
            )

        return response

    def get_client_ip(self, request):
        """Get client IP address for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# User Registration
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    User registration endpoint
    """
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # LOGGING: Registration activity
        ActivityLogger.log_user_authentication(
            user=user,
            house=None,
            action='registration',
            result={
                'success': True,
                'user_id': str(user.id),
            },
            email=user.email,
            source='api',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_201_CREATED)

    # LOGGING: Failed registration
    ActivityLogger.log_user_authentication(
        user=None,
        house=None,
        action='registration_failed',
        result={
            'success': False,
            'error_message': 'Validation failed',
        },
        email=request.data.get('email', 'unknown'),
        source='api',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        log_level='warning'
    )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get User Profile
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# Update User Profile
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update user profile
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get All User Types
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_types(request):
    """
    Get all user types (for admin/registration)
    """
    user_types = UserType.objects.all()
    serializer = UserTypeSerializer(user_types, many=True)
    return Response(serializer.data)


# OPTIONAL: Additional endpoints you had (keep if you want them)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not request.user.check_password(old_password):
        ActivityLogger.log_user_authentication(
            user=request.user,
            house=None,
            action='password_change_failed',
            result={'success': False, 'error_message': 'Old password incorrect'},
            source='api',
            ip_address=get_client_ip(request),
            log_level='warning'
        )
        return Response({'error': 'Old password is incorrect'}, status=400)

    request.user.set_password(new_password)
    request.user.save()

    ActivityLogger.log_user_authentication(
        user=request.user,
        house=None,
        action='password_change',
        result={'success': True, 'message': 'Password changed successfully'},
        source='api',
        ip_address=get_client_ip(request)
    )

    return Response({'message': 'Password changed successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user
    """
    ActivityLogger.log_user_authentication(
        user=request.user,
        house=None,
        action='logout',
        result={'success': True, 'message': 'User logged out'},
        source='api',
        ip_address=get_client_ip(request)
    )

    return Response({'message': 'Logged out successfully'})




# ============================================
# SUPERUSER CREATION ENDPOINT (DEPLOYMENT)
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def create_superuser_endpoint(request):
    """
    Create a superuser via API endpoint.
    
    Secured by DEPLOYMENT_TOKEN environment variable.
    
    Request body:
    {
        "token": "your-deployment-token",
        "email": "admin@example.com",
        "password": "securepAssWORD123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    """
    import os
    
    # Get deployment token from environment
    deployment_token = os.environ.get('DEPLOYMENT_TOKEN', '')
    
    if not deployment_token:
        return Response(
            {'error': 'Deployment token not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Verify token
    provided_token = request.data.get('token', '')
    if not provided_token or provided_token != deployment_token:
        return Response(
            {'error': 'Invalid or missing deployment token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Extract and validate data
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()
    first_name = request.data.get('first_name', 'Admin').strip()
    last_name = request.data.get('last_name', 'User').strip()
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if superuser exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'message': f'Superuser "{email}" already exists'},
                status=status.HTTP_200_OK
            )
        
        # Create superuser
        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return Response(
            {
                'message': '✅ Superuser created successfully',
                'email': email
            },
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return Response(
            {'error': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )