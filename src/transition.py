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

from .constants import *
from .utils import create_game_str_with_change

def on_user_select():
    game_str = create_game_str_with_change({}, 'state', STATE_USER0_JOIN)

    text = "一人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    return [selection_message]

def on_user0_join(game, user_id):
    game['users'] = [{'id': user_id}]
    game_str = create_game_str_with_change(game, 'state', STATE_USER1_JOIN)

    text = "二人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    return [selection_message]