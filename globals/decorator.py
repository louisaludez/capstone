from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.exceptions import PermissionDenied
def role_required(required_role):  
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'role') and request.user.role == required_role:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
