"""
TURBO-CDI v7.0 Error Handling Framework
Custom exceptions for the Meta-Prime Engine
"""


class TurboCDIError(Exception):
    """Base exception for all TURBO-CDI errors"""
    pass


class InvalidC4StateError(TurboCDIError):
    """Raised when an invalid C4 state is provided"""
    pass


class DomainNotFoundError(TurboCDIError):
    """Raised when a domain profile cannot be found"""
    pass


class NavigationError(TurboCDIError):
    """Raised when navigation between C4 states fails"""
    pass


class ValidationError(TurboCDIError):
    """Raised when transformation validation fails"""
    pass
