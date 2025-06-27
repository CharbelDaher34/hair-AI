import logging
import logging.config
from core.config import settings

LOG_LEVEL = "DEBUG" if settings.DEBUG_MODE else "INFO"

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

# Optionally disable overly verbose loggers from external libraries
for noisy_logger in ("urllib3", "sqlalchemy.engine"):  # add more if needed
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
