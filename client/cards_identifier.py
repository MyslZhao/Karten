"""
牌型识别类，包括:
+ 对客户端的出牌牌型进行判断
+ 识别、打包客户端的合法牌型
"""
from collections import Counter
from typing import List
from cards_data import Pattern, Cards

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。
# XXX: 在下一次可能的更新时，解决R0911、R0912和R0914

class Identifier:
    """
    客户端处的牌型判断单例类
    """

    @classmethod
    def identify(cls, cards : List[List[int]]) -> Cards:
        """
        牌型识别方法(按非qq方规则识别，同时禁止牌型降级使用，确保同一序列只有一种牌型)
        具体的牌型种类见Pattern类


        :param cards: 带识别牌序列
        :type cards: List[List[int]]
        :return: 牌型信息类
        :rtype: Cards
        """
        # BUG: 在可能的更新到来前，对于同一牌型不同形态均取大小最大的

        n = len(cards)
        points = []
        for i in cards:
            points.append(i[1])
        species = set(points)
        s = len(species)
        points.sort()
        match n:
            case 1: # 个子
                return Cards(Pattern.SINGLE, points[0])
            case 2: # 对子、王炸
                if s == 1:
                    return Cards(Pattern.PAIR, points[0])
                elif 14 in points and 15 in points:
                    return Cards(Pattern.KK)
            case 3: # 三张
                if s == 1:
                    return Cards(Pattern.FULLHOUSE, [3, points[0]])
            case 4: # 三带一、炸弹
                if s == 1:
                    return Cards(Pattern.BOMB, points[0])
                elif s == 2 and points[1] == points[2]:
                    return Cards(Pattern.FULLHOUSE, [4, points[1]])
            case 5: # 三带二、顺子
                if s == 2:
                    if not (points[1] == points[2] and points[2] == points[3]):
                        return Cards(Pattern.FULLHOUSE, [5, points[2]])
                elif s == 5:
                    if (points[1] == points[0] + 1 and
                        points[2] == points[1] + 1 and
                        points[3] == points[2] + 1 and
                        points[4] == points[3] + 1) and points[4] not in [
                            13, 14, 15
                            ]:
                        return Cards(Pattern.STRAIGHT, [5, points[4]])
            case _: # 顺子、飞机或者连对
                if n == s and points[-1] not in [13, 14, 15]:
                    for i in range(1, n):
                        if points[i] != points[i - 1] + 1:
                            return Cards(Pattern.NONE)
                    return Cards(Pattern.STRAIGHT, [n, points[-1]])
                dic = Counter(points)
                spairflag = True

                for i, v in dic.items():
                    if v != 2:
                        spairflag = False
                        break

                if spairflag:
                    if 13 in points:
                        return Cards(Pattern.NONE)

                    prev = 0
                    for i, v in dic.items():
                        if prev == 0:
                            prev = i
                            continue
                        if i != prev + 1:
                            return Cards(Pattern.NONE)
                        prev = i
                    return Cards(Pattern.SPAIRS, [n, prev])

                scale = 0
                m = 0
                r = []
                for i, v in dic.items():
                    if v == 3:
                        if i == 13:
                            return Cards(Pattern.NONE)
                        if m < i:
                            m = i
                        scale += 1
                        continue
                    r.extend([i] * v)

                rest = n - scale * 3
                if rest == 0:
                    return Cards(Pattern.PLANE, [scale, 0, m])
                elif rest == scale:
                    return Cards(Pattern.PLANE, [scale, rest, m])
                elif rest != scale * 2:
                    return Cards(Pattern.NONE)

                rc = Counter(r)
                for i, v in rc.items():
                    if v != 2:
                        return Cards(Pattern.NONE)
                return Cards(Pattern.PLANE, [scale, scale * 2, m])
        return Cards(Pattern.NONE)
