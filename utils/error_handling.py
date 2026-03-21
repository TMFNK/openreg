"""
OpenReg Error Handling and Retry Mechanisms
Implements comprehensive exception handling for enterprise reliability
"""
import logging
import time
import functools
from typing import Callable, Any, Optional
import sqlite3
import psycopg2
from sqlalchemy.exc import SQLAlchemyError
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

class OpenRegError(Exception):
    """Base exception class for OpenReg"""
    pass

class DataQualityError(OpenRegError):
    """Raised when data quality checks fail"""
    pass

class DatabaseConnectionError(OpenRegError):
    """Raised when database connections fail"""
    pass

class ETLProcessingError(OpenRegError):
    """Raised when ETL processing fails"""
    pass

class ConfigurationError(OpenRegError):
    """Raised when configuration is invalid"""
    pass

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0,
                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions on failure with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(
                            "Function failed after all retry attempts",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                            exc_info=True
                        )
                        raise

                    logger.warning(
                        "Function failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay=current_delay,
                        error=str(e)
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but just in case
            raise last_exception

        return wrapper
    return decorator

def handle_database_errors(func: Callable) -> Callable:
    """Decorator for handling database-specific errors"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except (sqlite3.Error, psycopg2.Error, SQLAlchemyError) as e:
            logger.error(
                "Database error occurred",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise DatabaseConnectionError(f"Database operation failed: {str(e)}") from e
        except Exception as e:
            logger.error(
                "Unexpected error in database operation",
                function=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise ETLProcessingError(f"ETL processing failed: {str(e)}") from e
    return wrapper

def validate_configuration(config: dict, required_keys: list) -> None:
    """
    Validate that configuration contains all required keys

    Args:
        config: Configuration dictionary
        required_keys: List of required configuration keys

    Raises:
        ConfigurationError: If required keys are missing
    """
    missing_keys = []
    for key in required_keys:
        keys = key.split('.')
        current = config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                missing_keys.append(key)
                break
        else:
            # Key exists, check if it has a value
            if current is None or current == "":
                missing_keys.append(key)

    if missing_keys:
        raise ConfigurationError(f"Missing required configuration keys: {missing_keys}")

class ErrorHandler:
    """Central error handling and recovery manager"""

    def __init__(self):
        self.error_counts = {}
        self.recovery_actions = {}

    def register_recovery_action(self, error_type: type, action: Callable):
        """Register a recovery action for specific error types"""
        self.recovery_actions[error_type] = action

    def handle_error(self, error: Exception, context: dict = None) -> None:
        """
        Handle an error with appropriate logging and recovery

        Args:
            error: The exception that occurred
            context: Additional context information
        """
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        log_data = {
            "error_type": error_type,
            "error_message": str(error),
            "error_count": self.error_counts[error_type],
            "context": context or {}
        }

        if isinstance(error, (DataQualityError, ConfigurationError)):
            logger.warning("Handled error", **log_data)
        elif isinstance(error, DatabaseConnectionError):
            logger.error("Database connectivity issue", **log_data)
            # Trigger recovery if registered
            if DatabaseConnectionError in self.recovery_actions:
                try:
                    self.recovery_actions[DatabaseConnectionError]()
                except Exception as recovery_error:
                    logger.error("Recovery action failed", recovery_error=str(recovery_error))
        else:
            logger.error("Unhandled error", **log_data, exc_info=True)

    def get_error_summary(self) -> dict:
        """Get summary of errors encountered"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts_by_type": self.error_counts.copy(),
            "most_common_error": max(self.error_counts.keys(),
                                   key=lambda k: self.error_counts[k]) if self.error_counts else None
        }

# Global error handler instance
error_handler = ErrorHandler()

# Convenience functions for common error scenarios

@retry_on_failure(max_attempts=3, delay=0.5, exceptions=(DatabaseConnectionError,))
def execute_with_retry(query: str, connection_params: dict) -> Any:
    """
    Execute a database query with retry logic

    Args:
        query: SQL query to execute
        connection_params: Database connection parameters

    Returns:
        Query results
    """
    # Implementation would depend on specific database type
    # This is a placeholder for the concept
    logger.info("Executing query with retry", query_length=len(query))
    # Actual implementation would go here
    pass

def graceful_shutdown(signum: int, frame) -> None:
    """Handle graceful shutdown on system signals"""
    logger.info("Received shutdown signal", signal=signum)
    # Perform cleanup operations here
    logger.info("Shutdown complete")

def setup_structured_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup structured logging configuration"""
    import logging.config

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'json'
            }
        },
        'loggers': {
            'openreg': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            }
        },
        'root': {
            'handlers': ['console'],
            'level': log_level
        }
    }

    if log_file:
        logging_config['handlers']['file'] = {
            'level': log_level,
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'json'
        }
        logging_config['loggers']['openreg']['handlers'].append('file')
        logging_config['root']['handlers'].append('file')

    logging.config.dictConfig(logging_config)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Initialize default logging
setup_structured_logging()
