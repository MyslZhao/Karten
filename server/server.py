"""
客户端->异步服务器模块实现，包含了：
+ 控制台日志输出
+ 单例模式的server连接管理类
"""
# pylint: disable=W0221
# pylint: disable=R0903
# pylint: disable=W0603
# pylint: disable=W0718
# 抑制警告：
# + W0221:覆写方法与原方法参数数量不统一/出现不必要的可变参数。
# + R0903:类的公共方法太少(小于2)。
# + W0603:使用了global关键字，pylint不鼓励使用任何的global关键字以在函数内部更改全局变量。
# + W0718:过于宽松的except异常捕获。
from game import Game
import asyncio
import os,sys
from datetime import datetime

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

def logger(msg : str, t : str = "INFO", thread : str = "main", pipe : str = "file"):
    """
    客户端日志接口

    :param msg: 消息内容
    :type msg: str
    :param t: 消息等级(规定为INFO, TRACE, DEBUG, WARN, ERROR五种等级)
    :type t: str
    :param thread: 日志线程([**线程变量名**|**重要函数特称**|[[**lambda**|**协程任务变量名**]/[**方法名**|**self.方法名**]]])
    :type thread: str
    :param pipe: 日志输出管道(规定为cmd, file两种)
    :type pipe: str
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if pipe == "cmd":
        print(timestamp + f" [{thread}] {t} {msg}")
    elif pipe == "file":
        print(timestamp + f" [{thread}] {t} {msg}")
        with open("test_server.log", "a") as f:
            if msg == "":
                f.write("\n")
            else:
                f.write(timestamp + f" [{thread}] {t} {msg}\n")

class server:
    """
    异步服务器类
    """
    _ready_status = 0
    _MAX_CONNECTIONS = 3
    _current_connections = 0
    _counter_lock = asyncio.Lock()  # 保护计数器
    _clients = set()
    _instance = None

    def __new__(cls, *argc, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, addr : str = '0.0.0.0', port : int = 8888, max_connection : int = 3):
        """
        初始化服务器

        :param addr: 服务器地址(默认监听所有可用接口)
        :type addr: str
        :param port: 接口的端口号(默认为8888)
        :type port: int
        :param max_connection: 最大连接数量
        :type max_connection: int
        """
        self._addr = addr
        self._port = port
        self._MAX_CONNECTIONS = max_connection
        self._game = Game()

    @property
    def current_clients(self) -> int:
        """
        当前客户端的数量

        :return: 当前客户端的数量
        :rtype: int
        """
        return len(self._clients)

    async def _game_run(self):
        while True:
            if self._ready_status == 1: # debug: 3-> 1

                logger("Single client debug permitted.", t = "DEBUG", thread = "lambda/self._game_run")
                self._game.start()
                await self.broadcast("begin") # -> client.SocketMain._run(2)
                break
            await asyncio.sleep(0.1)

    async def _client_run(self, reader : asyncio.StreamReader, writer : asyncio.StreamWriter) -> None:
        """
        游戏相关进程

        """
        logger("Game task starts.", thread = "lambda/self._client_run")

        READY = (await reader.readuntil(b'\n')).decode("utf-8").strip() # <- client.welcome_screen

        if READY:
            self._ready_status += 1
            id = int(READY[0])
        else:
            raise TimeoutError

        while not self._game.istart:
            await asyncio.sleep(0.1)
            continue

        logger("All players ready, game starts.", t = "TRACE", thread = "lambda/self._client_run")

        writer.write(str(self._game.arrangeCards()[17 * (id - 1):id * 17]).encode("utf-8")) # -> client.SocketMain._run(3)
        await writer.drain()


    async def broadcast(self, message : str, sender : asyncio.StreamWriter|None = None) -> None:
        """
        向所有客户端广播消息

        :param message: 广播的信息
        :type message: str
        :param sender: 发送消息的客户端(None即指当服务器发送消息的情况)
        :type sender: asyncio.StreamWriter|None
        """
        for client in self._clients:
            if client != sender:
                client.write((message + '\n').encode("utf-8"))
                await client.drain()
                logger(f"Boardcast message: {message}", t = "TRACE", thread = "lambda/self.boardcast")

    async def _handle_client(self, reader : asyncio.StreamReader, writer : asyncio.StreamWriter) -> None:
        """
        处理客户端的请求(eq session)

        :param reader: 网络输入流(通常无需手动指定)
        :type reader: asyncio.StreamReader
        :param writer: 网络输出流(通常无需手动指定)
        :type writer: asyncio.StreamWriter
        """
        addr = writer.get_extra_info("peername")

        async with self._counter_lock:
            if self._current_connections >= self._MAX_CONNECTIONS:
                logger(f"Connection is full, refuse {addr}.", t = "WARN")
                writer.write(b"failed\n")   # 如果连接数已满，发送"failed"
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

            # 接受连接
            self._current_connections += 1
            self._clients.add(writer)

        try:
            writer.write((str(self._current_connections) + '\n').encode("utf-8"))   # -> client.SocketMain._run(1)
            logger(f'user "{addr}" has joined.')
            await writer.drain()

            await self._client_run(reader, writer)

        except Exception as e:
            logger(f"Connection exception: {e}", t = "WARN")
        finally:

            self._clients.remove(writer)
            if not writer.is_closing():
                writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

            logger(f'user "{addr}" exits.')
            async with self._counter_lock:
                self._current_connections -= 1
            await self.broadcast(f"user {addr} left.\n")

    async def reset(self) -> None:
        """
        发生错误时重置服务器操作

        """
        logger("Unexpected client error occurred, server resetting.", t = "WARN", thread = "lambda/self.reset")
        pass # 待完善

    async def main(self) -> None:
        """
        服务器主程序
        """
        server = await asyncio.start_server(
            self._handle_client,
            self._addr,  # 监听所有网络接口
            self._port
        )

        # 获取服务器地址
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logger(f"Server starts on {addrs}.")

        # 运行服务器
        async with server:
            await asyncio.gather(server.serve_forever(), self._game_run()) #bug src,待更改

if __name__ == "__main__":
    # test start
    a = server()
    try:
        asyncio.run(a.main())
    except KeyboardInterrupt:
        logger("Server stops.")
    # test end

logger("")

