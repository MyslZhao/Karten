"""
牌型规范文件，包括:
+ 基础牌型规定
+ 牌型属性规定
+ 牌型信息包规定
"""
from typing import List, Union
from dataclasses import dataclass
from enum import Enum

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。

class Pattern(Enum):#牌型说明       牌数
    """
    基础牌型枚举类
    """
    NONE = 0        #不出/无效牌型  0
    SINGLE = 1      #个子           1
    PAIR = 2        #对子           2
    BOMB = 3        #炸弹           4
    STRAIGHT = 4    #顺子           [5,12]
    FULLHOUSE = 5   #三带一/一对    [3,5]
    SPAIRS = 6      #连对           [6,24]
    PLANE = 7       #飞机xxx        [6,unknown]
    KK = 8          #王炸           2

PATTERN_VALUE = {
    Pattern.NONE: None,
    Pattern.SINGLE: int,
    Pattern.PAIR: int,
    Pattern.BOMB: int,
    Pattern.STRAIGHT: list, # [长度, 最大点数]
    Pattern.FULLHOUSE: list, # [长度, 三张点数值]
    Pattern.SPAIRS: list, # [长度, 最大点数]
    Pattern.PLANE: list, # [三张种数, 带子长度, 三张最大点数]
    Pattern.KK: None
}

@dataclass
class Cards:
    """
    Cards牌型数据类
    """
    pattern : Pattern
    level : Union[int, List[int], None] = None

    def __post_init__(self) -> None:
        expected = PATTERN_VALUE[self.pattern]

        if expected is None:
            if self.level is not None:
                raise TypeError(
                    f"Level of the pattern {self.pattern.name} can't be {self.pattern}."
                    )
        elif expected is int:
            if not isinstance(self.level, int):
                raise TypeError(
                    f"Level of the pattern {self.pattern.name} can't be {self.pattern}."
                    )
        elif expected is list:
            if not isinstance(self.level, list):
                raise TypeError(
                    f"Level of the pattern {self.pattern.name} can't be {self.pattern}."
                    )
