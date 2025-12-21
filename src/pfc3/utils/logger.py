import logging
import sys
from pathlib import Path

def setup_logger(name: str = "PFC3", log_file: str = "logs/pipeline.log", level=logging.INFO):
    """
    Configures a thread-safe logger that outputs to both console and file.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # specific logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Catch everything, handlers filter it

    # Prevent duplicate handlers if function is called multiple times
    if logger.handlers:
        return logger

    # File Handler - Detailed
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Console Handler - Clean
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(message)s') # Just the message for console
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create a default instance
logger = setup_logger()
