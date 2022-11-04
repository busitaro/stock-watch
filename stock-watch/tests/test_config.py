from typing import Callable
from os import path

import pytest

from config import Config


@pytest.fixture
def make_object_func(mocker) -> Callable[[str], Config]:
    """
    引数で指定したファイルをDBとして、
    CsvAsDbオブジェクトを生成する
    """
    def make_object_func(file: str) -> Config:
        mocker.patch('config.Config.config_file', file)
        return Config()
    return make_object_func


@pytest.fixture
def object_by_normal_file(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_config.ini')
    )


@pytest.fixture
def object_by_empty_file(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_config_empty.ini')
    )


def test_config_no_ini_file(mocker):
    """
    configファイルがない場合、
    Configオブジェクト作成時にFileNotFoundErrorが発生すること

    """
    mocker.patch('config.Config.config_file', 'test_config_not_existing.ini')

    with pytest.raises(FileNotFoundError) as ex:
        Config()

    message = \
        "[Errno 2] No such file or directory: 'test_config_not_existing.ini'"
    assert str(ex.value) == message


def test_config_user_id(object_by_normal_file):
    """
    正常にiniファイルからuser_idの値が取得できること

    """
    assert object_by_normal_file.user_id == 'uuuu_iii_ddd'


def test_config_user_id_by_nothing_file(object_by_empty_file):
    """
    user_idの設定の無いiniファイルからuser_idの値を取得しようとした場合、
    ValueErrorが発生すること

    """
    with pytest.raises(ValueError) as ex:
        object_by_empty_file.user_id

    message = '設定ファイルにキーが存在しません。 キー: user_id'
    assert str(ex.value) == message


def test_config_channel_access_token(object_by_normal_file):
    """
    正常にiniファイルからchannel_access_tokenの値が取得できること

    """
    assert object_by_normal_file.channel_access_token == '9432jdf912'


def test_config_channel_access_token_by_nothing_file(object_by_empty_file):
    """
    user_idの設定の無いiniファイルからchannel_access_tokenの値を取得しようとした場合、
    ValueErrorが発生すること

    """
    with pytest.raises(ValueError) as ex:
        object_by_empty_file.channel_access_token

    message = '設定ファイルにキーが存在しません。 キー: channel_access_token'
    assert str(ex.value) == message
