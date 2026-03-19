import logging
import sys

def setup_logging():
    """
    Setup global logging configuration for the project.
    Logs will be output to stdout.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
