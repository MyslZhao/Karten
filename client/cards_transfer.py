"""
数据转换类，包括:
+ JSON字符串转Cards数据
+ Cards数据转JSON字符串
"""
from cards_data import Pattern, Cards
import json
from dataclasses import asdict

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。

class CardsTransfer:
    """
    牌型JSON转换单例

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
