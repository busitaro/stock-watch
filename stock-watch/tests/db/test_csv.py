from typing import Callable
from os import path

import pytest

from db import CsvAsDb
from exceptions import DbException


@pytest.fixture
def make_object_func(mocker) -> Callable[[str], CsvAsDb]:
    """
    引数で指定したファイルをDBとして、
    CsvAsDbオブジェクトを生成する
    """
    def make_object_func(file: str) -> CsvAsDb:
        mocker.patch('db.csv.CsvAsDb.csv_file', file)
        return CsvAsDb()
    return make_object_func


@pytest.fixture
def object_by_normal_file(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_normal.csv')
    )


@pytest.fixture
def object_by_duplicate_description(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_duplicate.csv')
    )


@pytest.fixture
def object_by_bad_trigger(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_bad_trigger.csv')
    )


@pytest.fixture
def object_by_bad_price(make_object_func):
    return make_object_func(
        '{}/{}'.format(path.dirname(__file__), 'test_bad_price.csv')
    )


def test_get_descriptions(object_by_normal_file):
    """
    正常に銘柄コードのリストが取得できること

    """
    result = object_by_normal_file.get_descriptions()
    assert result == [8267, 5555, 1333, 12345]


def test_get_descriptions_from_duplicate_file(object_by_duplicate_description):
    """
    重複する銘柄が存在するCSVから銘柄一覧を取得した場合、
    重複なく銘柄コードが取得できること

    """
    result = object_by_duplicate_description.get_descriptions()
    assert result == [8267, 1333, 12345]


def test_get_description(object_by_normal_file, mocker):
    """
    正常に銘柄コードグループのリストが取得できること

    """
    # mock
    descriptions = [136, 639, 543254, 453]
    triggers = ['under', 'over', 'over', 'under']
    mocker.patch.object(
        object_by_normal_file,
        'get_descriptions',
        return_value=descriptions
    )
    mock__get_price_triger_from_db = \
        mocker.patch.object(
            object_by_normal_file,
            '_CsvAsDb__get_price_trigger_from_db'
        )
    mock__get_price_triger_from_db.side_effect = \
        lambda description: (0, triggers[descriptions.index(description)])

    # exec
    result = object_by_normal_file.get_description_groups()

    # confirm
    assert result == [[639, 543254], [136, 453]]


def test_get_judge_func_trigger_over(object_by_normal_file):
    """
    正常にトリガー条件判定メソッドが返却されること
    (トリガーが以上の場合)

    """
    result_func = object_by_normal_file.get_judge_func(1333)
    test_param1 = 1999
    test_param2 = 2000
    test_param3 = 2001
    assert result_func(test_param1) is False
    assert result_func(test_param2) is True
    assert result_func(test_param3) is True


def test_get_judge_func_not_existing_description(object_by_normal_file):
    """
    トリガー条件判定メソッドについて、存在しない銘柄コードを指定した場合、
    DbExceptionが返ること
    """
    with pytest.raises(DbException) as ex:
        object_by_normal_file.get_judge_func(9999999999)

    message = 'DBにデータが存在しません。 銘柄コード: 9999999999'
    assert str(ex.value) == message


def test_get_judge_func_trigger_under(object_by_normal_file):
    """
    正常にトリガー条件判定メソッドが返却されること
    (トリガーが以下の場合)

    """
    result_func = object_by_normal_file.get_judge_func(8267)
    test_param1 = 2699
    test_param2 = 2700
    test_param3 = 2701
    assert result_func(test_param1) is True
    assert result_func(test_param2) is True
    assert result_func(test_param3) is False


def test_get_judge_func_exception_by_duplicate(
    object_by_duplicate_description
):
    """
    DBにて指定銘柄データが重複していた場合、
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_duplicate_description.get_judge_func(1333)

    message = 'DBデータが不正です。 銘柄コード: 1333'
    assert str(ex.value) == message


def test_get_judge_func_exception_by_invalid_trigger(object_by_bad_trigger):
    """
    DBにて指定銘柄データのトリガーが不正だった場合
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_bad_trigger.get_judge_func(12345)

    message = 'DBデータが不正です。 銘柄コード: 12345'
    assert str(ex.value) == message


def test_get_judge_func_exception_by_invalid_price(object_by_bad_price):
    """
    DBにて指定銘柄データのトリガー価格が不正だった場合
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_bad_price.get_judge_func(7452)

    message = 'DBデータが不正です。 銘柄コード: 7452'
    assert str(ex.value) == message


def test_make_alert_message_trigger_over(object_by_normal_file):
    """
    正常にお知らせメッセージが作成されること
    (トリガーが以上の場合)

    """
    result = object_by_normal_file.make_alert_message(12345)

    message = '銘柄コード: 12345 が 価格: 134.0 円を上回りました。'
    assert result == message


def test_make_alert_message_trigger_under(object_by_normal_file):
    """
    正常にお知らせメッセージが作成されること
    (トリガーが以下の場合)

    """
    result = object_by_normal_file.make_alert_message(8267)

    message = '銘柄コード: 8267 が 価格: 2,700.0 円を下回りました。'
    assert result == message


def test_make_alert_message_not_existing_description(object_by_normal_file):
    """
    お知らせメッセージ作成メソッドについて、存在しない銘柄コードを指定した場合、
    DbExceptionが返ること
    """
    with pytest.raises(DbException) as ex:
        object_by_normal_file.make_alert_message(9999999999)

    message = 'DBにデータが存在しません。 銘柄コード: 9999999999'
    assert str(ex.value) == message


def test_make_alert_message_exception_by_duplicate(
    object_by_duplicate_description
):
    """
    DBにて指定銘柄データが重複していた場合、
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_duplicate_description.make_alert_message(1333)

    message = 'DBデータが不正です。 銘柄コード: 1333'
    assert str(ex.value) == message


def test_make_alert_message_exception_by_invalid_trigger(
    object_by_bad_trigger
):
    """
    DBにて指定銘柄データのトリガーが不正だった場合
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_bad_trigger.make_alert_message(12345)

    message = 'DBデータが不正です。 銘柄コード: 12345'
    assert str(ex.value) == message


def test_make_alert_message_exception_by_invalid_price(object_by_bad_price):
    """
    DBにて指定銘柄データのトリガー価格が不正だった場合
    正常にDbExceptionがraiseされること

    """
    with pytest.raises(DbException) as ex:
        object_by_bad_price.make_alert_message(7452)

    message = 'DBデータが不正です。 銘柄コード: 7452'
    assert str(ex.value) == message


def test_make_fail_message(object_by_normal_file):
    """
    正常に失敗メッセージが作成されること

    """
    result = object_by_normal_file.make_fail_message(1333)

    message = '銘柄コード: 1333のDB登録取得が失敗しました。'
    assert result == message
