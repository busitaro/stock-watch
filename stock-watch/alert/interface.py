from abc import ABCMeta
from abc import abstractmethod


class IAlert(metaclass=ABCMeta):
    @abstractmethod
    def send_message(self, message: str):
        """
        通知メッセージを送信する

        Params
        -------
        message: str
            通知メッセージ

        Remarks
        -------
        通知できなかった場合には例外発生
        (exception.MessageException)

        """
        pass
