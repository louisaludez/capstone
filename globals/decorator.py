from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import HttpResponseRedirect

def role_required(*required_roles):
    """Restrict access to users whose `request.user.role` matches one of required_roles.
    When SUPER_ADMIN is required, Django is_superuser is also allowed.

    Usage:
        @role_required('staff')
        @role_required('staff', 'SUPER_ADMIN')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            role_upper = str(user_role).upper() if user_role else ''
            # Allow if role matches, or if SUPER_ADMIN required and user is Django superuser
            if user_role is not None and user_role in required_roles:
                return view_func(request, *args, **kwargs)
            if 'SUPER_ADMIN' in required_roles and getattr(request.user, 'is_superuser', False):
                return view_func(request, *args, **kwargs)
            if role_upper == 'SUPER_ADMIN' and 'SUPER_ADMIN' in required_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Restrict access to admin and super_admin users only.
    Redirects to login with error message if not authenticated or wrong role.
    
    Usage:
        @admin_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            login_url = reverse('login')
            return HttpResponseRedirect(f"{login_url}?next={request.path}&error=login_required")
        
        # Check if user is admin or super_admin
        user_role = getattr(request.user, 'role', None)
        is_admin = user_role == 'admin'
        is_super_admin = getattr(request.user, 'is_superuser', False) or (user_role and str(user_role).upper() == 'SUPER_ADMIN')
        
        # Debug logging
        print(f"=== ADMIN ACCESS CHECK ===")
        print(f"User: {request.user.username}")
        print(f"User Role: {user_role}")
        print(f"User Role Type: {type(user_role)}")
        print(f"Is Admin: {is_admin}")
        print(f"Is Super Admin: {is_super_admin}")
        print(f"Is Superuser: {getattr(request.user, 'is_superuser', False)}")
        print(f"========================")
        
        if is_admin or is_super_admin:
            return view_func(request, *args, **kwargs)
        
        # User is authenticated but doesn't have admin privileges
        login_url = reverse('login')
        return HttpResponseRedirect(f"{login_url}?next={request.path}&error=admin_required")
    
    return _wrapped_view
