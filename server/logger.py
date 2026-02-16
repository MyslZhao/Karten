"""
日志管理类，包括:
+ 基本的控制台日志功能
+ 日志文件写入功能
"""
from datetime import datetime

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。
# XXX: 在下一次可能的更新时，解决R0903。

class Logger:
    """
    服务器日志管理类(在可能的更新中，可能会加新功能)

    """
    @classmethod
    def write(cls, msg : str, t : str = "INFO", thread : str = "main", pipe : str = "file") -> None:
        """
        服务器日志写入接口

        :param msg: 消息内容
        :type msg: str
        :param t: 消息等级(规定为INFO, TRACE, WARN, ERROR四种等级)
        :type t: str
        :param thread: 日志线程
        :type thread: str
        :param pipe: 日志输出管道(规定为cmd, file两种)
        :type pipe: str
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if pipe == "cmd":
            print(timestamp + f" [{thread}] {t} {msg}")
        elif pipe == "file":
            with open("serevr.log", "a", encoding = "utf-8") as f:
                if msg == "":
                    f.write("\n")
                else:
                    f.write(timestamp + f" [{thread}] {t} {msg}\n")
