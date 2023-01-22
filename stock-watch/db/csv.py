from typing import List
from typing import Tuple
from typing import Callable
from decimal import Decimal

import pandas as pd

from exceptions import DbException
from .interface import IDb


class CsvAsDb(IDb):
    csv_file = '../config/alert.csv'

    def __init__(self):
        self.__df = pd.read_csv(self.csv_file)

    def get_descriptions(self) -> List[int]:
        description_list = list(self.__df['description'])
        # 重複をとる
        return list(dict.fromkeys(description_list))

    def get_description_groups(self) -> List[List[int]]:
        over_group = []
        under_group = []

        for description in self.get_descriptions():
            try:
                price, trigger = self.__get_price_trigger_from_db(description)
                print(description, trigger)
            except DbException:
                # TODO: エラー制御が良くない ファイル不正の場合の挙動がアプリケーションを通して一貫していない
                # MEMO: そもそもファイル不正のチェックは__init__でやるべきかも
                continue

            if trigger == 'over':
                over_group.append(description)
            else:
                under_group.append(description)
        return [over_group, under_group]

    def get_judge_func(self, description: int) -> Callable[[int], bool]:
        price, trigger = self.__get_price_trigger_from_db(description)

        def judge_func(now_price):
            if trigger == 'over':
                return (now_price - price) >= 0
            else:
                return (price - now_price) >= 0
        return judge_func

    def make_alert_message(self, description: int) -> str:
        price, trigger = self.__get_price_trigger_from_db(description)
        message = '銘柄コード: {} が 価格: {:,.1f} 円を{}'.format(
            description,
            price,
            '下回りました。' if trigger == 'under' else '上回りました。'
        )
        return message

    def make_fail_message(self, description: int) -> str:
        return '銘柄コード: {}のDB登録取得が失敗しました。'.format(description)

    def __get_price_trigger_from_db(
        self,
        description: int
    ) -> Tuple[Decimal, str]:
        # DBから指定銘柄についてのレコードを取得
        records = self.__df[self.__df['description'] == description]
        ex_message_not_exist = 'DBにデータが存在しません。 銘柄コード: {}'.format(description)
        ex_message_invalid = 'DBデータが不正です。 銘柄コード: {}'.format(description)

        if len(records) == 0:
            # 指定銘柄のデータがない場合
            raise DbException(ex_message_not_exist)
        if len(records) > 1:
            # 指定銘柄のデータが複数行
            raise DbException(ex_message_invalid)

        # DBデータからfunctionを作成
        record = records.iloc[0]
        trigger = record.trigger
        price = record.price

        # DB設定値のチェック
        if trigger not in ('under', 'over'):
            # トリガー条件が想定外の場合
            raise DbException(ex_message_invalid)
        if not str(price).isdigit():
            # 価格に数値以外が設定されている場合
            raise DbException(ex_message_invalid)

        return Decimal(price), trigger
