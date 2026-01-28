
import os
import logging
import datetime
from typing import Optional, Dict, Any, List


class LoggerSetup:
    """Set up and configure logging for the application."""

    def __init__(self, config: Dict[str, Any], args: Optional[Dict[str, Any]] = None):
        """
        Initialize logger setup with configuration.

        Args:
            config: Configuration dictionary with logging settings.
            args: Command line arguments that may influence logging.
        """
        self.args = args or {}
        self.config = config
        self.log_file_path: Optional[str] = None
        self.logger = self._setup_logger()

    def _get_log_level(self) -> int:
        """
        Determine the appropriate logging level.

        Returns:
            int: Logging level constant
        """
        logging_config = self.config.get("logging", {})
        level_str = logging_config.get("level", "INFO").upper()

        # Override with verbose flag if present
        if self.args.get("verbose"):
            level_str = "DEBUG"

        return getattr(logging, level_str, logging.INFO)

    def _create_formatter(self) -> logging.Formatter:
        """
        Create a formatter for log messages.

        Returns:
            logging.Formatter: Configured formatter
        """
        logging_config = self.config.get("logging", {})
        return logging.Formatter(
            fmt=logging_config.get("format",
                                   "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d -- %(message)s"),
            datefmt=logging_config.get("date_format", "%Y-%m-%d %H:%M:%S")
        )

    def _get_console_handler(self, formatter: logging.Formatter) -> logging.Handler:
        """
        Create a console handler for logging.

        Args:
            formatter: Formatter to use for log messages

        Returns:
            logging.Handler: Configured console handler
        """
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Set the console handler level based on verbose flag
        if self.args.get("verbose"):
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(self._get_log_level())

        return console_handler

    def _generate_log_filename(self) -> str:
        """
        Generate a log filename incorporating args and timestamp.

        Returns:
            str: Generated log filename
        """
        logging_config = self.config.get("logging", {})
        log_file = logging_config.get("file", "poster_maker_{{timestamp}}.log")

        # Replace timestamp placeholder with actual timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_file.replace("{{timestamp}}", timestamp)

        # Add relevant args to the filename if present
        filename_parts = []

        if "file" in self.args and self.args["file"]:
            # Extract just the base filename without extension
            base_name = os.path.splitext(os.path.basename(self.args["file"]))[0]
            filename_parts.append(f"img_{base_name[:15]}")  # Limit filename length

        if "parts" in self.args:
            filename_parts.append(f"p{self.args['parts']}")

        if "dpi" in self.args:
            filename_parts.append(f"dpi{self.args['dpi']}")

        if "resize_mode" in self.args and self.args["resize_mode"]:
            filename_parts.append(f"mode_{self.args['resize_mode']}")

        # Insert the parts before the extension if we have any
        if filename_parts:
            name_part, ext_part = os.path.splitext(log_file)
            log_file = f"{name_part}_{'_'.join(filename_parts)}{ext_part}"

        return log_file

    def _get_file_handler(self, formatter: logging.Formatter) -> Optional[logging.Handler]:
        """
        Create a file handler for logging if enabled.

        Args:
            formatter: Formatter to use for log messages

        Returns:
            Optional[logging.Handler]: Configured file handler or None
        """
        logging_config = self.config.get("logging", {})

        # Check if file logging is enabled
        if not logging_config.get("file_enabled", True):
            return None

        # Generate the log filename
        log_file = self._generate_log_filename()

        # Determine the log directory
        log_folder = logging_config.get("log_folder", "logs")
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        # Create the full path
        full_log_path = os.path.join(log_folder, log_file)

        # Create and configure the file handler
        try:
            file_handler = logging.FileHandler(full_log_path)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(self._get_log_level())
            self.log_file_path = os.path.abspath(full_log_path)
            return file_handler
        except Exception as e:
            print(f"Warning: Could not create log file at {full_log_path}: {str(e)}")
            return None

    def get_log_file_path(self) -> Optional[str]:
        """Return the path to the log file, if logging to file is enabled."""
        return self.log_file_path

    def _setup_logger(self) -> logging.Logger:
        """
        Set up and configure the logger based on configuration and args.

        Returns:
            logging.Logger: Configured logger
        """
        # Create logger
        logger = logging.getLogger("poster_maker")
        logger.setLevel(self._get_log_level())

        # Remove any existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create formatter
        formatter = self._create_formatter()

        # Add console handler
        console_handler = self._get_console_handler(formatter)
        logger.addHandler(console_handler)

        # Add file handler if appropriate
        file_handler = self._get_file_handler(formatter)
        if file_handler:
            logger.addHandler(file_handler)

        # Log the initialization
        logger.debug("Logger initialized")

        return logger

    def get_logger(self) -> logging.Logger:
        """
        Return the configured logger.

        Returns:
            logging.Logger: The configured logger instance
        """
        return self.logger