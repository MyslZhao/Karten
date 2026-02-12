from datetime import datetime

def logger(msg : str, t : str = "INFO", thread : str = "main", pipe : str = "file"):
    """
    客户端日志接口

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
        with open("client.log", "a") as f:
            if msg == "":
                f.write("\n")
            else:
                f.write(timestamp + f" [{thread}] {t} {msg}\n")
