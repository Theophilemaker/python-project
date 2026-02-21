from functools import wraps
from flask import flash, redirect, url_for, session
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('⛔ Access Denied! Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_key):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login first.', 'error')
                return redirect(url_for('login'))
            
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            if not current_user.has_permission(permission_key):
                flash('⛔ You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def branch_filter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin' and current_user.branch_id:
            # Add branch filter to session
            session['branch_filter'] = current_user.branch_id
        return f(*args, **kwargs)
    return decorated_function