import logging
import sys
from typing import Optional

class FractoRustFormatter(logging.Formatter):
    """
    Custom SQL-style formatter for FractoRust-AI industrial logs.
    Uses ANSI escape sequences to match the Cyberpunk palette.
    """
    # Cyberpunk Palette:
    # Rust Orange: #FF5F00 -> rgb(255, 95, 0)
    # Neon Cyan: #00F2FF -> rgb(0, 242, 255)
    # Industrial Gray: #666666 (Readable gray for terminals)
    
    RUST_ORANGE = "\033[38;2;255;95;0m"
    NEON_CYAN = "\033[38;2;0;242;255m"
    INDUSTRIAL_GRAY = "\033[38;2;102;102;102m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    LEVEL_COLORS = {
        logging.DEBUG: INDUSTRIAL_GRAY,
        logging.INFO: NEON_CYAN,
        logging.WARNING: RUST_ORANGE,
        logging.ERROR: RUST_ORANGE + BOLD,
        logging.CRITICAL: RUST_ORANGE + BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record with custom colors based on the severity level.
        
        Args:
            record (logging.LogRecord): The log record to be formatted.
            
        Returns:
            str: The formatted and colorized log string.
        """
        log_color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        formatter = logging.Formatter(f"{log_color}{self.FORMAT}{self.RESET}")
        return formatter.format(record)


def setup_logging(level: Optional[int] = logging.INFO) -> None:
    """
    Configures the root logger with the FractoRust custom formatter.
    
    Args:
        level (Optional[int]): The minimum logging level to capture.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler configuration
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FractoRustFormatter())
    
    # Avoid duplicate handlers if setup is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Utility function to create and return a logger instance for a specific module.
    
    Args:
        name (str): The name of the module (usually __name__).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)