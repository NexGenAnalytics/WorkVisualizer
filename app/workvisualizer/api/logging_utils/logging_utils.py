# logging_utils.py
import logging
from logging import handlers
import threading
import time
from functools import wraps
from contextlib import contextmanager

# Thread-local storage to keep track of call depth
thread_local = threading.local()

# Global variable to store current log level
current_log_level = logging.INFO


def setup_logging(log_level=logging.INFO):
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler("../app.log", maxBytes=10 ** 6, backupCount=3)
    file_handler.setFormatter(log_formatter)

    # Logger setup
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Set up the logger
logger = setup_logging()


@contextmanager
def log_call_depth():
    if not hasattr(thread_local, "depth"):
        thread_local.depth = 0

    thread_local.depth += 1
    try:
        yield
    finally:
        thread_local.depth -= 1


def get_call_depth():
    return getattr(thread_local, "depth", 0)


def log_with_depth(message, level=logging.INFO):
    depth = get_call_depth()
    indent = " " * (depth * 2)  # 2 spaces per depth level
    logger.log(level, f"{indent}{message}")


def log_timed():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with log_call_depth():
                start_time = time.time()
                log_with_depth(f"Entering {func.__name__}", current_log_level)

                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    log_with_depth(f"Exception in {func.__name__}: {e}", logging.ERROR)
                    raise
                finally:
                    elapsed_time = time.time() - start_time
                    log_with_depth(f"Exiting {func.__name__} (Elapsed Time: {elapsed_time:.4f} secs)",
                                   current_log_level)

                return result

        return wrapper

    return decorator


def set_log_level(log_level: str):
    global current_log_level
    log_level = log_level.upper()
    valid_log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    if log_level in valid_log_levels:
        current_log_level = valid_log_levels[log_level]
        logger.setLevel(current_log_level)
        log_with_depth(f"Log level set to {log_level}", logging.INFO)
        return f"Log level set to {log_level}"
    else:
        raise ValueError("Invalid log level")
