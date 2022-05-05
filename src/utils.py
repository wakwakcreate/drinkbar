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

def get_user_name(api, group_id, user_id):
    # Dummy names
    if user_id == DUMMY_USER_ID0:
        return "Aマン"
    if user_id == DUMMY_USER_ID1:
        return "Bマン"
    if user_id == DUMMY_USER_ID2:
        return "Cマン"
    
    # Get user name via LINE API
    profile = api.get_group_member_profile(group_id, user_id)
    return profile.display_name

def get_user_from_drink_id(api, game, group_id, drink_id, user_id_only=False):
    for user in game['users']:
        if user['drink'] == drink_id:
            user_id = user['id']
            if user_id_only:
                return user_id
            else:
                user_name = get_user_name(api, group_id, user_id)
                return user_id, user_name

    if user_id_only:
        return None
    else:
        return None, None

# TODO: Should be moved to test directory?
class DummyAPI:
    def push_message(self, user_id, message):
        # TODO: Put test here
        pass