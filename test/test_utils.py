from ..src.constants import *
from ..src.utils import get_drink_name

def test_get_drink_name():
    assert("メロンソーダ" == get_drink_name(DRINK_MELON))
    assert("オレンジジュース" == get_drink_name(DRINK_ORANGE))
    assert("ウーロンチャ" == get_drink_name(DRINK_OOLONG))
    assert("ジャスミンティ" == get_drink_name(DRINK_JASMINE))
