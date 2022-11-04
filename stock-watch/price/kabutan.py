from decimal import Decimal

import requests
from bs4 import BeautifulSoup
from lxml import html as lxml_html

from .interface import IPrice
from exceptions import PriceException


class PriceByKabutan(IPrice):
    def get_data(self, description: int) -> Decimal:
        try:
            return self.extract_price(
                self.get_html(description)
            )
        except Exception as ex:
            raise PriceException(ex) from ex

    def get_html(self, description: int) -> str:
        """
        スクレイピング対象のhtmlを取得する

        Params
        -------
        description: int
            銘柄コード

        Returns
        -------
        0: str
            取得したhtml
        """
        url = 'https://kabutan.jp/stock/?code={}'.format(description)
        response = requests.get(url)
        return response.text

    def extract_price(self, html: str) -> Decimal:
        """
        htmlから価格を抽出する

        Params
        -------
        html: str
            抽出元html

        Returns
        -------
        0: Decimal
            価格
        """
        soup = BeautifulSoup(html, 'html.parser')
        lxml_data = lxml_html.fromstring(str(soup))
        xpath = '//*[@id="stockinfo_i1"]/div[2]/span[2]'
        element = lxml_data.xpath(xpath)[0]
        price = element.text.replace('円', '').replace(',', '')
        return Decimal(price)
