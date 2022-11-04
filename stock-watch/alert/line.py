import json

import requests

from .interface import IAlert
from config import Config
from exceptions import AlertException


class AlertByLine(IAlert):
    def __init__(self):
        config = Config()
        self.__url = 'https://api.line.me/v2/bot/message/push'
        self.__user_id = config.user_id
        self.__channel_access_token = config.channel_access_token

    def send_message(self, message: str):
        try:
            response = requests.post(
                self.__url,
                headers=self.__make_headers(),
                data=self.__make_payload(message),
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            response = ex.response
            status_code = response.status_code
            response_body = \
                json.loads(
                    response.content.decode('utf-8')
                )    # contentはバイト列のJSONが返る
            err_message = \
                f'api error: status_code => {status_code} ' \
                f'message => {response_body["message"]}'
            raise AlertException(err_message)

    def __make_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__channel_access_token}'
        }

    def __make_payload(self, message: str):
        payload = {
            'to': self.__user_id,
            'messages': [{
                'type': 'text',
                'text': message
            }]
        }
        return json.dumps(payload)
