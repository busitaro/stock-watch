from logging import getLogger
from logging import FileHandler
from logging import Formatter
from logging import DEBUG

from .interface import ILogger


class FileLogger(ILogger):
    log_file = 'stock.log'
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    time_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        logger = getLogger(__name__)
        handler = FileHandler(self.log_file)
        formatter = Formatter(self.log_format, self.time_format)
        handler.setFormatter(formatter)

        handler.setLevel(DEBUG)
        logger.setLevel(DEBUG)

        logger.addHandler(handler)

        self.__logger = logger

    def info(self, message: str):
        self.__logger.info(message)

    def error(self, message: str):
        self.__logger.error(message)

    def exception(self, exception: Exception):
        self.__logger.exception(exception)
