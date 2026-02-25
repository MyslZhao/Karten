"""
服务器游戏逻辑相关类, 包括:
+ Player玩家属性管理类
+ Game游戏基本属性管理类
"""
from random import shuffle, choice
from enum import Enum
from typing import List, Optional
# Card id
# HACK: 用List[int]而不是Tuple[int,int]
# HACK: 我忘了我当时怎么想的了xp.
# HACK: 在下一次可能的更新中会改正。
CARD = [
    [0, 1], #->3
    [0, 2],
    [0, 3],
    [0, 4],
    [0, 5],
    [0, 6],
    [0, 7],
    [0, 8],
    [0, 9],
    [0, 10],
    [0, 11],
    [0, 12],
    [0, 13], #->2
    [1, 1],
    [1, 2],
    [1, 3],
    [1, 4],
    [1, 5],
    [1, 6],
    [1, 7],
    [1, 8],
    [1, 9],
    [1, 10],
    [1, 11],
    [1, 12],
    [1, 13],
    [2, 1],
    [2, 2],
    [2, 3],
    [2, 4],
    [2, 5],
    [2, 6],
    [2, 7],
    [2, 8],
    [2, 9],
    [2, 10],
    [2, 11],
    [2, 12],
    [2, 13],
    [3, 1],
    [3, 2],
    [3, 3],
    [3, 4],
    [3, 5],
    [3, 6],
    [3, 7],
    [3, 8],
    [3, 9],
    [3, 10],
    [3, 11],
    [3, 12],
    [3, 13],
    [4, 14], #小王
    [4, 15]  #大王
]

class Player:
    """
    玩家属性管理类
    """
    _card : List[List[int]]
    _num = -1
    def __init__(self, id : str):
        """初始化玩家

        :param id: 玩家id
        :type id: str
        """
        self.id = id
        self._card = []
        self._landlord = False

    def changeChar(self) -> None:
        """反转角色
        """
        self._landlord = not self._landlord

    def addCard(self, cards : List[List[int]]|List[int]) -> None:
        """添加初始牌型

        :param cards: 牌序列
        :type cards: List[List[int]] | List[int]
        """
        if isinstance(cards[0], List):
            self._card.extend(cards) # pyright: ignore[reportArgumentType]
        else:
            self._card.append(cards) # pyright: ignore[reportArgumentType]

    @property
    def cards(self) -> List[List[int]]:
        """查询牌序列

        :return: 初始牌序列
        :rtype: List[List[int]]
        """
        return self._card

    @property
    def cardnum(self) -> int:
        """牌数量

        :return: 牌数量
        :rtype: int
        """
        if self._num == -1:
            self._num = len(self._card)
        return self._num

    @property
    def identity(self) -> bool:
        """身份

        :return: 是否为地主
        :rtype: bool
        """
        return self._landlord

    def dec_cards(self, n : int) -> None:
        """更新牌数

        :param n: 减少的牌数
        :type n: int
        """
        self._num -= n

class Game:
    """
    游戏属性管理类
    """
    _start : bool = False
    _lords : List[List[int]]
    _li : int = 0
    _player : List[Player]
    _ind : List[int]

    def __init__(self):
        self._player = []
        self._ind = [0] * 4

    @property
    def playerlist(self) -> List[Player]:
        return self._player

    @property
    def playeridlist(self) -> List[int]:
        return self._ind

    @property
    def playernum(self) -> int:
        return len(self._player)

    @property
    def lordscard(self) -> List[List[int]]:
        return self._lords

    @property
    def lordsid(self) -> int:
        return self._li

    def addPlayer(self, player : Player) -> None:
        self._player.append(player)
        self._ind[int(player.id)] = self.playernum - 1

    def searchPlayer(self, id : str) -> Optional[Player]:
        cache = self._ind[int(id)]
        if cache:
            return self._player[cache]
        return None

    def start(self) -> None:
        self._start = True

    @property
    def istart(self) -> bool:
        """游戏状态

        :return: 是否正在游戏
        :rtype: bool
        """
        return self._start

    def arrangeCards(self) -> List[List[int]]:
        """分配初始牌

        :return: 牌序列
        :rtype: List[List[int]]
        """
        arrangements = CARD
        shuffle(arrangements)
        self._lords = arrangements[51:]
        return arrangements[:51]

    def arrangeIden(self) -> Optional[Player]:
        """分配玩家身份

        :return: 地主身份的Player对象
        :rtype: Optional[Player]
        """
        NUM = [1, 2, 3]
        self._li = choice(NUM)
        ti = self._ind[self._li]
        t : Optional[Player] = None
        if 0 <= ti < 3:
            self._player[ti].changeChar()
        return t

    def isfinished(self) -> bool:
        """检查是否结束

        :return: 是否结束
        :rtype: bool
        """
        if self._start:
            for i in self._player:
                if i:
                    if i.cardnum == 0:
                        self._start = False
                        return True
        return False
