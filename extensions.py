"""
Flask extension singletons — imported by routes that need access to shared
extension objects (e.g. csrf) without circular imports.
"""
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
