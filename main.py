import os
import random
import enum
import pandas as pd
from flask import Flask, request, abort, g

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, PostbackEvent,
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
# TODO: use enum
drink_names = []
drink_names.append("メロンソーダ")
drink_names.append("オレンジジュース")
drink_names.append("ウーロンチャ")
drink_names.append("ジャスミンティ")

# Load scripts from GitHub
scripts = {}


def load_scripts():
    # お題の選択肢
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/scenario.csv"
    scripts['scenario'] = pd.read_csv(url)

    # 個別に送るメッセージ
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/mission.csv"
    scripts['mission'] = pd.read_csv(url)

    # ヘンテコミッション（easy, hard）
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/easymission.csv"
    scripts['easymission'] = pd.read_csv(url)
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/hardmission.csv"
    scripts['hardmission'] = pd.read_csv(url)


load_scripts()


class State(enum.Enum):
    INIT = enum.auto(),
    SELECT_DIFFICULTY = enum.auto(),
    START = enum.auto(),
    JUDGE = enum.auto(),
    ANSWER = enum.auto(),


class Game:
    def __init__(self, num_people=3):
        self.state = State.INIT
        self.num_people = num_people
        self.chapon = 0
        self.scenario = 0
        self.selected_answer = None
        self.selected_id = None

        self.reset()

    def reset(self):
        self.user_ids = set()
        self.user_names = {}
        self.user_drinks = {}
        self.user_missions = {}

        # Dummy users
        if self.num_people == 1:
            self.user_ids.add("0")
            self.user_names["0"] = "Aマン"
            self.user_ids.add("1")
            self.user_names["1"] = "Bマン"
        if self.num_people == 2:
            self.user_ids.add("1")
            self.user_names["1"] = "Bマン"

        self.mission_difficulty = None

    def random_init_scenario(self):
        # シナリオ（お題）をランダムに決定
        scenarios = scripts['scenario']
        num_scenarios = len(scenarios.index)
        scenario_id = random.randint(0, num_scenarios - 1)
        self.scenario = scenarios.iloc[scenario_id]
        # チャポンの選択肢をランダムに決定
        self.chapon = random.randint(0, 2)
        # ヘンテコミッションをランダムに決定
        assert(self.mission_difficulty is not None)
        if self.mission_difficulty == "easy":
            hentekos = scripts['easymission']
        else:
            hentekos = scripts['hardmission']
        num_hentekos = len(hentekos.index)
        henteko_id = random.randint(0, num_hentekos - 1)
        self.henteko = hentekos.iloc[henteko_id]["mission"]

    def get_user_from_drink(self, drink_id):
        user_id = None
        for k, v in self.user_drinks.items():
            if v == drink_id:  # オレンジ
                user_id = k
        return user_id

    # Only for debugging
    def print_state(self):
        print(f"{self.state=}")
        print(f"{self.num_people=}")
        print(f"{self.user_ids=}")
        print(f"{self.user_names=}")
        print(f"{self.user_drinks=}")
        print(f"{self.user_missions=}")
        print(f"{self.chapon=}")
        print(f"{self.scenario=}")
        print(f"{self.selected_answer=}")
        print(f"{self.selected_id=}")
        print(f"{self.mission_difficulty=}")
        print(f"{self.henteko=}")


games = {}


def get_games():
    return games


# Main callback
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


# Message handler
@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    source = event.source
    group_id = source.group_id
    user_id = source.user_id

    games = get_games()

    # Find game state or create new game
    if group_id not in games:
        games[group_id] = Game()

    # デバッグコマンドを処理
    if event.message.text == "debug reload":
        load_scripts()
        games[group_id] = Game()
        return
    if event.message.text == "debug 1":
        games[group_id] = Game(1)
        return
    if event.message.text == "debug 2":
        games[group_id] = Game(2)
        return
    if event.message.text == "debug 3":
        games[group_id] = Game(3)
        return

    # 既存の game 状態を取得
    game = games[group_id]

    if game.state == State.INIT:
        if len(game.user_ids) < 3:
            # ユーザーを3人集める

            # Add user
            game.user_ids.add(user_id)

            # Get new user name
            profile = line_bot_api.get_group_member_profile(group_id, user_id)
            game.user_names[user_id] = profile.display_name

        if len(game.user_ids) == 3:
            # ユーザーが３人揃った場合

            # ミッションの難易度を選択
            if game.mission_difficulty is None:
                message = f"まずは最初に、へんてこミッションの難易度を選ぼう。"
                actions = [
                    PostbackAction(label="やさしい", data="easy"),
                    PostbackAction(label="むずかしい", data="hard"),
                ]
                selection = ButtonsTemplate(text=message, actions=actions)
                selection_message = TemplateSendMessage(
                    alt_text='ヘンテコミッション難易度', template=selection)

                line_bot_api.reply_message(
                    event.reply_token,
                    [selection_message])

                game.state = State.SELECT_DIFFICULTY
                return

    # Debug output
    print("debug: handle_message")
    game.print_state()


# Postback handler
@ handler.add(PostbackEvent)
def handle_postback(event):
    source = event.source
    group_id = source.group_id
    user_id = source.user_id

    games = get_games()

    # 既存の game 状態を取得
    game = games[group_id]

    if game.state == State.INIT:
        action = event.postback.data
        assert(action == "continue" or action == "reset")
        if action == "reset":
            # ゲームをリセット
            game.reset()

            message = "参加したい3人がそれぞれ一言つぶやくとゲームがスタートするぞ。"
            text_message = TextSendMessage(text=message)
            line_bot_api.reply_message(
                event.reply_token,
                [text_message])
            return
        else:
            game.state = State.START

    if game.state == State.SELECT_DIFFICULTY:
        # ヘンテコミッションの難易度をセット
        difficulty = event.postback.data
        assert(game.mission_difficulty is None)
        assert(difficulty == "easy" or difficulty == "hard")
        game.mission_difficulty = difficulty

        # message = "ゲームスタート！"
        # text_message = TextSendMessage(text=message)
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     [text_message])
        game.state = State.START

    if game.state == State.START:
        # ドリンクをシャッフルする
        drink_ids = [0, 1]  # メロンとオレンジは確定
        drink_ids.append(random.choice([2, 3]))  # ウーロンとジャスミンをランダムで選択
        random.shuffle(drink_ids)  # ランダムに憑依

        # シナリオをランダムに決定
        game.random_init_scenario()

        for i, user_id in enumerate(game.user_ids):
            game.user_drinks[user_id] = drink_ids[i]
            mission = scripts['mission'].iloc[drink_ids[i]]['mission']
            game.user_missions[user_id] = mission

            user_name = game.user_names[user_id]
            drink_name = drink_names[game.user_drinks[user_id]]
            message = f"あなた（{user_name}）に{drink_name}が乗り移ったぞ。\n"
            message += f"{drink_name}のあなたは、{mission}\n"
            if drink_ids[i] == 3:
                message += f"へんてこミッション「{game.henteko}」\n"
            if drink_ids[i] == 0:
                chapon = game.scenario['ans' + str(game.chapon)]
                message += f"メロンソーダのあなただけに、チャポンの選択肢が「{chapon}」であることを教えてあげるぞ。\n"
            else:
                message += f"チャポンの選択肢はメロンソーダの人しか知らない。メロンソーダに騙されるな。\n"
            message += f"これがミッションだ！"

            # Do not send message to dummy users
            if user_id == "0" or user_id == "1":
                continue

            # NOTICE: This consumes API call count
            # line_bot_api.push_message(
            #     user_id, TextSendMessage(text=message))

        # トークテーマ出題
        game.selected_answer = None
        question = game.scenario['question']
        actions = []
        for i in range(3):
            answer = game.scenario['ans' + str(i)]
            actions.append(PostbackAction(label=answer, data=i))

        selection = ButtonsTemplate(text=question, actions=actions)
        selection_message = TemplateSendMessage(
            alt_text='トークテーマ答え選択肢', template=selection)

        # Prepare image message
        image_url = "https://github.com/wakwakcreate/drink_scripts/raw/main/countdown.gif"

        image_message = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url)

        line_bot_api.reply_message(
            event.reply_token,
            [selection_message, image_message])

        # State transition
        game.state = State.JUDGE

    elif game.state == State.JUDGE:
        if game.selected_answer is None:
            game.selected_answer = event.postback.data
        else:
            return
        scenario = game.scenario
        answer_str = scenario['ans' + str(game.selected_answer)]
        message = f"{answer_str} が選択されたぞ。"
        text_message = TextSendMessage(text=message)

        # ジャスミンティが誰かを選択

        # Find orange user
        orange_id = game.get_user_from_drink(1)
        assert(orange_id is not None)

        game.selected_id = None

        user_name = game.user_names[orange_id]
        message = f"オレンジジュースの{user_name}さん、ジャスミンティがいるか推理し、1つ選ぼう"
        actions = []
        for id in game.user_ids:
            user_name = game.user_names[id]
            actions.append(PostbackAction(label=user_name, data=id))
        actions.append(PostbackAction(label='いない', data="-1"))
        selection = ButtonsTemplate(text=message, actions=actions)
        selection_message = TemplateSendMessage(
            alt_text='ジャスミン答え選択肢', template=selection)
        line_bot_api.reply_message(
            event.reply_token,
            [text_message, selection_message])

        # State transition
        game.state = State.ANSWER

    elif game.state == State.ANSWER:
        # 答え合わせメッセージ表示フェーズ

        # -----------------------------
        # 勝者決定
        # -----------------------------

        # Get drink user id
        melon_id = game.get_user_from_drink(0)
        orange_id = game.get_user_from_drink(1)
        oolong_id = game.get_user_from_drink(2)
        jasmine_id = game.get_user_from_drink(3)

        if game.selected_id is not None:
            return

        if event.postback.data != "-1":
            game.selected_id = event.postback.data

        winner = None
        image_name = "draw"
        if game.selected_answer == str(game.chapon):
            winner = 0
            image_name = "melon"
        elif game.selected_id == jasmine_id:
            winner = 1
            image_name = "orange"
        elif game.selected_id == melon_id and oolong_id is not None:
            winner = 2
            image_name = "oolong"
        elif game.selected_id != jasmine_id and jasmine_id is not None:
            winner = 3
            image_name = "jasmine"

        # -----------------------------
        # 各種メッセージを準備
        # -----------------------------

        # 勝者ドリンクの写真メッセージ
        image_url = f"https://github.com/wakwakcreate/drink_scripts/blob/main/{image_name}.png?raw=true"
        image_message = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url)

        # 答え合わせメッセージ
        message = "答えあわせ:\n"
        if jasmine_id is None:
            message += "ジャスミンティはいませんでした！\n"
        else:
            user_name = game.user_names[jasmine_id]
            message += f"ジャスミンティは{user_name}でした！\n"

        message += "\n配役:\n"
        for id in game.user_ids:
            message += game.user_names[id] + ": " + \
                drink_names[game.user_drinks[id]] + "\n"

        message += "\nチャポンの選択肢:\n" + game.scenario["ans" + str(game.chapon)]

        message += "\n選択された選択肢:\n" + \
            game.scenario["ans" + game.selected_answer]
        user_name = "いない"
        if game.selected_id != "-1":
            user_name = game.user_names[game.selected_id]
        message += "\n選択されたユーザー:\n" + user_name
        message += "\nへんてこミッション:\n" + game.henteko

        text_message = TextSendMessage(text=message)

        # ゲーム続行 or リセットボタン メッセージ
        message = f"ゲームを続けますか？"
        actions = [
            PostbackAction(label="同じメンバーで続ける", data="continue"),
            PostbackAction(label="メンバーを変える", data="reset"),
        ]
        selection = ButtonsTemplate(text=message, actions=actions)
        selection_message = TemplateSendMessage(
            alt_text='ゲーム続行 or リセット', template=selection)

        # -----------------------------
        # メッセージ送信
        # -----------------------------
        line_bot_api.reply_message(
            event.reply_token,
            [image_message, text_message, selection_message])

        game.state = State.INIT

    # Debug output
    print("debug: handle_postback")
    game.print_state()


if __name__ == "__main__":
    app.run()
