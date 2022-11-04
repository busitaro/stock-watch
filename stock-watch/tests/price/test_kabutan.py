from decimal import Decimal

import pytest

from price import PriceByKabutan
from exceptions import PriceException


def test_occur_exception(mocker):
    price_by_kabutan = PriceByKabutan()

    """
    mock
    """
    message = 'test exception'
    mocker.patch.object(
        price_by_kabutan,
        'get_html'
    ).side_effect = Exception(message)

    """
    exec
    """
    description = 9024
    with pytest.raises(PriceException) as ex:
        price_by_kabutan.get_data(description)

    assert str(ex.value) == message


def test_get_html():
    price_by_kabutan = PriceByKabutan()

    """
    exec
    """
    description = 9024
    result = price_by_kabutan.get_html(description)

    """
    confirm
    """
    assert type(result) is str


def test_extract_price():
    price_by_kabutan = PriceByKabutan()

    """
    exec
    """
    description = 9024
    html = price_by_kabutan.get_html(description)
    result = price_by_kabutan.extract_price(html)

    """
    confirm
    """
    assert type(result) is Decimal
