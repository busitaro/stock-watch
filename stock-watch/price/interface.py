from abc import ABCMeta
from abc import abstractmethod
from decimal import Decimal


class IPrice(metaclass=ABCMeta):
    @abstractmethod
    def get_data(self, description: int) -> Decimal:
        """
        指定された銘柄コードの価格を取得する

        Params
        -------
        description: int
            銘柄コードのリスト

        Returns
        -------
        0: decimal.Decimal
            価格

        Remarks
        -------
        取得できなかった場合には、例外発生
        (exception.GetException)

        """
        pass
