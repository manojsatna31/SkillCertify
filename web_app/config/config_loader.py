import os
import yaml

class ConfigLoader:
    """
    Loads application configuration from YAML based on the current environment (APP_ENV).
    Provides clean access to configs as attributes.
    """
    def __init__(self, config_file=None):
        # Always load application.yaml from the same directory as this file
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'application.yaml')
        self.env = os.getenv('APP_ENV', 'DEV').upper()  # Auto-detect ENV (fallback to DEV)
        with open(config_file, 'r') as f:
            self.config_data = yaml.safe_load(f)

        self.default_config = self.config_data.get('default', {})
        self.env_config = self.config_data.get('environments', {}).get(self.env, {})

        self.merged_config = self._merge_configs(self.default_config, self.env_config)

    def _merge_configs(self, default_config, env_config):
        """
        Merges environment-specific config into default config (env overrides default).
        Supports nested dictionaries.
        """
        merged = default_config.copy()
        for key, value in env_config.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def get(self, key, default=None):
        """
        Get config value by key. Supports nested keys via dot notation (e.g., 'EXAM_TIME_LIMITS.easy')
        """
        keys = key.split('.')
        value = self.merged_config
        for k in keys:
            value = value.get(k)
            if value is None:
                return default
        return value

    def __getattr__(self, name):
        """
        Allows attribute-style access to configs.
        Example: config.SECRET_KEY
        """
        return self.merged_config.get(name)

# Singleton-like usage
config = ConfigLoader()
