import os
import random
import enum
import json
import copy

import pandas as pd
from flask import Flask, request, abort, g

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
    PostbackAction, MessageAction
)

app = Flask(__name__)

# Load secret keys and setup LINE SDK
# NOTICE: Do not embedded secrets here. Use env variables.
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

STATE_USER_SELECT = 10
STATE_USER0_JOIN = 11
STATE_USER1_JOIN = 12
STATE_USER2_JOIN = 13

GAME_EASY = 0
GAME_HARD = 1

# Constants
c = {
    'scripts': {},
}

def load_scripts():
    # お題の選択肢
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/scenario.csv"
    c.scripts['scenario'] = pd.read_csv(url)

    # 個別に送るメッセージ
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/mission.csv"
    c.scripts['mission'] = pd.read_csv(url)

    # ヘンテコミッション（easy, hard）
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/easymission.csv"
    c.cscripts['easymission'] = pd.read_csv(url)
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/hardmission.csv"
    c.scripts['hardmission'] = pd.read_csv(url)


# Main callback
# NOTICE: Do not edit this method
@ app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def reply_init_message(token, group_id):
    game = {}
    game['state'] = STATE_USER_SELECT
    game['group_id'] = group_id
    game['debug_mode'] = False
    game_str = json.dumps(game)

    text = "一人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(token, selection_message)

def start_debug_mode(token, group_id):
    game = {}
    game['state'] = STATE_USER1_JOIN
    game['group_id'] = group_id
    game['user_ids'] = ["dummy_user_id_0", "dummy_user_id_1"]
    game['debug_mode'] = True
    game_str = json.dumps(game)

    text = "三人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(token, selection_message)


@handler.add(JoinEvent)
def handle_join(event):
    reply_init_message(event.reply_token, event.source.group_id)


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    source = event.source
    group_id = source.group_id

    # デバッグコマンドを処理
    if event.message.text == "init":
        reply_init_message(event.reply_token, group_id)
        return
    
    if event.message.text == "debug":
        start_debug_mode(event.reply_token, group_id)
        return


@ handler.add(PostbackEvent)
def handle_postback(event):
    source = event.source
    # group_id = source.group_id
    user_id = source.user_id

    game_str = event.postback.data
    game = json.loads(game_str)

    if game['state'] == STATE_USER_SELECT:
        game['user_ids'] = [user_id]
        game['state'] = STATE_USER0_JOIN
        game_str = json.dumps(game)

        text = "二人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        line_bot_api.reply_message(event.reply_token, selection_message)

    elif game['state'] == STATE_USER0_JOIN:
        # Ignore duplicate join button click
        if (user_id in game['user_ids']):
            return
        
        game['user_ids'].append(user_id)
        game['state'] = STATE_USER1_JOIN
        game_str = json.dumps(game)

        text = "三人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        line_bot_api.reply_message(event.reply_token, selection_message)

    elif game['state'] == STATE_USER1_JOIN:
        # Ignore duplicate join button click
        if (user_id in game['user_ids']):
            return
        
        game['user_ids'].append(user_id)
        game['state'] = STATE_USER2_JOIN

        game_easy = copy.deepcopy(game)
        game_easy['difficulty'] = GAME_EASY
        game_easy_str = json.dumps(game_easy)

        game_hard = copy.deepcopy(game)
        game_hard['difficulty'] = GAME_HARD
        game_hard_str = json.dumps(game_hard)

        text = "最初にゲームの難易度を選ぼう。へんてこミッションに関係するよ。"
        actions = [
            PostbackAction("微炭酸", game_easy_str),
            PostbackAction("強炭酸", game_hard_str),
        ]
        selection = ButtonsTemplate(text, actions=actions)
        selection_message = TemplateSendMessage(text, selection)

        line_bot_api.reply_message(event.reply_token, selection_message)

if __name__ == "__main__":
    load_scripts()
    app.run()
