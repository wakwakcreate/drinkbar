import os
import random
import enum
import json

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

STATE_USER0_JOIN = 0,

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


@handler.add(JoinEvent)
def handle_join(event):
    source = event.source
    group_id = source.group_id

    game = {
        'state': STATE_USER0_JOIN,
        'group_id': group_id,
    }
    game_str = json.dumps(game)

    text = "一人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(event.reply_token, selection_message)


if __name__ == "__main__":
    load_scripts()
    app.run()
