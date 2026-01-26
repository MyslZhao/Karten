import random
from typing import List,Dict,Tuple,Optional,Any
from enum import Enum
import time
#=============================================
#基础数据结构
#=============================================
class Card:
    """牌类"""
    def __init__(self,card_id:int=0):
        self.id=card_id
        if card_id<0 or card_id>53:
            print("错误！")
            return
        if card_id==52:
            #小王
            self.suit=0 #只有♠️
            self.value=16
            self.weight=16
        elif card_id==53:
            #大王
            self.suit=0
            self.value=17
            self.weight=17
        else:
            #普通牌
            self.suit=card_id//13
            self.value=3+(card_id%13)
            self.weight=self.value
        def get_name(self)->str:
            """获取牌名"""
            suit_names={
                0:"♠️",1:"♥️",2:"♣️",3:"♦️"
            }
            value_names={
                3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"J",12:"Q",13:"K",14:"A",15:"2",16:"小王",17:"大王"
            }
            if self.value>=16:
                return value_names.get(self.value,"?")
            suit_str=suit_names.get(self.value,"?")
            value_str=value_names.get(self.value,"?")
            return value_str+suit_str
        def __str__(self)->str:
            return self.get_name()
        def __lt__(self,other:'Card')->bool:
            return self.weight<other.weight
        def __eq__(self,other:'Card')->bool:
            return self.id==other.id
        

        





