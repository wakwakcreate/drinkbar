import itertools

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

@pytest.mark.parametrize("user_id_only", [False, True])
def test_get_user_from_drink_id(user_id_only):
    for l in itertools.permutations(DRINK_LIST):
        # Use first 3 drinks for game state
        # Orange and Melon are always exists
        if l[3] == DRINK_ORANGE or l[3] == DRINK_MELON:
            continue
        game = {
            'users': [
                {'id': DUMMY_USER_ID0, 'drink': l[0]},
                {'id': DUMMY_USER_ID1, 'drink': l[1]},
                {'id': DUMMY_USER_ID2, 'drink': l[2]},
            ]
        }

        if user_id_only:
            user_id0 = get_user_from_drink_id(None, game, None, l[0], user_id_only)
            user_id1 = get_user_from_drink_id(None, game, None, l[1], user_id_only)
            user_id2 = get_user_from_drink_id(None, game, None, l[2], user_id_only)
            user_id3 = get_user_from_drink_id(None, game, None, l[3], user_id_only)
            assert(DUMMY_USER_ID0 == user_id0)
            assert(DUMMY_USER_ID1 == user_id1)
            assert(DUMMY_USER_ID2 == user_id2)
            assert(user_id3 is None)
        else:
            user_id0, user_name0 = get_user_from_drink_id(None, game, None, l[0], user_id_only)
            user_id1, user_name1 = get_user_from_drink_id(None, game, None, l[1], user_id_only)
            user_id2, user_name2 = get_user_from_drink_id(None, game, None, l[2], user_id_only)
            user_id3, user_name3 = get_user_from_drink_id(None, game, None, l[3], user_id_only)

            assert(DUMMY_USER_ID0 == user_id0)
            assert(DUMMY_USER_ID1 == user_id1)
            assert(DUMMY_USER_ID2 == user_id2)
            assert(user_id3 is None)

            assert(get_user_name(None, None, DUMMY_USER_ID0) == user_name0)
            assert(get_user_name(None, None, DUMMY_USER_ID1) == user_name1)
            assert(get_user_name(None, None, DUMMY_USER_ID2) == user_name2)
            assert(user_name3 is None)

