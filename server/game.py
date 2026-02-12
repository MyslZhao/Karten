from random import shuffle
from enum import Enum
from typing import List,Dict,Tuple,Optional,Any, cast
from dataclasses import dataclass
import time
# Card id
CARD = [
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (0, 6),
    (0, 7),
    (0, 8),
    (0, 9),
    (0, 10),
    (0, 11),
    (0, 12),
    (0, 13),
    (1, 0),
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),
    (1, 10),
    (1, 11),
    (1, 12),
    (1, 13),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (2, 9),
    (2, 10),
    (2, 11),
    (2, 12),
    (2, 13),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
    (3, 6),
    (3, 7),
    (3, 8),
    (3, 9),
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13)
]

#class Suit(Enum):
#    HEART = 0
#    SPADE = 1
#    CLUB = 2
#    DIAMOND = 3

class Player:
    def __init__(self, id : str):
        self.id = id
        self._card : List[Optional[Tuple[int, int]]] = []
        self._landlord = False
        
    def changeChar(self) -> None:
        self._landlord = not self._landlord
    
    def addCard(self, cards : List[Tuple[int, int]]|Tuple[int, int]) -> None:
        if isinstance(cards[0], Tuple):
            self._card.extend(cards) # pyright: ignore[reportArgumentType]
        else:
            self._card.append(cards) # pyright: ignore[reportArgumentType]
            
    @property
    def cardnum(self) -> int:
        return len(self._card)

class Game:
    _start = False
    _lords : List[Tuple[int, int]] = []
    class类型(Enum):
        SINGLE = 1
        PAIR = 2
        SPRING = 3
        BOMB = 4
        STRAIGHT = 5
        FULLHOUSE = 6
        SPAIRS = 7
        PLANE = 8
        KK = 9
        
    def __init__(self):
        self._player : List[Optional[Player]] = []
        self._ind : List[Optional[int]] = [0] * 4
    
    @property
    def playernum(self) -> int:
        return len(self._player)
    
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
        return self._start
    
    def arrangeCards(self) -> List[Tuple[int, int]]:
        arrangements = CARD # 待添加更新player._card
        shuffle(arrangements)
        self._lords = arrangements[51:]
        return arrangements[:51]
        
    async def isfinished(self) -> Player:
        a : Optional[Player] = None
        while self._start:
            for i in self._player:
                if i and i.cardnum == 0:
                    self._start = False
                    a = i
        return cast(Player, a)
