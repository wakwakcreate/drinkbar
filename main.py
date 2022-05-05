import os
import random
import enum
import json
import copy

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

from constants import *
from scripts import load_scripts, scripts

app = Flask(__name__)

# Load secret keys and setup LINE SDK
# NOTICE: Do not embedded secrets here. Use env variables.
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

def get_drink_name(drink_id):
    if drink_id == DRINK_MELON:
        return "メロンソーダ"
    elif drink_id == DRINK_ORANGE:
        return "オレンジジュース"
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

def get_user_from_drink_id(game, group_id, drink_id, user_id_only=False):
    for user in game['users']:
        if user['drink'] == drink_id:
            user_id = user['id']
            if user_id_only:
                return user_id
            else:
                user_name = get_user_name(group_id, user_id)
                return user_id, user_name

    if user_id_only:
        return None
    else:
        return None, None

def create_game_str_with_change(game, attribute, value):
    new_game = copy.deepcopy(game)
    new_game[attribute] = value
    new_game_str = json.dumps(new_game)
    new_game_str = new_game_str.replace(" ", "")
    return new_game_str


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

    text = "一人目の参加者はボタンを押してね。"
    game_str = create_game_str_with_change({}, 'state', STATE_USER0_JOIN)
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    line_bot_api.reply_message(token, selection_message)

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
    reply_init_message(event.reply_token, event.source.group_id)


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

    reply_messages = []

    if game['state'] == STATE_USER_SELECT:
        game_str = create_game_str_with_change({}, 'state', STATE_USER0_JOIN)

        text = "一人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        reply_messages = [selection_message]

    elif game['state'] == STATE_USER0_JOIN:
        game['users'] = [{'id': user_id}]
        game_str = create_game_str_with_change(game, 'state', STATE_USER1_JOIN)

        text = "二人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        reply_messages = [selection_message]

    elif game['state'] == STATE_USER1_JOIN:
        # Ignore duplicate join button click
        for user in game['users']:
            if user['id'] == user_id:
                return
        
        game['users'].append({'id': user_id})
        game_str = create_game_str_with_change(game, 'state', STATE_USER2_JOIN)

        text = "三人目の参加者はボタンを押してね。"
        action = PostbackAction("参加", game_str)
        selection = ButtonsTemplate(text, actions=[action])
        selection_message = TemplateSendMessage(text, selection)

        reply_messages = [selection_message]

    elif game['state'] == STATE_USER2_JOIN:
        # Ignore duplicate join button click
        for user in game['users']:
            if user['id'] == user_id:
                return
        
        game['users'].append({'id': user_id})
        game['state'] = STATE_DIFFICULTY_SELECTED
        game_easy_str = create_game_str_with_change(game, 'difficulty', GAME_EASY)
        game_hard_str = create_game_str_with_change(game, 'difficulty', GAME_HARD)

        text = "最初にゲームの難易度を選ぼう。へんてこミッションに関係するよ。"
        actions = [
            PostbackAction("微炭酸", game_easy_str),
            PostbackAction("強炭酸", game_hard_str),
        ]
        selection = ButtonsTemplate(text, actions=actions)
        selection_message = TemplateSendMessage(text, selection)

        reply_messages = [selection_message]

    elif game['state'] == STATE_DIFFICULTY_SELECTED:
        game['state'] = STATE_ANSWER_SELECTED

        # ドリンクの配役をランダムに決定
        drinks = [DRINK_MELON, DRINK_ORANGE]
        drinks.append(random.choice([DRINK_OOLONG, DRINK_JASMINE]))
        random.shuffle(drinks)
        for idx, user in enumerate(game['users']):
            user['drink'] = drinks[idx]

        # お題をランダムに決定
        scenarios = scripts['scenarios']
        scenario_id = random.randint(0, len(scenarios) - 1)
        game['s_id'] = scenario_id

        # チャポンの選択肢をランダムに決定
        game['c_id'] = random.randint(0, 2)

        # へんてこミッションをランダムに決定
        hentekos = scripts['easy_missions'] if game['difficulty'] == GAME_EASY else scripts['hard_missions']
        henteko_id = random.randint(0, len(hentekos) - 1)
        game['h_id'] = henteko_id

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
                chapon_ans = answers[game['c_id']]
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
            next_game_str = create_game_str_with_change(game, 'sa_id', i)
            actions.append(PostbackAction(answer, next_game_str))

        selection = ButtonsTemplate(question, actions=actions)
        selection_message = TemplateSendMessage(question, selection)

        # カウントダウン画像メッセージ
        image_url = "https://github.com/wakwakcreate/drink_scripts/raw/main/countdown.gif"
        image_message = ImageSendMessage(image_url, image_url)

        # 返信メッセージ 
        reply_messages = [selection_message, image_message]
    
    elif game['state'] == STATE_ANSWER_SELECTED:
        game['state'] = STATE_JASMINE_SELECTED

        # 選択された答えの確認メッセージ
        scenario = scripts['scenarios'][game['s_id']]
        selected_answer_id = game['sa_id'] # Selected Answer id
        answer = scenario['answers'][selected_answer_id]
        message = f"{answer} が選択されたぞ。"
        text_message = TextSendMessage(message)

        # ジャスミンティ選択メッセージ
        orange_user_id, orange_user_name = get_user_from_drink_id(game, group_id, DRINK_ORANGE)
        message = f"オレンジジュースの{orange_user_name}さん、ジャスミンティがいるか推理し、1つ選ぼう"
        actions = []
        for idx, user in enumerate(game['users']):
            user_id = user['id']
            # Ignore self
            if user_id == orange_user_id:
                continue
            user_name = get_user_name(group_id, user_id)
            next_game_str = create_game_str_with_change(game, 'su_idx', idx)
            actions.append(PostbackAction(user_name, next_game_str))
        next_game_str = create_game_str_with_change(game, 'su_idx', -1)
        actions.append(PostbackAction(label='いない', data=next_game_str))

        selection = ButtonsTemplate(message, actions=actions)
        selection_message = TemplateSendMessage(message, selection)

        # 返信メッセージ 
        reply_messages = [text_message, selection_message]

    elif game['state'] == STATE_JASMINE_SELECTED:
        # 答え合わせメッセージ返信

        # -----------------------------
        # 勝者決定
        # -----------------------------

        # Get drink user id
        melon_user_id = get_user_from_drink_id(game, group_id, DRINK_MELON, True)
        orange_user_id = get_user_from_drink_id(game, group_id, DRINK_ORANGE, True)
        oolong_user_id = get_user_from_drink_id(game, group_id, DRINK_OOLONG, True)
        jasmine_user_id = get_user_from_drink_id(game, group_id, DRINK_JASMINE, True)

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
            user_name = get_user_name(group_id, winner)
            message += f"{user_name}の勝ち！\n"
        # 配役
        message += "\n配役:\n"
        for user in game['users']:
            user_id = user['id']
            user_name = get_user_name(group_id, user_id)
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
            selected_user_name = get_user_name(group_id, selected_user_id)
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
    line_bot_api.reply_message(event.reply_token, reply_messages)



if __name__ == "__main__":
    app.run()
