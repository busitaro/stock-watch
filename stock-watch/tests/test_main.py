from decimal import Decimal
from typing import Callable

import pytest
from injector import Module
from injector import Injector

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

    def __init__(self):
        super().__init__(IDb, MockDb)


class TestPriceDiModule(TestDiModule):
    __test__ = False

    def __init__(self):
        super().__init__(IPrice, MockPrice)


class TestAlertDiModule(TestDiModule):
    __test__ = False

    def __init__(self):
        super().__init__(IAlert, MockAlert)


class TestLoggerDiModule(TestDiModule):
    __test__ = False

    def __init__(self):
        super().__init__(ILogger, MockLogger)


def get_description_groups(test_descriptions: dict) -> list:
    """
    テスト用関数
    test_descriptionsから、銘柄グループを取得する
    """
    description_groups_dict = {}
    for code, config in test_descriptions.items():
        group = config['group']
        if group in description_groups_dict:
            description_groups_dict[group].append(code)
        else:
            description_groups_dict[group] = [code]
    return list(description_groups_dict.values())


def get_alert_description_groups(test_descriptions: dict) -> list:
    """
    テスト用関数
    test_descriptionsから、アラート対象の銘柄コードをグループ毎に取得する
    """
    groups = []
    for config in test_descriptions.values():
        group = config['group']
        if group not in groups:
            groups.append(group)
    description_group_dict = \
        dict(zip(
            groups,
            [[] for _ in range(len(groups))]
        ))
    for code, config in test_descriptions.items():
        group = config['group']
        if config['alert_target']:
            description_group_dict[group].append(code)
    return list(description_group_dict.values())


def get_main_object():
    injector = \
        Injector([
            TestDbDiModule(),
            TestPriceDiModule(),
            TestAlertDiModule(),
            TestLoggerDiModule()
        ])
    return injector.get(main.Main)


def test_execute_normal(mocker):
    """
    以下の3点が正常終了した場合のテスト
    1. DBから対象銘柄コードグループの取得
    2. すべての銘柄コードの価格取得
    3. 通知メッセージ送信

    以下の結果を期待する
    1. DBからの対象銘柄コードグループ取得メソッドが一度だけ呼ばれること
    2. 対象銘柄の数の回数だけ、価格取得メソッドが呼ばれること
       またその引数がDBから取得した銘柄コードグループの銘柄コードであること
    3. 対象銘柄の数の回数だけ、トリガー条件判定メソッド取得メソッドが呼ばれること
       その引数がDBから取得した銘柄コードグループの銘柄コードであること
       またトリガー条件判定メソッドに渡される引数が価格取得メソッドで取得した価格であること
    4. 各銘柄コードグループ毎に、アラートメソッドが呼ばれること
       またその引数が、トリガー条件判定メソッドにてTrueが返された銘柄のリストであること
       (Trueの銘柄が一つもない場合には、引数は空のリスト)
    5. 処理完了時に、メッセージ通知メソッドが呼ばれ、
       パラメータとして終了メッセージが設定されていること
    6. 価格取得失敗メッセージ通知メソッドが一度も呼ばれないこと
    """
    test_groups = ['gr0', 'gr1', 'gr2']
    test_descriptions = {
        12345: {
            'alert_target': False,
            'price': Decimal(8394),
            'group': test_groups[0],
        },
        56789: {
            'alert_target': True,
            'price': Decimal(43093),
            'group': test_groups[2],
        },
        24680: {
            'alert_target': True,
            'price': Decimal(12),
            'group': test_groups[0],
        },
        13579: {
            'alert_target': False,
            'price': Decimal(43),
            'group': test_groups[1],
        },
        87954: {
            'alert_target': True,
            'price': Decimal(987),
            'group': test_groups[0],
        },
    }
    # 銘柄グループ
    description_groups = get_description_groups(test_descriptions)
    # アラート対象の銘柄コード
    alert_description_groups = get_alert_description_groups(test_descriptions)
    """
    mock Main
    """
    main_send_message = mocker.patch('main.Main.send_message')
    main_alert = mocker.patch('main.Main.alert')
    main_fail = mocker.patch('main.Main.fail')

    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    # IDb.get_description_groups
    idb_get_description_groups = \
        mocker.patch.object(
            db_mock,
            'get_description_groups',
            return_value=description_groups
        )

    # IDb.get_judge_func
    def get_judge_func(description: int) -> Callable[[Decimal], bool]:
        """
        引数のチェックとalert_targetの値を返す
        """

        if description in test_descriptions:
            config = test_descriptions[description]

            def func(param_price: Decimal) -> bool:
                if param_price != config['price']:
                    # judge_funcに与えられた引数の確認
                    raise ValueError('unexpected param_price is received')
                return config['alert_target']
            return func
        else:
            raise ValueError('Parameter description is invalid')

    idb_get_judge_func = mocker.patch.object(db_mock, 'get_judge_func')
    idb_get_judge_func.side_effect = get_judge_func

    # patch
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)

    # IPrice.get_data
    iprice_get_data = \
        mocker.patch.object(price_mock, 'get_data', return_value=1111)
    iprice_get_data.side_effect = \
        lambda description: test_descriptions[description]['price']

    # patch
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    # patch
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    # patch
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    """
    mock di
    """
    """
    exec
    """
    main_object = get_main_object()
    main_object.execute()

    """
    confirm
    """
    # 1. DBからの対象銘柄コードグループ取得メソッドが一度だけ呼ばれること
    assert idb_get_description_groups.call_count == 1
    # 2. 対象銘柄の数の回数だけ、価格取得メソッドが呼ばれること
    #    またその引数がDBから取得した銘柄コードグループの銘柄コードであること
    params_descriptions = []
    for description_group in description_groups:
        for code in description_group:
            params_descriptions.append(mocker.call(code))
    assert iprice_get_data.call_count == len(test_descriptions)
    iprice_get_data.assert_has_calls(params_descriptions)
    # 3. 対象銘柄の数の回数だけ、トリガー条件判定メソッド取得メソッドが呼ばれること
    #    その引数がDBから取得した銘柄コードグループの銘柄コードであること
    #    またトリガー条件判定メソッドに渡される引数が価格取得メソッドで取得した価格であること
    assert idb_get_judge_func.call_count == len(test_descriptions)
    idb_get_judge_func.assert_has_calls(params_descriptions)
    # 4. 各銘柄コードグループ毎に、アラートメソッドが呼ばれること
    #    またその引数が、トリガー条件判定メソッドにてTrueが返された銘柄のリストであること
    #    (Trueの銘柄が一つもない場合には、引数は空のリスト)
    params_alert_description_groups = \
        [mocker.call(group) for group in alert_description_groups]
    assert main_alert.call_count == len(test_groups)
    main_alert.assert_has_calls(params_alert_description_groups)
    # 5. 処理完了時に、メッセージ通知メソッドが呼ばれ、
    #    パラメータとして終了メッセージが設定されていること
    assert main_send_message.call_count == 1
    main_send_message.assert_has_calls([mocker.call(main.Main.end_message)])
    # 6. 価格取得失敗メッセージ通知メソッドが一度も呼ばれないこと
    assert main_fail.call_count == 0


def test_fail_get_descriptions(mocker):
    """
    DBからの対象銘柄グループ取得処理で例外が発生した場合、
    その旨のメッセージが送出され、終了すること
    """
    """
    mock Main
    """
    main_send_message = mocker.patch('main.Main.send_message')
    mocker.patch('main.Main.alert')
    mocker.patch('main.Main.fail')

    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    # IDb.get_description_groups
    idb_get_description_groups = \
        mocker.patch.object(db_mock, 'get_description_groups')
    idb_get_description_groups.side_effect = DbException()
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    """
    exec
    """
    main_object = get_main_object()
    with pytest.raises(SystemExit):
        main_object.execute()

    """
    confirm
    """
    assert idb_get_description_groups.call_count == 1
    main_send_message.assert_has_calls(
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
    description_groups = [
        [12345, 56789],
        [24680],
        [13579, 45678, 67890],
    ]

    """
    mock Main
    """
    main_send_message = mocker.patch('main.Main.send_message')
    main_alert = mocker.patch('main.Main.alert')
    main_fail = mocker.patch('main.Main.fail')

    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch.object(
        db_mock,
        'get_description_groups',
        return_value=description_groups
    )
    mocker.patch.object(db_mock, 'get_judge_func', return_value=lambda x: True)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)

    def get_data(description: int) -> Decimal:
        """
        銘柄コード 56789, 24680, 13579 で例外を発生させる
        """
        if description in [56789, 24680, 13579]:
            raise PriceException()
        else:
            return Decimal(1111)
    mocker.patch.object(price_mock, 'get_data').side_effect = get_data
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)

    """
    exec
    """
    main_object = get_main_object()
    main_object.execute()

    """
    confirm
    """

    # 価格取得失敗のメッセージ
    assert main_fail.call_count == 3
    main_fail.assert_has_calls([
        mocker.call(56789),
        mocker.call(24680),
        mocker.call(13579)
    ])

    # アラートの送信
    assert main_alert.call_count == 3
    main_alert.assert_has_calls([
        mocker.call([12345]),
        mocker.call([]),
        mocker.call([45678, 67890]),
    ])

    # 終了メッセージの出力
    assert main_send_message.call_count == 1


def test_send_message_normal(mocker):
    """
    send_messageメソッドの正常系テスト

    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(
        alert_mock,
        'send_message'
    )
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    main_object = get_main_object()
    main_object.send_message('param_message')

    """
    confirm
    """
    assert ialert_send_message.call_count == 1
    ialert_send_message.assert_has_calls([mocker.call('param_message')])
    assert ilogger_exception.call_count == 0


def test_exception_from_send_message(mocker):
    """
    send_message内で例外が発生した場合、
    log出力が行われること
    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(
        alert_mock,
        'send_message'
    )
    ialert_send_message.side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    main_object = get_main_object()
    main_object.send_message('param_message')

    """
    confirm
    """
    assert ilogger_exception.call_count == 1


def test_alert_normal(mocker):
    """
    alert対象銘柄が1件以上の場合のメッセージテスト

    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    idb_make_alert_message = mocker.patch.object(db_mock, 'make_alert_message')
    idb_make_alert_message.side_effect = lambda x: 'alert {}'.format(x)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(
        alert_mock,
        'send_message'
    )
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    descriptions = [5489, 124785, 1111]
    main_object = get_main_object()
    main_object.alert(descriptions)

    """
    confirm
    """
    assert ialert_send_message.call_count == 1
    expected_message = \
        'alert 5489\n' \
        'alert 124785\n' \
        'alert 1111'
    ialert_send_message.assert_has_calls([mocker.call(expected_message)])
    assert ilogger_exception.call_count == 0


def test_alert_empty(mocker):
    """
    alert対象銘柄が0件の場合のメッセージテスト

    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(
        alert_mock,
        'send_message'
    )
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    descriptions = []
    main_object = get_main_object()
    main_object.alert(descriptions)

    """
    confirm
    """
    assert ialert_send_message.call_count == 1
    expected_message = main.Main.no_alert_description_message
    ialert_send_message.assert_has_calls([mocker.call(expected_message)])
    assert ilogger_exception.call_count == 0


def test_exception_from_alert(mocker):
    """
    alert内で通知の際に例外が発生した場合、
    log出力が行われること
    """
    """
    mock
    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch.object(
        alert_mock,
        'send_message'
    ).side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    main_object = get_main_object()
    main_object.alert([])

    """
    confirm
    """
    assert ilogger_exception.call_count == 1


def test_fail_normal(mocker):
    """
    failメソッドの正常系テスト
    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    idb_make_fail_message = mocker.patch.object(db_mock, 'make_fail_message')
    idb_make_fail_message.side_effect = lambda x: 'fail {}'.format(x)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    ialert_send_message = mocker.patch.object(
        alert_mock,
        'send_message'
    )
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    description = 95247
    main_object = get_main_object()
    main_object.fail(description)

    """
    confirm
    """
    assert ialert_send_message.call_count == 1
    expected_message = 'fail 95247'
    ialert_send_message.assert_has_calls([mocker.call(expected_message)])
    assert ilogger_exception.call_count == 0


def test_exception_from_fail(mocker):
    """
    fail内で例外が発生した場合、
    log出力が行われること
    """
    """
    mock
    """
    """
    mock IDb
    """
    db_mock = mocker.Mock(spec=IDb)
    mocker.patch(MockDb.mock_path, new=db_mock)

    """
    mock IPrice
    """
    price_mock = mocker.Mock(spec=IPrice)
    mocker.patch(MockPrice.mock_path, new=price_mock)

    """
    mock IAlert
    """
    alert_mock = mocker.Mock(spec=IAlert)
    mocker.patch.object(
        alert_mock,
        'send_message'
    ).side_effect = AlertException()
    mocker.patch(MockAlert.mock_path, new=alert_mock)

    """
    mock ILogger
    """
    logger_mock = mocker.Mock(spec=ILogger)
    mocker.patch(MockLogger.mock_path, new=logger_mock)
    ilogger_exception = mocker.patch.object(logger_mock, 'exception')

    """
    exec
    """
    description = 95247
    main_object = get_main_object()
    main_object.fail(description)

    """
    confirm
    """
    assert ilogger_exception.call_count == 1
