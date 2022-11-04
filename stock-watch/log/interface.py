from abc import ABCMeta
from abc import abstractmethod


class ILogger(metaclass=ABCMeta):
    @abstractmethod
    def info(self, message: str):
        """
        INFOログを出力する

        Params
        -------
        message: str
            出力内容

        """
        pass

    @abstractmethod
    def error(self, message: str):
        """
        ERRORログを出力する

        Params
        -------
        message: str
            出力内容

        """
        pass

    @abstractmethod
    def exception(self, exception: Exception):
        """
        Exceptionログを出力する

        Params
        -------
        exception: Exception
            出力対象の例外

        """
        pass
