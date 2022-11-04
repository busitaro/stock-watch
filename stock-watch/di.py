from injector import Module

from db import IDb
from db import CsvAsDb
from price import IPrice
from price import PriceByKabutan
from alert import IAlert
from alert import AlertByLine
from log import ILogger
from log import FileLogger


class DbDiModule(Module):
    def configure(self, binder):
        binder.bind(IDb, to=CsvAsDb())


class PriceDiModule(Module):
    def configure(self, binder):
        binder.bind(IPrice, to=PriceByKabutan())


class AlertDiModule(Module):
    def configure(self, binder):
        binder.bind(IAlert, to=AlertByLine())


class LoggerDiModule(Module):
    def configure(self, binder):
        binder.bind(ILogger, to=FileLogger())
