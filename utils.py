from functools import wraps
from flask import flash, redirect, url_for, session

def requires_role(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user_role = session.get('role')

            # Check if the user role is None or not in roles
            if user_role is None:
                return 'access denied'  # Or handle it as you see fit
            
            if user_role in roles:
                return view_func(*args, **kwargs)
            else:
                return 'access denied'

        return wrapped_view

    return decorator
