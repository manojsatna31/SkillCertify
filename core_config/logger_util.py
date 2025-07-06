# logger_util.py
import logging
import logging.config

import yaml


class LoggerUtility:
    _is_configured = False

    @classmethod
    def configure(cls, config_path=None):
        if not cls._is_configured:
            if config_path is None:
                # Lazy-load core_config instance only at runtime
                from core_config import Config
                config_path = Config().LOGGING_CONFIG_YML

            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                logging.config.dictConfig(config)
                cls._is_configured = True

    @classmethod
    def get_logger(cls, name='universalLogger'):
        cls.configure()
        return logging.getLogger(name)
