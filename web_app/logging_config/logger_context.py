from contextvars import ContextVar  # Import ContextVar for context-local (thread-safe) storage
from functools import wraps         # Import wraps to preserve function metadata in decorators
from web_app.logging_config.logger_config import CustomLogger  # Import CustomLogger for logger configuration and instantiation

class ContextLogger:
    _logger_instance = None  # Class-level variable to hold the singleton logger instance
    _context_logger = ContextVar('context_logger', default=None)  # ContextVar for binding logger per request/thread

    @staticmethod
    def inject_logger(func):
        """
        Decorator to bind the logger into ContextVar for the duration of a request.
        This allows logger access in any function called within the request context,
        without modifying the function signature.
        """
        @wraps(func)  # Preserve original function metadata (name, docstring, etc.)
        def wrapper(*args, **kwargs):
            # Initialize the singleton logger instance if it doesn't exist
            if ContextLogger._logger_instance is None:
                ContextLogger._logger_instance = CustomLogger().get_logger()
            # Bind the logger to the context for this request/thread
            token = ContextLogger._context_logger.set(ContextLogger._logger_instance)
            try:
                # Call the original function (e.g., Flask view)
                return func(*args, **kwargs)
            finally:
                # Reset the context to avoid logger leakage across requests/threads
                ContextLogger._context_logger.reset(token)
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
                cls._logger_instance = YAMLLogger().get_logger()
            logger = cls._logger_instance  # Use singleton logger as fallback
        return logger  # Return
