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
    no_alert_description_message = '通知対象銘柄はありませんでした'

    @inject
    def __init__(self, db: IDb, price: IPrice, alert: IAlert, logger: ILogger):
        self.__db = db
        self.__price = price
        self.__alert = alert
        self.__logger = logger

    def execute(self):
        try:
            # 対象銘柄グループを取得
            description_groups = self.__db.get_description_groups()
        except DbException:
            self.send_message(self.fail_get_descriptions)
            exit()

        # 株価を取得
        for description_group in description_groups:
            alert_target_descriptions = []
            for description in description_group:
                try:
                    price = self.__price.get_data(description)
                except PriceException:
                    self.fail(description)
                    continue

                # 条件を満たした場合アラート対象とする
                judge_func = self.__db.get_judge_func(description)
                if judge_func(price):
                    alert_target_descriptions.append(description)
            # アラートの送信
            self.alert(alert_target_descriptions)

        # 終了メッセージの出力
        self.send_message(self.end_message)

    def send_message(self, message: str):
        try:
            self.__alert.send_message(message)
        except AlertException as ex:
            self.__logger.exception(ex)

    def alert(self, descriptions: list):
        messages = \
            [self.__db.make_alert_message(code) for code in descriptions]
        message = '\n'.join(messages)
        if not message:
            message = self.no_alert_description_message
        try:
            self.__alert.send_message(message)
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
