import os
import random
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction, MessageAction
)

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


game_state = 0

user_ids = set()
user_names = {}

# TODO: Remove this
# Dummy users
user_ids.add("0")
user_ids.add("1")
user_names["0"] = "Aマン"
user_names["1"] = "Bマン"
user_drinks = {}
drink_names = []
drink_names.append("メロンソーダ")
drink_names.append("オレンジジュース")
drink_names.append("ウーロンチャ")
drink_names.append("ジャスミンティ")


# @app.route("/", methods=['POST'])
# def root():
#     print("debug")
#     return 'OK'


@app.route("/callback", methods=['POST'])
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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global game_state

    if game_state == 0:
        source = event.source
        group_id = source.group_id
        user_id = source.user_id

        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        user_names[user_id] = profile.display_name
        user_ids.add(user_id)

        # ユーザーが３人揃った場合
        if len(user_ids) == 3:
            # ドリンクをシャッフルする
            drink_ids = [0, 1]  # メロンとオレンジは確定
            drink_ids.append(random.choice([2, 3]))  # ウーロンとジャスミンをランダムで選択
            random.shuffle(drink_ids)  # ランダムに憑依
            print(drink_ids)

            for idx, user_id in enumerate(user_ids):
                # TODO: Remove this
                # if user_id == "0" or user_id == "1":
                #     continue

                user_drinks[user_id] = drink_ids[idx]
                message = f"あなた（{user_names[user_id]}）に{drink_names[user_drinks[user_id]]}が乗り移りました。"
                # line_bot_api.push_message(
                #     event.source.user_id, TextSendMessage(text=message))

            selection = ButtonsTemplate(text='トークテーマ', actions=[
                MessageAction(label='和食', text='和食'),
                MessageAction(label='洋食', text='洋食'),
                MessageAction(label='中華', text='中華'),
            ])
            selection_message = TemplateSendMessage(
                alt_text='トークテーマ答え選択肢', template=selection)
            line_bot_api.reply_message(
                event.reply_token,
                selection_message)

            game_state = 1

    # ジャスミンティが誰か選択
    elif game_state == 1:
        # TODO: Optimize here
        orange_id = ""
        for k, v in user_drinks.items():
            if v == 1:  # オレンジ
                orange_id = k
        assert(orange != "")

        message = f"オレンジジュースの{user_names[orange_id]}さん、ジャスミンティがいるか推理し、1つ選ぼう"
        actions = []
        for id in user_ids:
            name = user_names[id]
            actions.append(MessageAction(label=name, text=name))
        actions.append(MessageAction(label='いない', text='いない'))
        selection = ButtonsTemplate(text=message, actions=actions)
        selection_message = TemplateSendMessage(
            alt_text='ジャスミン答え選択肢', template=selection)
        line_bot_api.reply_message(
            event.reply_token,
            selection_message)

        game_state = 2

    # 正解を表示
    elif game_state == 2:
        # TODO: Optimize here
        jasmine_id = -1
        for k, v in user_drinks.items():
            if v == 3:  # ジャスミンティ
                jasmine_id = k

        message = "答え:\n"
        if jasmine_id == -1:
            message += "ジャスミンティはいませんでした！"
        else:
            message += f"ジャスミンティは{user_names[jasmine_id]}でした！"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))
        game_state = 0


if __name__ == "__main__":
    app.run()
