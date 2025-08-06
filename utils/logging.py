import logging
import os

LOG_FILE = "application.log"

def setup_logging():
    """
    Sets up the application's logging configuration.
    Logs to both console and a file.
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, LOG_FILE)

    logging.basicConfig(
        level=logging.INFO, # Default logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path), # Log to file
            logging.StreamHandler() # Log to console
        ]
    )
    # Silence overly verbose loggers from libraries if needed
    logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

    logging.info("Logging setup complete.")

def get_logger(name: str):
    """
    Returns a logger instance for a specific module.
    """
    return logging.getLogger(name)