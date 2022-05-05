import copy
import json

from .constants import *

def get_drink_name(drink_id):
    if drink_id == DRINK_MELON:
        return "メロンソーダ"
    elif drink_id == DRINK_ORANGE:
        return "オレンジジュース"
    elif drink_id == DRINK_OOLONG:
        return "ウーロンチャ"
    elif drink_id == DRINK_JASMINE:
        return "ジャスミンティ"

def create_game_str_with_change(game, attribute, value):
    new_game = copy.deepcopy(game)
    new_game[attribute] = value
    new_game_str = json.dumps(new_game)
    new_game_str = new_game_str.replace(" ", "")
    return new_game_str