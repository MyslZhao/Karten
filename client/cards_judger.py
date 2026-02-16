"""
牌型比较类，包括:
+ 可比较类型判断
+ 值大小判断
"""
# pylint: disable=R0903
# 抑制警告：
# + R0903:类的公共方法太少(小于2)。
from cards_data import Pattern, Cards

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。
# XXX: 在下一次可能的更新时，解决R0911和R0912

class Judger:
    """
    牌型对比单例

    """

    @classmethod
    def compare(cls, a : Cards, b : Cards) -> int:
        """
        比较牌型

        :param a: 上家的出牌牌型(确保绝对非NONE)
        :type a: Cards
        :param b: 本家的选择牌型
        :type b: Cards
        :return: 比较状态码(0为b的牌型非法;1为上家大,无法打出;2为下家打,可以出牌)
        :rtype: int
        """
        if Pattern.KK in [a.pattern, b.pattern]:
            if a.pattern == Pattern.KK:
                return 1
            else:
                return 2

        if Pattern.BOMB in [a.pattern, b.pattern]:
            if len(set([a.pattern, b.pattern])) == 1:
                if isinstance(a.level, int) and isinstance(b.level, int):
                    if a.level > b.level:
                        return 1
                    else:
                        return 2
            else:
                if a.pattern == Pattern.BOMB:
                    return 1
                else:
                    return 2

        if a.pattern != b.pattern:
            return 0

        if a.pattern in [Pattern.STRAIGHT, Pattern.FULLHOUSE, Pattern.SPAIRS]:
            if isinstance(a.level, list) and isinstance(b.level, list):
                if a.level[0] != b.level[0]:
                    return 0

                if a.level[1] >= b.level[1]:
                    return 1
                else:
                    return 2

        if a.pattern == Pattern.PLANE:
            if isinstance(a.level, list) and isinstance(b.level, list):
                if a.level[0] != b.level[0] or a.level[1] != b.level[1]:
                    return 0

                if a.level[2] >= b.level[2]:
                    return 1
                else:
                    return 2

        if isinstance(a.level, int) and isinstance(b.level, int):
            if a.level >= b.level:
                return 1
            else:
                return 2

        return 0
