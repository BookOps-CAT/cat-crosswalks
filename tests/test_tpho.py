from contextlib import nullcontext as does_not_raise

import pytest
from bookops_sierra import SierraSession

from src.tpho import connect2sierra, get_item_callnos, update_item_callno


def test_get_item_callnos():
    reader = get_item_callnos("tests/t-pho-item-sample.csv")
    item1 = next(reader)
    item2 = next(reader)

    assert item1 == ("41221786", "*T-CLP (Hard man (Motion picture))")
    assert item2 == ("33065330", "*T-Pho A (Boy detective)")


def test_connect2sierra_live():
    assert isinstance(connect2sierra(), SierraSession)
