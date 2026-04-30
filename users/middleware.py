# users/middleware.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """Get the current user from thread locals"""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """Middleware to capture the current user making the request"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the current user in thread locals
        if hasattr(request, 'user') and request.user.is_authenticated:
            _thread_locals.user = request.user
        else:
            _thread_locals.user = None
        
        response = self.get_response(request)
        
        # Clean up after request
        _thread_locals.user = None
        
        return response