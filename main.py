import os
import random
import pandas as pd
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

scripts = {}
scenario_url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/scenario.csv"
mission_url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/mission.csv"


def load_scripts():
    scenario = pd.read_csv(scenario_url)
    mission = pd.read_csv(mission_url)
    scripts['scenario'] = scenario
    scripts['mission'] = mission


load_scripts()


app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# Constants
drink_names = []
drink_names.append("メロンソーダ")
drink_names.append("オレンジジュース")
drink_names.append("ウーロンチャ")
drink_names.append("ジャスミンティ")


class Game:
    def __init__(self):
        self.state = 0
        self.user_ids = set()
        self.user_names = {}
        self.user_drinks = {}
        self.user_missions = {}
        self.chapon = 0
        self.scenario = 0

        # TODO: Remove this
        # Dummy users
        # self.user_ids.add("0")
        # self.user_ids.add("1")
        # self.user_names["0"] = "Aマン"
        # self.user_names["1"] = "Bマン"

    def get_user_from_drink(self, drink_id):
        user_id = None
        for k, v in self.user_drinks.items():
            if v == drink_id:  # オレンジ
                user_id = k
        return user_id


# Main game states (key: group_id)
games = {}


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
    source = event.source
    group_id = source.group_id
    user_id = source.user_id

    # Find game state or create new game
    if group_id not in games:
        games[group_id] = Game()

    game = games[group_id]

    if game.state == 0:
        # ユーザーを3人確定する

        # Add user
        game.user_ids.add(user_id)

        # Get new user name
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        game.user_names[user_id] = profile.display_name

        # ユーザーが３人揃った場合
        if len(game.user_ids) == 3:
            # ドリンクをシャッフルする
            drink_ids = [0, 1]  # メロンとオレンジは確定
            drink_ids.append(random.choice([2, 3]))  # ウーロンとジャスミンをランダムで選択
            random.shuffle(drink_ids)  # ランダムに憑依

            # シナリオをランダムに決定
            scenarios = scripts['scenario']
            num_scenarios = len(scenarios.index)
            scenario_id = random.randint(0, num_scenarios - 1)
            game.scenario = scenarios.iloc[scenario_id]
            scenario = game.scenario

            # チャポンの選択肢をランダムに決定
            game.chapon = random.randint(0, 2)

            for i, user_id in enumerate(game.user_ids):
                game.user_drinks[user_id] = drink_ids[i]
                mission = scripts['mission'].iloc[drink_ids[i]]['mission']
                game.user_missions[user_id] = mission

                user_name = game.user_names[user_id]
                drink_name = drink_names[game.user_drinks[user_id]]
                message = f"あなた（{user_name}）に{drink_name}が乗り移ったぞ。\n"
                message += f"{drink_name}のあなたは、{mission}\n"
                if drink_ids[i] == 0:
                    chapon = scenario['ans' + str(i)]
                    message += f"メロンソーダのあなただけに、チャポンの選択肢が「{chapon}」であることを教えてあげるぞ。\n"
                else:
                    message += f"チャポンの選択肢はメロンソーダの人しか知らない。メロンソーダに騙されるな。\n"
                message += f"これがミッションだ！"

                print("Debug:")
                print(message)

                # TODO: Remove this condition for the release
                if user_id == "0" or user_id == "1":
                    # Dummy users
                    continue

                # TODO: Comment out following lines for the release
                line_bot_api.push_message(
                    user_id, TextSendMessage(text=message))

            # トークテーマ出題
            question = scenario['question']
            actions = []
            for i in range(3):
                answer = scenario['ans' + str(i)]
                actions.append(MessageAction(label=answer, text=answer))

            selection = ButtonsTemplate(text=question, actions=actions)
            selection_message = TemplateSendMessage(
                alt_text='トークテーマ答え選択肢', template=selection)
            line_bot_api.reply_message(
                event.reply_token,
                selection_message)

            # State transition
            game.state = 1

    elif game.state == 1:
        # ジャスミンティが誰かを選択

        # TODO: Optimize here
        # Find orange user
        orange_id = game.get_user_from_drink(1)
        assert(orange_id is not None)

        user_name = game.user_names[orange_id]
        message = f"オレンジジュースの{user_name}さん、ジャスミンティがいるか推理し、1つ選ぼう"
        actions = []
        for id in game.user_ids:
            user_name = game.user_names[id]
            actions.append(MessageAction(label=user_name, text=user_name))
        actions.append(MessageAction(label='いない', text='いない'))
        selection = ButtonsTemplate(text=message, actions=actions)
        selection_message = TemplateSendMessage(
            alt_text='ジャスミン答え選択肢', template=selection)
        line_bot_api.reply_message(
            event.reply_token,
            selection_message)

        # State transition
        game.state = 2

    elif game.state == 2:
        # 正解を表示

        # TODO: Optimize here
        # Find jasmine user
        jasmine_id = game.get_user_from_drink(3)

        message = "答え:\n"
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

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))

        game.state = 0

    print(f"Debug:")
    print(f"{game.state}")
    print(f"{game.user_ids}")
    print(f"{game.user_names}")
    print(f"{game.scenario}")


if __name__ == "__main__":
    app.run()
