# utils/decorators.py

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from flask import jsonify

def login_required(fn):
    """
    Ensures the user has a valid JWT.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    """
    Ensures the user is an admin.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if not identity.get("is_admin"):
            return jsonify({"error": "Admins only"}), 403
        return fn(*args, **kwargs)
    return wrapper
