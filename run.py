# SkillCertify/run.py

"""
Application Entry Point
-----------------------
Supports optional CLI overrides for environment and port.
Falls back to .env configuration when arguments are not provided.
Launches the Flask app using application factory pattern.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

def main():
    # Step 1: Load .env early
    basedir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(basedir, '.env'))
    sys.path.append(basedir)

    # Step 2: Parse optional CLI arguments
    parser = argparse.ArgumentParser(description="SkillCertify Web Application")
    parser.add_argument('--env', type=str, help="Environment (e.g. development, staging, production)")
    parser.add_argument('--port', type=int, help="Port to run the app on")
    args = parser.parse_args()

    try:
        # Step 3: Load Config and Logger
        from core_config import Config
        from core_config.logger_util import LoggerUtility

        config = Config()
        LoggerUtility.configure(config_path=config.LOGGING_CONFIG_YML)
        logger = LoggerUtility.get_logger(__name__)
        logger.info("Logging initialized")

        # Step 4: Determine effective env and port
        effective_env = args.env or os.environ.get("FLASK_ENV", "production")
        effective_port = args.port or int(os.environ.get("FLASK_PORT", "5000"))

        logger.info(f"Environment: {effective_env}")
        logger.info(f"Application is running on port {effective_port}")

        # Step 5: Create app and run
        from skillcertify_web_app import create_web_app
        app = create_web_app()

        if __name__ == '__main__':
            app.run(host="0.0.0.0", port=effective_port)

    except Exception as e:
        logging.basicConfig(level=logging.ERROR)
        logging.error("Startup failure", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()