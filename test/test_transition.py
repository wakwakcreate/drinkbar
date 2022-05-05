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