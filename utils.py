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