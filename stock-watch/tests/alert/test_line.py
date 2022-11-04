import json

import pytest
import requests

from alert import AlertByLine
from exceptions import AlertException
from config import Config


def test_send_message_correctly(mocker):
    """
    正常にメッセージ送信APIがcallされること

    """

    """
    mock
    """
    response = requests.Response()
    response.status_code = 200
    post_mock = mocker.patch('alert.line.requests.post', return_value=response)

    user_id = 'uuu_id'
    channel_access_token = 'c_a_token'
    config_mock = mocker.Mock(spec=Config)
    config_mock.user_id = user_id
    config_mock.channel_access_token = channel_access_token
    mocker.patch('alert.line.Config', return_value=config_mock)

    """
    exec
    """
    alert_by_line = AlertByLine()
    message = 'テストメッセージです。'
    alert_by_line.send_message(message)

    """
    confirm
    """
    expected_url = 'https://api.line.me/v2/bot/message/push'
    expected_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }
    expected_data = {
        'to': user_id,
        'messages': [{
            'type': 'text',
            'text': message
        }]
    }

    assert post_mock.call_count == 1
    positional_args, named_args = post_mock.call_args
    assert positional_args[0] == expected_url
    assert named_args['headers'] == expected_headers
    assert named_args['data'] == json.dumps(expected_data)


def test_when_an_error_occurs_in_send_message_api(mocker):
    """
    メッセージ送信API中でエラーが発生し、
    HTTPステータスコードが200番台でなかった場合、
    AlertExceptionが発生し、メッセージが正しいこと

    """
    """
    mock
    """
    response = requests.Response()
    response.status_code = 500
    response._content = b'{"message": "api error detail"}'
    mocker.patch('alert.line.requests.post', return_value=response)

    user_id = 'uuu_id'
    channel_access_token = 'c_a_token'
    config_mock = mocker.Mock(spec=Config)
    config_mock.user_id = user_id
    config_mock.channel_access_token = channel_access_token
    mocker.patch('alert.line.Config', return_value=config_mock)

    """
    exec
    """
    alert_by_line = AlertByLine()
    message = 'テストメッセージです。'
    with pytest.raises(AlertException) as ex:
        alert_by_line.send_message(message)

    """
    confirm
    """
    expected_message = \
        'api error: status_code => 500 message => api error detail'
    assert str(ex.value) == expected_message
