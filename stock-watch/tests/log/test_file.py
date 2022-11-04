import logging

from log import FileLogger


logger_name = 'log.file'


def test_info(caplog):
    caplog.set_level(logging.DEBUG)

    file_logger = FileLogger()

    message = 'test for info'
    file_logger.info(message)

    assert (logger_name, logging.INFO, message) in caplog.record_tuples


def test_error(caplog):
    caplog.set_level(logging.DEBUG)

    file_logger = FileLogger()

    message = 'test for error'
    file_logger.error(message)

    assert (logger_name, logging.ERROR, message) in caplog.record_tuples


def test_exception(caplog):
    caplog.set_level(logging.DEBUG)

    file_logger = FileLogger()

    message = 'exception message'
    exception = Exception(message)
    file_logger.exception(exception)

    assert (logger_name, logging.ERROR, message) in caplog.record_tuples
