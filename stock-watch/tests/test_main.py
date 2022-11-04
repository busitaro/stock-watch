from decimal import Decimal
from typing import Callable

import pytest
from injector import Module

import main
from db import IDb
from price import IPrice
from alert import IAlert
from log import ILogger
from exceptions import DbException
from exceptions import PriceException
from exceptions import AlertException


class MockDb(IDb):
    mock_path = 'test_main.MockDb'


class MockPrice(IPrice):
    mock_path = 'test_main.MockPrice'


class MockAlert(IAlert):
    mock_path = 'test_main.MockAlert'


class MockLogger(ILogger):
    mock_path = 'test_main.MockLogger'


class TestDiModule(Module):
    __test__ = False

    def __init__(self, interface, inject_object):
        self.__interface = interface
        self.__inject_object = inject_object

    def configure(self, binder):
        binder.bind(self.__interface, to=self.__inject_object)


class TestDbDiModule(TestDiModule):
    __test__ = False
    mock_path = 'main.DbDiModule'

    def __init__(self):
        super().__init__(IDb, MockDb)


class TestPriceDiModule(TestDiModule):
    __test__ = False
    mock_path = 'main.PriceDiModule'

    def __init__(self):
        super().__init__(IPrice, MockPrice)


class TestAlertDiModule(TestDiModule):
    __test__ = False
    mock_path = 'main.AlertDiModule'

    def __init__(self):
        super().__init__(IAlert, MockAlert)


class TestLoggerDiModule(TestDiModule):
    __test__ = False
    mock_path = 'main.LoggerDiModule'

    def __init__(self):
        super().__init__(ILogger, MockLogger)


def test_main_normal(mocker):
    """
    以下の3点が正常終了した場合のテスト
    1. DBからの対象銘柄コード取得
    2. すべての銘柄コードの価格取得
    3. 通知メッセージ送信

    以下の結果を期待する
    1. DBからの銘柄取得メソッドが呼ばれること
    2. 対象銘柄の数の回数だけ、価格取得メソッドが呼ばれること
       またその引数が銘柄コードであること
    3. 対象銘柄の数の回数だけ、トリガー条件判定メソッド取得メソッドが呼ばれること
       その引数が銘柄コードであること
       またトリガー条件判定メソッドの引数が価格取得メソッドで取得した価格であること
    4. 通知条件に合致した銘柄について、通知メッセージ作成メソッドが呼ばれること
    5. 通知条件に合致した銘柄について、メッセージ通知メソッドが呼ばれ、
       パラメータとして通知メッセージ作成メソッドの戻り値が設定されていること
    6. 処理完了時に、メッセージ通知メソッドが呼ばれ、
       パラメータとして終了メッセージが設定されていること
    """
    # 銘柄コード
    descriptions = [12345, 56789, 24680, 13579]
    alert_target = [False, True, True, False]
    prices = [Decimal(8394), Decimal(43093), Decimal(12), Decimal(43)]
    alert_target_descriptions = []
    for idx, description in enumerate(descriptions):
        if alert_target[idx]:
            alert_target_descriptions.append(description)

    """
    mock
    """
    # IDb
    db_mock = mocker.Mock(spec=IDb)

    def get_judge_func(description: int) -> Callable[[Decimal], bool]:
        """
        パラメータdescriptionsに対応した
        発火有無判定メソッドを返す

        発火判定はalert_targetの内容に従って実施
        また発火有無判定メソッド内にて、
        パラメータのチェックを実施する
        """
        if description in descriptions:
            idx = descriptions.index(description)
            judge = alert_target[idx]
            price = prices[idx]

            def func(param_price: Decimal) -> bool:
                if param_price != price:
                    # 与えられた引数が、想定通り価格となっているか確認
                    raise ValueError('unexpected param_price is received')
                return judge
            return func
        else:
            raise ValueError('Parameter description is invalid')
    idb_get_descriptions = \
        mocker.patch.object(
            db_mock,
            'get_descriptions',
            return_value=descriptions
        )
    idb_get_judge_func = mocker.patch.object(db_mock, 'get_judge_func')
    idb_get_judge_func.side_effect = get_judge_func
    idb_make_alert_message = mocker.patch.object(db_mock, 'make_alert_message')
    idb_make_alert_message.side_effect = lambda x: 'alert {}'.format(x)
    idb_make_fail_message = mocker.patch.object(db_mock, 'make_fail_message')
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)

    def get_data(description: int) -> Decimal:
        if description in descriptions:
            return prices[descriptions.index(description)]
        else:
            raise ValueError('Parameter description is invalid')
    iprice_get_data = \
        mocker.patch.object(price_mock, 'get_data', return_value=1111)
    iprice_get_data.side_effect = get_data
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(alert_mock, 'send_message')
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    main.execute()

    """
    confirm
    """
    params_descriptions = [
        mocker.call(description) for description in descriptions
    ]
    params_alert_descriptions = [
        mocker.call(description) for description in alert_target_descriptions
    ]
    alert_messages = [
        mocker.call(
            'alert {}'.format(description)
        ) for description in alert_target_descriptions
    ]
    # IDb
    assert idb_get_descriptions.call_count == 1
    assert idb_get_judge_func.call_count == len(descriptions)
    idb_get_judge_func.assert_has_calls(params_descriptions)
    alert_count = len(list(filter(lambda x: x, alert_target)))
    assert idb_make_alert_message.call_count == alert_count
    idb_make_alert_message.assert_has_calls(params_alert_descriptions)
    assert idb_make_fail_message.call_count == 0

    # IPrice
    assert iprice_get_data.call_count == len(descriptions)
    iprice_get_data.assert_has_calls(params_descriptions)

    # IAlert
    assert ialert_send_message.call_count == 3
    ialert_send_message.assert_has_calls(
        alert_messages + [mocker.call(main.Main.end_message)]
    )


def test_fail_get_descriptions(mocker):
    """
    DBからの対象銘柄取得処理で例外が発生した場合、
    その旨のメッセージが送出され、終了すること
    """
    """
    mock
    """
    # IDb
    db_mock = mocker.Mock(spec=IDb)
    idb_get_descriptions = mocker.patch.object(db_mock, 'get_descriptions')
    idb_get_descriptions.side_effect = DbException()
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(alert_mock, 'send_message')
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    with pytest.raises(SystemExit):
        main.execute()

    """
    confirm
    """
    assert ialert_send_message.call_count == 1
    ialert_send_message.assert_has_calls(
        [mocker.call(main.Main.fail_get_descriptions)]
    )


def test_fail_get_data_some_descriptions(mocker):
    """
    幾つかの銘柄で、価格取得が失敗した場合、
    失敗した銘柄については、取得失敗メッセージが送出され、
    その他の処理は正常に進行することの確認
    """
    """
    mock
    """
    descriptions = [12345, 56789, 24680, 13579]

    # IDb
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch.object(db_mock, 'get_descriptions', return_value=descriptions)
    mocker.patch.object(db_mock, 'get_judge_func', return_value=lambda x: True)
    idb_make_alert_message = mocker.patch.object(db_mock, 'make_alert_message')
    idb_make_alert_message.side_effect = lambda x: 'alert {}'.format(x)
    idb_make_fail_message = mocker.patch.object(db_mock, 'make_fail_message')
    idb_make_fail_message.side_effect = lambda x: 'fail {}'.format(x)
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)

    def get_data(description: int) -> Decimal:
        if description in [56789, 24680]:
            return Decimal(1111)
        else:
            raise PriceException()
    mocker.patch.object(price_mock, 'get_data').side_effect = get_data
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(alert_mock, 'send_message')
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    main.execute()

    """
    confirm
    """
    assert idb_make_alert_message.call_count == 2
    idb_make_alert_message.assert_has_calls([
        mocker.call(56789),
        mocker.call(24680),
    ])
    assert idb_make_fail_message.call_count == 2
    idb_make_fail_message.assert_has_calls([
        mocker.call(12345),
        mocker.call(13579),
    ])
    assert ialert_send_message.call_count == 5
    ialert_send_message.assert_has_calls([
        mocker.call('fail 12345'),
        mocker.call('alert 56789'),
        mocker.call('alert 24680'),
        mocker.call('fail 13579'),
    ])


def test_exception_from_send_message(mocker):
    """
    send_message内で例外が発生した場合、
    log出力が行われること
    """
    """
    mock
    """
    # IDb
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch.object(db_mock, 'get_descriptions', return_value=[])
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch.object(
        alert_mock,
        'send_message'
    ).side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    main.execute()

    """
    confirm
    """
    assert ilogger_exception.call_count == 1


def test_exception_from_alert(mocker):
    """
    alert内で例外が発生した場合、
    log出力が行われること
    """
    """
    mock
    """
    # IDb
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch.object(db_mock, 'get_descriptions', return_value=[1])
    mocker.patch.object(db_mock, 'get_judge_func', return_value=lambda x: True)
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch.object(
        alert_mock,
        'send_message'
    ).side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    mocker.patch('main.Main.send_message')
    main.execute()

    """
    confirm
    """
    assert ilogger_exception.call_count == 1


def test_exception_from_fail(mocker):
    """
    fail内で例外が発生した場合、
    log出力が行われること
    """
    """
    mock
    """
    # IDb
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch.object(db_mock, 'get_descriptions', return_value=[1])
    mocker.patch(MockDb.mock_path, new=db_mock)

    # IPrice
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch.object(price_mock, 'get_data').side_effect = PriceException()
    mocker.patch(MockPrice.mock_path, new=price_mock)

    # IAlert
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch.object(
        alert_mock,
        'send_message'
    ).side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    # ILogger
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    # mockのDi設定
    mocker.patch(TestDbDiModule.mock_path, new=TestDbDiModule)
    mocker.patch(TestPriceDiModule.mock_path, new=TestPriceDiModule)
    mocker.patch(TestAlertDiModule.mock_path, new=TestAlertDiModule)
    mocker.patch(TestLoggerDiModule.mock_path, new=TestLoggerDiModule)

    """
    exec
    """
    mocker.patch('main.Main.send_message')
    main.execute()

    """
    confirm
    """
    assert ilogger_exception.call_count == 1
