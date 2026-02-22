# app_logger.py

from logger_config import CustomLogger  # Import the custom logger configuration class
from contextvars import ContextVar  # Import ContextVar for context-local storage (thread-safe)
from functools import wraps  # Import wraps to preserve function metadata in decorators

class AppLogger:
    """
    Unified Logger Utility for the application.
    Features:
    - Proxy Pattern: Use AppLogger as a drop-in logger (e.g., logger.info(...))
    - ContextVar-based injection: Allows logger access in Flask routes without passing as a parameter
    """
    _logger_instance = None  # Class-level singleton logger instance (shared across app)
    _context_logger = ContextVar('context_logger', default=None)  # ContextVar for binding logger per request/thread

    def __init__(self):
        # Initialize the singleton logger instance if it doesn't exist
        if AppLogger._logger_instance is None:
            AppLogger._logger_instance = CustomLogger().get_logger()

    def __getattr__(self, name):
        """
        Proxy attribute access to the underlying logger instance.
        Allows calls like logger.info(...) to be forwarded to the real logger.
        """
        return getattr(AppLogger._logger_instance, name)

    @staticmethod
    def inject_logger(func):
        """
        Decorator to bind the logger into ContextVar for the duration of a request.
        This allows logger access in any function called within the request context,
        without modifying the function signature.
        """

        @wraps(func)  # Preserve original function metadata
        def wrapper(*args, **kwargs):
            # Ensure the singleton logger is initialized
            if AppLogger._logger_instance is None:
                AppLogger._logger_instance = CustomLogger().get_logger()

            # Bind the logger to the context for this request/thread
            token = AppLogger._context_logger.set(AppLogger._logger_instance)

            try:
                # Call the original function (e.g., Flask view)
                return func(*args, **kwargs)
            finally:
                # Reset the context to avoid logger leakage across requests/threads
                AppLogger._context_logger.reset(token)

        return wrapper  # Return the decorated function

    @classmethod
    def get_context_logger(cls):
        """
        Retrieve the logger bound in the current context (request scope).
        If not set, fallback to the singleton logger instance.
        """
        logger = cls._context_logger.get()  # Get logger from context variable
        if logger is None:
            # If not set, initialize the singleton logger if needed
            if cls._logger_instance is None:
                cls._logger_instance = CustomLogger().get_logger()
            logger = cls._logger_instance  # Use singleton logger as fallback
        return logger  # Return the logger instance
