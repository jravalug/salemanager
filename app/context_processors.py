from datetime import datetime


def inject_now():
    return {"now": datetime.now}


def inject_request():
    """Expose request path and endpoint to templates for active-link detection."""
    try:
        from flask import request

        return {"request_path": request.path, "request_endpoint": request.endpoint}
    except Exception:
        # If request isn't available (e.g., during CLI tasks), return safe defaults
        return {"request_path": None, "request_endpoint": None}
