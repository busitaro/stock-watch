import configparser
import os
import errno


class Config():
    config_file = '../config/config.ini'

    def __init__(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                self.config_file
            )
        self.__parser = configparser.ConfigParser()
        self.__parser.read(self.config_file, encoding='utf_8')

    @property
    def user_id(self):
        section = 'DEFAULT'
        key = 'user_id'
        try:
            return self.__parser.get(section, key)
        except configparser.NoOptionError:
            raise ValueError(f'設定ファイルにキーが存在しません。 キー: {key}')

    @property
    def channel_access_token(self):
        section = 'DEFAULT'
        key = 'channel_access_token'
        try:
            return self.__parser.get(section, key)
        except configparser.NoOptionError:
            raise ValueError(f'設定ファイルにキーが存在しません。 キー: {key}')
