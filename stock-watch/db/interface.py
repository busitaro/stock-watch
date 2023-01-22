from abc import ABCMeta
from abc import abstractmethod
from decimal import Decimal
from typing import List
from typing import Callable


class IDb(metaclass=ABCMeta):
    @abstractmethod
    def get_descriptions(self) -> List[int]:
        """
        監視対象の銘柄コードリストを取得する

        Returns
        -------
        0: List[int]
            銘柄コードのリスト
        """
        pass

    @abstractmethod
    def get_description_groups(self) -> List[List[int]]:
        """
        監視対象の銘柄コードについて、
        グループ毎のリストで取得する

        Returns
        -------
        0: List[List[int]]
            銘柄グループのリスト
            各銘柄グループは銘柄コードのリストを持つ
        """
        pass

    @abstractmethod
    def get_judge_func(self, description: int) -> Callable[[Decimal], bool]:
        """
        与えられた銘柄について、
        トリガー条件を満たすかの判定メソッドを返却する

        Params
        -------
        decription
            銘柄コード

        Returns
        -------
        0: Callable[[Decimal], bool]
            トリガー発火判定メソッド
            param: Decimal(価格)
            return: トリガー発火有無
        """
        pass

    @abstractmethod
    def make_alert_message(self, description: int) -> str:
        """
        お知らせメッセージを作成する

        Params
        -------
        description: int
            銘柄コード

        Returns
        -------
        0: str
            作成したお知らせメッセージ
        """
        pass

    @abstractmethod
    def make_fail_message(self, description: int) -> str:
        """
        失敗メッセージを作成する

        Params
        -------
        description: int
            銘柄コード

        Returns
        -------
        0: str
            作成した失敗メッセージ
        """
        pass
