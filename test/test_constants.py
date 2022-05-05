from ..src.constants import *

def test_drinks():
    assert(DRINK_MELON == 0)
    assert(DRINK_ORANGE == 1)
    assert(DRINK_OOLONG == 2)
    assert(DRINK_JASMINE == 3)
    assert(DRINK_LIST == [DRINK_MELON, DRINK_ORANGE, DRINK_OOLONG, DRINK_JASMINE])

def test_dummy_user_id():
    assert(DUMMY_USER_ID0 == 'Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    assert(DUMMY_USER_ID1 == 'Uyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
    assert(DUMMY_USER_ID2 == 'Uzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')