from enum import Enum
from typing import List
class Pattern(Enum):
    ILLEGAL = 0
    SINGLE = 1
    PAIR = 2
    SPRING = 3
    BOMB = 4
    STRAIGHT = 5
    FULLHOUSE = 6
    SPAIRS = 7
    PLANE = 8
    KK = 9

class Identifier:
    """
    客户端处的牌型判断单例类
    """
    _instance = None

    def __new__(cls, *argc, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):...
    def identify(self, cards : List[List[int]]) -> Pattern:...

IDENTIFIER = Identifier()