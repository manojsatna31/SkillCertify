from web_app.logging_config.logger_config import CustomLogger  # Correct absolute import

class AppLogger:
    _logger_instance = None  # Class-level variable to hold the singleton logger instance

    def __init__(self):
        # Initialize the singleton logger instance if it doesn't exist yet
        if AppLogger._logger_instance is None:
            AppLogger._logger_instance = CustomLogger().get_logger()  # Create and configure the logger

    def __getattr__(self, name):
        # Proxy attribute access to the underlying logger instance
        # Allows calls like logger.info(...) to be forwarded to the real logger
        return getattr(AppLogger._logger_instance, name)
