from functools import wraps
from db import db, cursor
from flask import  flash, redirect, url_for, flash
from flask import  session 

def requires_role(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):

            if session.get('role') in roles:
                return view_func(*args, **kwargs)
            else:
                #flash('You are not authorized to access vehicle details','danger')
                #return redirect(url_for('auth.dashboard'))
                return 'access denied'
        return wrapped_view

    return decorator




