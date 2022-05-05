import json

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