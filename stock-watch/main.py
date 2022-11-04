from sys import exit

from injector import Injector
from injector import inject

from db import IDb
from price import IPrice
from alert import IAlert
from log import ILogger
from exceptions import PriceException
from exceptions import DbException
from exceptions import AlertException
from di import DbDiModule
from di import PriceDiModule
from di import AlertDiModule
from di import LoggerDiModule


class Main:
    end_message = '株価チェックが完了しました'
    fail_get_descriptions = 'DBからの対象銘柄取得に失敗しました'

    @inject
    def __init__(self, db: IDb, price: IPrice, alert: IAlert, logger: ILogger):
        self.__db = db
        self.__price = price
        self.__alert = alert
        self.__logger = logger

    def execute(self):
        try:
            # 対象銘柄を取得
            descriptions = self.__db.get_descriptions()
        except DbException:
            self.send_message(self.fail_get_descriptions)
            exit()

        # 株価を取得
        for description in descriptions:
            try:
                price = self.__price.get_data(description)
            except PriceException:
                self.fail(description)
                continue

            # 条件を満たせばアラート
            judge_func = self.__db.get_judge_func(description)
            if judge_func(price):
                self.alert(description)

        # 終了メッセージの出力
        self.send_message(self.end_message)

    def send_message(self, message: str):
        try:
            self.__alert.send_message(message)
        except AlertException as ex:
            self.__logger.exception(ex)

    def alert(self, description: int):
        try:
            self.__alert.send_message(
                self.__db.make_alert_message(description)
            )
        except AlertException as ex:
            self.__logger.exception(ex)

    def fail(self, description: int):
        try:
            self.__alert.send_message(self.__db.make_fail_message(description))
        except AlertException as ex:
            self.__logger.exception(ex)


def execute():
    injector = \
        Injector([
            DbDiModule(),
            PriceDiModule(),
            AlertDiModule(),
            LoggerDiModule()
        ])
    main = injector.get(Main)
    main.execute()


if __name__ == '__main__':
    execute()
