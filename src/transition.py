import random

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
from .utils import get_drink_name, create_game_str_with_change, get_user_name, get_user_from_drink_id

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

def on_user1_join(game, user_id):
    # Ignore duplicate join button click
    for user in game['users']:
        if user['id'] == user_id:
            return None
    
    game['users'].append({'id': user_id})
    game_str = create_game_str_with_change(game, 'state', STATE_USER2_JOIN)

    text = "三人目の参加者はボタンを押してね。"
    action = PostbackAction("参加", game_str)
    selection = ButtonsTemplate(text, actions=[action])
    selection_message = TemplateSendMessage(text, selection)

    return [selection_message]

def on_user2_join(game, user_id):
    # Ignore duplicate join button click
    for user in game['users']:
        if user['id'] == user_id:
            return None
    
    game['users'].append({'id': user_id})
    game['state'] = STATE_DIFFICULTY_SELECTED
    game_easy_str = create_game_str_with_change(game, 'difficulty', GAME_EASY)
    game_hard_str = create_game_str_with_change(game, 'difficulty', GAME_HARD)

    text = "最初にゲームの難易度を選ぼう。へんてこミッションに関係するよ。"
    actions = [
        PostbackAction("やさしい", game_easy_str),
        PostbackAction("強炭酸", game_hard_str),
    ]
    selection = ButtonsTemplate(text, actions=actions)
    selection_message = TemplateSendMessage(text, selection)

    return [selection_message]

def on_difficulty_selected(api, game, group_id, scripts):
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
        user_name = get_user_name(api, group_id, user_id)
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
        api.push_message(
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

    return [selection_message, image_message]

def on_answer_selected(api, game, group_id, scripts):
    game['state'] = STATE_JASMINE_SELECTED

    # 選択された答えの確認メッセージ
    scenario = scripts['scenarios'][game['s_id']]
    selected_answer_id = game['sa_id'] # Selected Answer id
    answer = scenario['answers'][selected_answer_id]
    message = f"{answer} が選択されたぞ。"
    text_message = TextSendMessage(message)

    # ジャスミンティ選択メッセージ
    orange_user_id, orange_user_name = get_user_from_drink_id(api, game, group_id, DRINK_ORANGE)
    message = f"オレンジジュースの{orange_user_name}さん、ジャスミンティがいるか推理し、1つ選ぼう"
    actions = []
    for idx, user in enumerate(game['users']):
        user_id = user['id']
        # Ignore self
        if user_id == orange_user_id:
            continue
        user_name = get_user_name(api, group_id, user_id)
        next_game_str = create_game_str_with_change(game, 'su_idx', idx)
        actions.append(PostbackAction(user_name, next_game_str))
    next_game_str = create_game_str_with_change(game, 'su_idx', -1)
    actions.append(PostbackAction(label='いない', data=next_game_str))

    selection = ButtonsTemplate(message, actions=actions)
    selection_message = TemplateSendMessage(message, selection)

    return [text_message, selection_message]