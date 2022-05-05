import itertools
import json

import pytest
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    JoinEvent, MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction
)

from ..src.transition import *
from ..src.utils import DummyAPI
from ..src.scripts import dummy_scripts

def test_on_user_select():
    reply_messages = on_user_select()
    assert(len(reply_messages) == 1)

    selection_message = reply_messages[0]
    assert(isinstance(selection_message, TemplateSendMessage))

    actions = selection_message.template.actions
    assert(len(actions) == 1)

    assert(actions[0].type == 'postback')

    game_str = actions[0].data
    game = json.loads(game_str)
    assert(game['state'] == STATE_USER0_JOIN)

def test_on_user0_join():

    game = {
        'state': STATE_USER0_JOIN,
    }

    reply_messages = on_user0_join(game, DUMMY_USER_ID0)
    assert(len(reply_messages) == 1)

    selection_message = reply_messages[0]
    assert(isinstance(selection_message, TemplateSendMessage))

    actions = selection_message.template.actions
    assert(len(actions) == 1)

    assert(actions[0].type == 'postback')

    game_str = actions[0].data
    game = json.loads(game_str)
    assert(game['state'] == STATE_USER1_JOIN)
    assert(len(game['users']) == 1)
    assert(game['users'][0]['id'] == DUMMY_USER_ID0)

def test_on_user1_join():
    # Normal case
    game = {
        'state': STATE_USER1_JOIN,
        'users': [
            {'id': DUMMY_USER_ID0}
        ]
    }

    reply_messages = on_user1_join(game, DUMMY_USER_ID1)
    assert(len(reply_messages) == 1)

    selection_message = reply_messages[0]
    assert(isinstance(selection_message, TemplateSendMessage))

    actions = selection_message.template.actions
    assert(len(actions) == 1)

    assert(actions[0].type == 'postback')

    game_str = actions[0].data
    game = json.loads(game_str)
    assert(game['state'] == STATE_USER2_JOIN)
    assert(len(game['users']) == 2)
    assert(game['users'][0]['id'] == DUMMY_USER_ID0)
    assert(game['users'][1]['id'] == DUMMY_USER_ID1)

    # User duplication case
    game = {
        'state': STATE_USER1_JOIN,
        'users': [
            {'id': DUMMY_USER_ID0}
        ]
    }

    reply_messages = on_user1_join(game, DUMMY_USER_ID0)
    assert(reply_messages is None)

def test_on_user2_join():
    # Normal case
    game = {
        'state': STATE_USER2_JOIN,
        'users': [
            {'id': DUMMY_USER_ID0},
            {'id': DUMMY_USER_ID1}
        ]
    }

    reply_messages = on_user2_join(game, DUMMY_USER_ID2)
    assert(len(reply_messages) == 1)

    selection_message = reply_messages[0]
    assert(isinstance(selection_message, TemplateSendMessage))

    actions = selection_message.template.actions
    assert(len(actions) == 2)

    assert(actions[0].type == 'postback')
    assert(actions[1].type == 'postback')

    # Action for difficulty easy
    game_str = actions[0].data
    game = json.loads(game_str)
    assert(game['difficulty'] == GAME_EASY)
    assert(game['state'] == STATE_DIFFICULTY_SELECTED)
    assert(len(game['users']) == 3)
    assert(game['users'][0]['id'] == DUMMY_USER_ID0)
    assert(game['users'][1]['id'] == DUMMY_USER_ID1)
    assert(game['users'][2]['id'] == DUMMY_USER_ID2)

    # Action for difficulty hard
    game_str = actions[1].data
    game = json.loads(game_str)
    assert(game['difficulty'] == GAME_HARD)
    assert(game['state'] == STATE_DIFFICULTY_SELECTED)
    assert(len(game['users']) == 3)
    assert(game['users'][0]['id'] == DUMMY_USER_ID0)
    assert(game['users'][1]['id'] == DUMMY_USER_ID1)
    assert(game['users'][2]['id'] == DUMMY_USER_ID2)

    # User duplication case
    game = {
        'state': STATE_USER1_JOIN,
        'users': [
            {'id': DUMMY_USER_ID0},
            {'id': DUMMY_USER_ID1}
        ]
    }

    reply_messages = on_user1_join(game, DUMMY_USER_ID0)
    assert(reply_messages is None)

    reply_messages = on_user1_join(game, DUMMY_USER_ID1)
    assert(reply_messages is None)

@pytest.mark.parametrize("difficulty", [GAME_EASY, GAME_HARD])
def test_on_difficulty_selected(difficulty):
    game = {
        'state': STATE_DIFFICULTY_SELECTED,
        'difficulty': difficulty,
        'users': [
            {'id': DUMMY_USER_ID0},
            {'id': DUMMY_USER_ID1},
            {'id': DUMMY_USER_ID2},
        ]
    }

    api = DummyAPI()
    group_id = None # TODO: Create dummy_group_id?
    scripts = dummy_scripts

    reply_messages = on_difficulty_selected(api, game, group_id, scripts)

    assert(len(reply_messages) == 2)

    assert(isinstance(reply_messages[0], TemplateSendMessage))
    assert(isinstance(reply_messages[1], ImageSendMessage))

    actions = reply_messages[0].template.actions
    assert(len(actions) == 3)

    for i in range(3):
        next_game_str = actions[i].data
        next_game = json.loads(next_game_str)

        s_id = next_game['s_id']
        assert(0 <= s_id and s_id < len(scripts['scenarios']))

        c_id = next_game['c_id']
        assert(c_id in [0, 1, 2])

        h_id = next_game['h_id']
        hentekos = scripts['easy_missions'] if difficulty else scripts['hard_missions']
        assert(0 <= h_id and h_id < len(hentekos))

        sa_id = next_game['sa_id']
        assert(sa_id == i)

        assert(next_game['state'] == STATE_ANSWER_SELECTED)

@pytest.mark.parametrize("difficulty", [GAME_EASY, GAME_HARD])
@pytest.mark.parametrize("user_drinks", itertools.permutations(DRINK_LIST))
@pytest.mark.parametrize("s_id", [0, 3])
@pytest.mark.parametrize("c_id", [0, 1, 2])
@pytest.mark.parametrize("h_id", [0, 3])
@pytest.mark.parametrize("sa_id", [0])
def test_on_answer_selected(difficulty, user_drinks, s_id, c_id, h_id, sa_id):
    # Orange and Melon are always exists
    if user_drinks[3] == DRINK_ORANGE or user_drinks[3] == DRINK_MELON:
        pytest.skip('Orange and Melon are always exists')
    
    game = {
        'state': STATE_ANSWER_SELECTED,
        'difficulty': difficulty,
        'users': [
            {'id': DUMMY_USER_ID0, 'drink': user_drinks[0]},
            {'id': DUMMY_USER_ID1, 'drink': user_drinks[1]},
            {'id': DUMMY_USER_ID2, 'drink': user_drinks[2]},
        ],
        's_id': s_id,
        'c_id': c_id,
        'h_id': h_id,
        'sa_id': sa_id,
    }
    
    api = DummyAPI()
    group_id = None # TODO: Create dummy_group_id?
    scripts = dummy_scripts

    reply_messages = on_answer_selected(api, game, group_id, scripts)

    assert(len(reply_messages) == 2)

    assert(isinstance(reply_messages[0], TextSendMessage))
    assert(isinstance(reply_messages[1], TemplateSendMessage))

    actions = reply_messages[1].template.actions
    assert(len(actions) == 3)

    orange_user_id = get_user_from_drink_id(api, game, group_id, DRINK_ORANGE, user_id_only=True)

    for i in range(2):
        next_game_str = actions[i].data
        next_game = json.loads(next_game_str)

        assert(next_game['su_idx'] in [0, 1, 2])
        assert(orange_user_id != game['users'][next_game['su_idx']]['id'])

        # TODO: More complicated tests are needed
