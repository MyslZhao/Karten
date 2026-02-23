"""
数据转换类，包括:
+ JSON字符串转Cards数据
+ Cards数据转JSON字符串
"""
import json
from typing import Tuple, List
from dataclasses import asdict
from cards_data import Pattern, Cards

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。

# 牌型信息构造规则
# 牌型发起者id_接收者id_出牌数_牌型JSON数据_原序列

class CardsTransfer:
    """
    牌型传输数据转换类

    """
    @classmethod
    def encoson(cls, send_cards : Cards) -> str:
        """
        把Cards数据转为JSON数据字符串

        :param sendCards: 要发送的Cards数据类
        :type sendCards: Cards
        :return: JSON字符串
        :rtype: str
        """
        data_dict = asdict(send_cards)
        data_dict['pattern'] = send_cards.pattern.name
        return json.dumps(data_dict)

    @classmethod
    def decoson(cls, recv_cards : str) -> Cards:
        """
        把JSON数据字符串转为Cards数据

        :param recvCards: 接收的JSON数据
        :type recvCards: str
        :return: Cards数据类
        :rtype: Cards
        """
        data_dict = json.loads(recv_cards)
        data_dict['pattern'] = Pattern[data_dict['pattern']]
        return Cards(**data_dict)

    @classmethod
    def parsetotuple(cls, src_str : str
                     ) -> Tuple[int, int, int, Cards, List[Tuple[int, int]]]:
        """牌型传递字符串转tuple组

        :param src_str: 牌型传递串
        :type src_str: str
        :return: Tuple信息组
        :rtype: Tuple[int, int, int, Cards, List[Tuple[int, int]]]
        """
        try:
            things = src_str.split(" ")
            sender = int(things[0])
            recver = int(things[1])
            sd_dec = int(things[2])
            msg = cls.decoson(things[3])
            src_list = json.loads(things[4])
            return (sender,
                    recver,
                    sd_dec,
                    msg,
                    src_list)

        except ValueError as e:
            print(f"Sender error: {e}")
            return (
                            0, 0, 0,
                            Cards(Pattern.NONE, None),
                            [(-1, -1)]
                        )

        except IndexError as e:
            print(f"Sender error: {e}")
            return (
                            0, 0, 0,
                            Cards(Pattern.NONE, None),
                            [(-1, -1)]
                        )

    @classmethod
    def covercode(cls,
                  player_id : int,
                  cards_num : int,
                  send_cards : Cards,
                  src_list : List[Tuple[int, int]]
                  ) -> str:
        """发起新的牌型传递

        :param player_id: 玩家id
        :type player_id: int
        :param cards_num: 发送牌数
        :type cards_num: int
        :param send_cards: 要发送的Card数据类
        :type send_cards: Cards
        :param src_list: 原序列
        :type src_list: List[Tuple[int, int]]
        :return: 构造出的牌型传输字符串
        :rtype: str
        """
        cache = cls.encoson(send_cards)
        src_str = json.dumps(src_list)
        return f"{player_id} {(player_id % 3) + 1} {cards_num} {cache} {src_str}"

    @classmethod
    def passcode(cls,
                 old_str : str
                 ) -> str:
        """传递牌型

        :param old_str: 接收传递牌型串
        :type old_str: str
        :return: 待发送传递串
        :rtype: str
        """
        i = old_str.split(" ")
        next_id = (int(i[1]) % 3) + 1
        return f"{i[0]} {next_id} {0} {i[3]} {i[4]}"
