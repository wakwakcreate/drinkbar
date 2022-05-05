import os
import json

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
    PostbackAction
)

from .src.constants import *
from .src.scripts import load_scripts, scripts
from .src.utils import get_drink_name, create_game_str_with_change, get_user_name, get_user_from_drink_id
from .src.transition import *

app = Flask(__name__)

# Load secret keys and setup LINE SDK
# NOTICE: Do not embedded secrets here. Use env variables.
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

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

def reply_init_message(token):
    load_scripts()
    reply_messages = on_user_select()
    line_bot_api.reply_message(token, reply_messages)

def start_debug_mode(token):
    load_scripts()

    game = {}
    game['state'] = STATE_USER2_JOIN
    game['users'] = [
        {'id': DUMMY_USER_ID0}, 
        {'id': DUMMY_USER_ID1},
    ]
    game_str = json.dumps(game)

    text = "三人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(token, selection_message)


@handler.add(JoinEvent)
def handle_join(event):
    reply_init_message(event.reply_token)


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    source = event.source
    group_id = source.group_id

    # デバッグコマンドを処理
    if event.message.text == "i" or event.message.text == "スタート":
        reply_init_message(event.reply_token)
        return
    
    if event.message.text == "d":
        start_debug_mode(event.reply_token)
        return


@ handler.add(PostbackEvent)
def handle_postback(event):
    source = event.source
    group_id = source.group_id
    user_id = source.user_id

    game_str = event.postback.data
    game = json.loads(game_str)

    reply_messages = None

    if game['state'] == STATE_USER_SELECT:
        reply_messages = on_user_select()

    elif game['state'] == STATE_USER0_JOIN:
        reply_messages = on_user0_join(game, user_id)

    elif game['state'] == STATE_USER1_JOIN:
        reply_messages = on_user1_join(game, user_id)

    elif game['state'] == STATE_USER2_JOIN:
        reply_messages = on_user2_join(game, user_id)

    elif game['state'] == STATE_DIFFICULTY_SELECTED:
        reply_messages = on_difficulty_selected(line_bot_api, game, group_id, scripts)
    
    elif game['state'] == STATE_ANSWER_SELECTED:
        reply_messages = on_answer_selected(line_bot_api, game, group_id, scripts)

    elif game['state'] == STATE_JASMINE_SELECTED:
        # 答え合わせメッセージ返信

        # -----------------------------
        # 勝者決定
        # -----------------------------

        # Get drink user id
        melon_user_id = get_user_from_drink_id(line_bot_api, game, group_id, DRINK_MELON, True)
        orange_user_id = get_user_from_drink_id(line_bot_api, game, group_id, DRINK_ORANGE, True)
        oolong_user_id = get_user_from_drink_id(line_bot_api, game, group_id, DRINK_OOLONG, True)
        jasmine_user_id = get_user_from_drink_id(line_bot_api, game, group_id, DRINK_JASMINE, True)

        selected_user_idx = game['su_idx']
        selected_user_id = None if selected_user_idx == -1 else game['users'][selected_user_idx]['id']

        winner = None
        image_name = "draw"
        if game['sa_id'] == game['c_id']:
            # Chapon is selected
            winner = melon_user_id
            image_name = "melon"
        elif selected_user_id == jasmine_user_id:
            winner = orange_user_id
            image_name = "orange"
        elif selected_user_id == melon_user_id and oolong_user_id is not None:
            winner = oolong_user_id
            image_name = "oolong"
        elif selected_user_id != jasmine_user_id and jasmine_user_id is not None: # TODO: Work for jasmine_user_id == None?
            winner = jasmine_user_id
            image_name = "jasmine"

        # -----------------------------
        # 各種メッセージを準備
        # -----------------------------

        # 勝者ドリンクの写真メッセージ
        image_url = f"https://github.com/wakwakcreate/drink_scripts/blob/main/{image_name}.png?raw=true"
        image_message = ImageSendMessage(image_url, image_url)

        # 答え合わせメッセージ
        # 勝者
        message = "答えあわせ:\n"
        if winner is None:
            message += "引き分け！\n"
        else:
            user_name = get_user_name(line_bot_api, group_id, winner)
            message += f"{user_name}の勝ち！\n"
        # 配役
        message += "\n配役:\n"
        for user in game['users']:
            user_id = user['id']
            user_name = get_user_name(line_bot_api, group_id, user_id)
            drink_name = get_drink_name(user['drink'])
            message += user_name + ": " + drink_name + "\n"
        # チャポンの選択肢
        scenario = scripts['scenarios'][game['s_id']]
        chapon_answer = scenario['answers'][game['c_id']]
        message += "\nチャポンの選択肢:\n" + chapon_answer
        # 選択された選択肢
        selected_answer = scenario['answers'][game['sa_id']]
        message += "\n選択された選択肢:\n" + selected_answer
        # 選択されたユーザー
        selected_user_name = "いない"
        if game['su_idx'] != -1:
            selected_user_id = game['users'][game['su_idx']]['id']
            selected_user_name = get_user_name(line_bot_api, group_id, selected_user_id)
        message += "\n選択されたユーザー:\n" + selected_user_name
        # へんてこミッションの内容
        if jasmine_user_id is not None:
            hentekos = scripts['easy_missions'] if game['difficulty'] == GAME_EASY else scripts['hard_missions']
            henteko = hentekos[game['h_id']]
            message += "\nへんてこミッション:\n" + henteko

        text_message = TextSendMessage(text=message)

        # ゲーム続行 or リセットボタン メッセージ
        message = f"ゲームを続けますか？"
        game_continue_str = create_game_str_with_change(game, 'state', STATE_DIFFICULTY_SELECTED)
        game_reset_str = create_game_str_with_change(game, 'state', STATE_USER_SELECT)
        actions = [
            PostbackAction("同じメンバーで続ける", game_continue_str),
            PostbackAction("メンバーを変える", game_reset_str),
        ]
        selection = ButtonsTemplate(message, actions=actions)
        selection_message = TemplateSendMessage(message, selection)

        # 返信メッセージ 
        reply_messages = [image_message, text_message, selection_message]

    # メッセージ送信
    if reply_messages is not None:
        line_bot_api.reply_message(event.reply_token, reply_messages)



if __name__ == "__main__":
    app.run()
