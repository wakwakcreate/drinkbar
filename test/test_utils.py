import pytest
from ..src.constants import *
from ..src.utils import get_drink_name, get_user_name, get_user_from_drink_id

def test_get_drink_name():
    assert("メロンソーダ" == get_drink_name(DRINK_MELON))
    assert("オレンジジュース" == get_drink_name(DRINK_ORANGE))
    assert("ウーロンチャ" == get_drink_name(DRINK_OOLONG))
    assert("ジャスミンティ" == get_drink_name(DRINK_JASMINE))

def test_get_user_name():
    # Dummy users
    assert("Aマン" == get_user_name(None, None, DUMMY_USER_ID0))
    assert("Bマン" == get_user_name(None, None, DUMMY_USER_ID1))
    assert("Cマン" == get_user_name(None, None, DUMMY_USER_ID2))

    # Real user names
    # TODO:

@pytest.mark.parametrize("drink_id", DRINK_LIST)
@pytest.mark.parametrize("user_id_only", [False, True])
def test_get_user_from_drink_id(user_id_only):
    pass
