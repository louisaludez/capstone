from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.exceptions import PermissionDenied

def role_required(*required_roles):
    """Restrict access to users whose `request.user.role` matches one of required_roles.

    Usage:
        @role_required('staff')
        @role_required('staff', 'SUPER_ADMIN')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            if user_role is not None and user_role in required_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
