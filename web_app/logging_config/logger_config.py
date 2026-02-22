import logging  # Python's built-in logging module for logging functionality
import os  # Provides access to environment variables and file system paths
import yaml  # Used to parse YAML configuration files
from logging.handlers import RotatingFileHandler  # Handler for rotating log files when they reach a certain size

from web_app.config.config_loader import ConfigLoader

class CustomLogger:
    _logger_instance = None

    def __new__(cls, *args, **kwargs):
        if cls._logger_instance is None:
            cls._logger_instance = super(CustomLogger, cls).__new__(cls)
            cls._logger_instance._initialized = False
        return cls._logger_instance

    def __init__(self):
        if self._initialized:
            return

        # Access configurations from central YAML config
        self.config = ConfigLoader()
        self.env = self.config.env
        self.logger = logging.getLogger(f"AppLogger-{self.env}")

        self._setup_logger()
        self._initialized = True

    def _setup_logger(self):
        log_dir = self.config.log_dir
        os.makedirs(log_dir, exist_ok=True)

        log_file = self.config.get('log_file', os.path.join(log_dir, f"{self.env.lower()}.log"))
        log_format = self.config.log_format
        formatter = logging.Formatter(log_format)

        # Console Handler (if enabled)
        if self.config.get('enable_console', False):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_level = self.config.get('console_level', 'INFO')
            console_handler.setLevel(getattr(logging, str(console_level).upper()))
            self.logger.addHandler(console_handler)

        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count
        )
        file_handler.setFormatter(formatter)
        file_level = self.config.get('file_level', 'INFO')
        file_handler.setLevel(getattr(logging, str(file_level).upper()))
        self.logger.addHandler(file_handler)

        # Set Logger Level to DEBUG to capture all logs (Handlers will filter)
        self.logger.setLevel(logging.DEBUG)

    def get_logger(self):
        return self.logger
