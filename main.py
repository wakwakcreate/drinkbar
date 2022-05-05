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

# Constants
STATE_USER_SELECT = 10
STATE_USER0_JOIN = 11
STATE_USER1_JOIN = 12
STATE_USER2_JOIN = 13

GAME_EASY = 0
GAME_HARD = 1

DRINK_MELON = 0
DRINK_ORANGE = 1
DRINK_OOLONG = 2
DRINK_JASMINE = 3

DUMMY_USER_ID0 = 'Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
DUMMY_USER_ID1 = 'Uyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'

def get_drink_name(drink_id):
    if drink_id == DRINK_MELON:
        return "メロンソーダ"
    elif drink_id == DRINK_ORANGE:
        return "オレンジソーダ"
    elif drink_id == DRINK_OOLONG:
        return "ウーロン茶"
    elif drink_id == DRINK_JASMINE:
        return "ジャスミン茶"

def get_user_name(group_id, user_id):
    # Dummy names
    if user_id == DUMMY_USER_ID0:
        return "Aマン"
    if user_id == DUMMY_USER_ID1:
        return "Bマン"
    
    # Get user name via LINE API
    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    return profile.display_name

scripts = {}

def load_scripts():
    # お題の選択肢
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/scenario.csv"
    scenarios_csv = pd.read_csv(url)
    scenarios = []
    for _, row in scenarios_csv.iterrows():
        answers = [row['ans0'], row['ans1'], row['ans2']]
        scenario = {
            'question': row['question'],
            'answers': answers,
        }
        scenarios.append(scenario)
    scripts['scenarios'] = scenarios

    # 個別に送るメッセージ
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/mission.csv"
    missions_csv = pd.read_csv(url)
    missions = []
    for _, row in missions_csv.iterrows():
        missions.append(row['mission'])
    scripts['missions'] = missions

    # ヘンテコミッション（easy, hard）
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/easymission.csv"
    easy_missions_csv = pd.read_csv(url)
    easy_missions = []
    for _, row in easy_missions_csv.iterrows():
        easy_missions.append(row['mission'])
    scripts['easy_missions'] = easy_missions

    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/hardmission.csv"
    hard_missions_csv = pd.read_csv(url)
    hard_missions = []
    for _, row in hard_missions_csv.iterrows():
        hard_missions.append(row['mission'])
    scripts['hard_missions'] = hard_missions

    print("Scripts loaded.")


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
    load_scripts()

    game = {}
    game['state'] = STATE_USER_SELECT
    game['users'] = []
    game_str = json.dumps(game)

    text = "一人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(token, selection_message)

def start_debug_mode(token, group_id):
    load_scripts()

    game = {}
    game['state'] = STATE_USER1_JOIN
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
    reply_init_message(event.reply_token, event.source.group_id)


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    source = event.source
    group_id = source.group_id

    # デバッグコマンドを処理
    if event.message.text == "i":
        reply_init_message(event.reply_token, group_id)
        return
    
    if event.message.text == "d":
        start_debug_mode(event.reply_token, group_id)
        return


@ handler.add(PostbackEvent)
def handle_postback(event):
    source = event.source
    group_id = source.group_id
    user_id = source.user_id

    game_str = event.postback.data
    game = json.loads(game_str)

    if game['state'] == STATE_USER_SELECT:
        game['users'].append({'id': user_id})
        game['state'] = STATE_USER0_JOIN
        game_str = json.dumps(game)

        text = "二人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        line_bot_api.reply_message(event.reply_token, selection_message)

    elif game['state'] == STATE_USER0_JOIN:
        # Ignore duplicate join button click
        for user in game['users']:
            if user['id'] == user_id:
                return
        
        game['users'].append({'id': user_id})
        game['state'] = STATE_USER1_JOIN
        game_str = json.dumps(game)

        text = "三人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        line_bot_api.reply_message(event.reply_token, selection_message)

    elif game['state'] == STATE_USER1_JOIN:
        # Ignore duplicate join button click
        for user in game['users']:
            if user['id'] == user_id:
                return
        
        game['users'].append({'id': user_id})
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

    elif game['state'] == STATE_USER2_JOIN:
        # ドリンクの配役をランダムに決定
        drinks = [DRINK_MELON, DRINK_ORANGE]
        drinks.append(random.choice([DRINK_OOLONG, DRINK_JASMINE]))
        random.shuffle(drinks)
        for idx, user in enumerate(game['users']):
            user['drink'] = drinks[idx]

        # お題をランダムに決定
        scenarios = scripts['scenarios']
        scenario_id = random.randint(0, len(scenarios) - 1)
        game['scenario_id'] = scenario_id

        # チャポンの選択肢をランダムに決定
        game['chapon_id'] = random.randint(0, 2)

        # へんてこミッションをランダムに決定
        hentekos = scripts['easy_missions'] if game['difficulty'] == GAME_EASY else scripts['hard_missions']
        henteko_id = random.randint(0, len(hentekos) - 1)
        game['henteko_id'] = henteko_id

        # 個別メッセージを送信
        for user in game['users']:
            user_id = user['id']
            user_name = get_user_name(group_id, user_id)
            drink_id = user['drink']
            drink_name = get_drink_name(user['drink'])
            mission = scripts['missions'][drink_id]

            message = f"あなた（{user_name}）に{drink_name}が乗り移ったぞ。\n"
            message += f"\n{drink_name}のあなたは、{mission}\n"
            message += f"これが勝利条件だ！"
            if drink_id == DRINK_JASMINE:
                message += f"\nへんてこミッション：『{hentekos[henteko_id]}』\n"
            if drink_id == DRINK_MELON:
                answers = scenarios[scenario_id]['answers']
                chapon_ans = answers[game['chapon_id']]
                message += f"\nチャポンの選択肢は「{chapon_ans}」だ。チャポンの選択肢が何かはあなたしか知らないぞ。\n"
            else:
                message += f"\nチャポンの選択肢はメロンソーダの人しか知らない。メロンソーダに騙されるな。\n"

            # Do not send message to dummy users
            if user_id == DUMMY_USER_ID0 or user_id == DUMMY_USER_ID1:
                continue

            # NOTICE: This consumes API call count
            line_bot_api.push_message(
                user_id, TextSendMessage(text=message))
        
        # お題選択肢ボタンメッセージ
        scenario = scenarios[scenario_id]
        question = scenario['question']
        actions = []
        for i in range(3):
            answer = scenario['answers'][i]
            next_game = copy.deepcopy(game)
            next_game['selected_scenario_id'] = i
            next_game_str = json.dumps(next_game)
            actions.append(PostbackAction(answer, next_game_str))

        selection = ButtonsTemplate(question, actions=actions)
        selection_message = TemplateSendMessage(question, selection)

        # カウントダウン画像メッセージ
        image_url = "https://github.com/wakwakcreate/drink_scripts/raw/main/countdown.gif"
        image_message = ImageSendMessage(image_url, image_url)

        # メッセージを送信
        line_bot_api.reply_message(
            event.reply_token,
            [selection_message, image_message])

if __name__ == "__main__":
    app.run()
