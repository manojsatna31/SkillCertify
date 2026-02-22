from web_app.logging_config.logger_config import CustomLogger
from web_app.logging_config.logger_proxy import AppLogger as LoggerProxy
from web_app.logging_config.logger_context import ContextLogger


# Proxy Logger Usage
logger = LoggerProxy()

# Decorator for Context Injection
inject_logger = ContextLogger.inject_logger

# Get Logger from Context (Inside Decorated Functions)
get_context_logger = ContextLogger.get_context_logger
