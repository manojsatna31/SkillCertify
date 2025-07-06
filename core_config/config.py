import os
from dotenv import load_dotenv
import logging


# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
bootstrap_logger = logging.getLogger("bootstrap")
bootstrap_logger.setLevel(logging.WARNING)
if not bootstrap_logger.hasHandlers():
    bootstrap_logger.addHandler(logging.StreamHandler())



class Config:
    """Application configuration manager with logger-aware environment validation."""

    def __init__(self):
        self.LOGGING_CONFIG_YML = self.get_env('LOGGING_CONFIG_YML',default='./core_config/logging/logging_dev.yml',required=True)
        # General Config
        self.FLASK_ENV = self.get_env('FLASK_ENV', default='production', required=True)
        self.SECRET_KEY = self.get_env('SECRET_KEY', required=True)
        self.FLASK_PORT = self.get_env('FLASK_PORT', default='5000')

        # Enable template auto-reloading for development
        self.TEMPLATES_AUTO_RELOAD = True

        # Directory paths
        self.QB_SOURCE_DIR = self.get_env('QB_SOURCE_DIR', default='data', required=True)

        # Manifest file
        self.QB_MANIFEST_FILE_NAME = self.get_env('QB_MANIFEST_FILE_NAME', default='topics_manifest.json')

        # Logging core_config path
        self.LOGGING_FILE_PATHS = {
            "development": "./core_config/logging/logging_dev.yml",
            "staging": "./core_config/logging/logging_stage.yml",
            "production": "./core_config/logging/logging_prod.yml"
        }
        env_key = self.get_env('ENV', default='development')
        self.LOGGING_CONFIG_YML = self.LOGGING_FILE_PATHS.get(env_key)

        bootstrap_logger.info("Configuration initialized successfully.")

    def get_env(self, var_name: str, default: str = None, required: bool = False) -> str:
        """Retrieve environment variable and log fallback if default is used."""
        value = os.environ.get(var_name)

        if value is None or value.strip() == "":
            if default is not None:
                bootstrap_logger.warning(f"Env variable '{var_name}' missing. Defaulting to: '{default}'")
                return default
            elif required:
                raise EnvironmentError(f"Missing required env variable: '{var_name}' and no default was provided.")
            else:
                return ""
        return value