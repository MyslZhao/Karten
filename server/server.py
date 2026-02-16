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
import asyncio
import os
import sys
import json
from typing import List, cast
from Game import Game, Player
from logger import Logger

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

class Server:
    """
    异步服务器类
    """
    _ready_status = 0
    _MAX_CONNECTIONS = 3
    _current_connections = 0
    _counter_lock = asyncio.Lock()  # 保护计数器
    _writers : List[asyncio.StreamWriter] = []
    _readers : List[asyncio.StreamReader] = []
    _instance = None
    _buffer : str = ''

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
        return len(self._writers)

    async def _game_run(self):
        while True:
            if self._ready_status == 3: # debug: 3-> 1
                if self._ready_status == 1:
                    Logger.write("Single client debug permitted.", t = "DEBUG", thread = "_game_run")
                self._game.start()
                await self.broadcast("b") # -> client.SocketMain._run
                break
            await asyncio.sleep(0.1)

        await asyncio.sleep(1)

        Logger.write("Enter game loop.", t = 'TRACE', thread = "_game_run")
        num_list = []
        for i in range(1, 4):
            num_list.append(self._game.playerlist[
                self._game.playeridlist[i]
            ].cardnum)
        rnd = self._game.lordsid
        while True:
            current_recv = self._readers[rnd - 1]
            if current_recv:
                # 客户id + " " + 出牌数 + " " + 牌型JSON字符串 + "\n"
                deploy_card = (await cast(
                    asyncio.StreamReader,current_recv
                    ).readuntil(b'\n')
                               ).decode("utf-8")
                dec_num = len(eval(deploy_card))
                await self.broadcast(deploy_card)

    async def _client_run(self, reader : asyncio.StreamReader, writer : asyncio.StreamWriter) -> None:
        """
        游戏相关进程

        """
        Logger.write("Game task starts.", thread = "_client_run")

        ready = (await reader.readuntil(b'\n')).decode("utf-8").strip().split() # <- client.welcome_screen

        if ready:
            self._ready_status += 1
            player_id = int(ready[0])
            self._game.addPlayer(Player(ready[0]))

        else:
            raise TimeoutError

        while not self._game.istart:
            await asyncio.sleep(0.1)
            continue
        cl = self._game.arrangeCards()
        Logger.write("All players ready, game starts.", t = "TRACE", thread = "_client_run")

        # 公布地主牌
        Logger.write("Inform lord's cards", thread = "_client_run")
        if self._game.lordscard:
            await self.broadcast(json.dumps(self._game.lordscard)) # -> client.SocketMain._run

        # 分配地主
        Logger.write("Arrange identities.", thread = "_client_run")
        self._game.arrangeIden()
        i = self._game.playeridlist[player_id]
        if i:
            p = self._game.playerlist[i]
        else:
            raise IndexError("The player id is not exist.")
        if p:
            p.addCard(cl[17 * (player_id - 1):player_id * 17])
            writer.write((
                '1\n' if p.identity else '0\n'
                ).encode("utf-8")) # -> client.SocketMian._run
            await writer.drain()
        else:
            raise IndexError("The player of the id is lost.")

        # 发牌
        Logger.write("Arrange cards.", thread = "_client_run")
        if p and p.identity:
            if self._game.lordscard:
                p.addCard(cast(List[List[int]], self._game.lordscard))
            else:
                raise TypeError("Lordscard is not initialtive, please arrangeCards fst.")
        else:
            raise IndexError("The player of the id is lost.")
        writer.write((json.dumps(p.cards) + '\n').encode("utf-8")) # -> client.SocketMain._run
        await writer.drain()

    async def broadcast(self, message : str, sender : asyncio.StreamWriter|None = None) -> None:
        """
        向所有客户端广播消息

        :param message: 广播的信息
        :type message: str
        :param sender: 发送消息的客户端(None即指当服务器发送消息的情况)
        :type sender: asyncio.StreamWriter|None
        """
        for client in self._writers:
            if client != sender:
                client.write((message + '\n').encode("utf-8"))
                await client.drain()
                Logger.write(f"Boardcast message: {message}", t = "TRACE", thread = "lambda/self.boardcast")

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
                Logger.write(f"Connection is full, refuse {addr}.", t = "WARN", thread = "_handle_client")
                writer.write(b"f\n")   # 如果连接数已满，发送"failed"
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

            # 接受连接
            self._current_connections += 1
            self._writers.append(writer)
            self._readers.append(reader)

        try:
            writer.write((str(self._current_connections) + '\n').encode("utf-8"))   # -> client.SocketMain._run
            Logger.write(f'user "{addr}" has joined.')
            await writer.drain()

            await self._client_run(reader, writer)

        except (TimeoutError, ConnectionError) as e:
            Logger.write(f"Connection exception: {e}", t = "WARN", thread = "_handle_client")
        except BaseException as e:
            Logger.write(str(e), t = "ERROR", thread = "_handle_client")
        finally:

            self._writers.remove(writer)
            if not writer.is_closing():
                writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

            Logger.write(f'user "{addr}" exits.', thread = "_handle_client")
            async with self._counter_lock:
                self._current_connections -= 1

            if self._game.istart:
                Logger.write(f'{addr} diconnected during game,resetting game.', t = "WARN", thread = "_handle_client")
                self._game = Game()
                self._ready_status = 0


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
        Logger.write(f"Server starts on {addrs}.")

        # 运行服务器
        async with server:
            await asyncio.gather(server.serve_forever(), self._game_run()) #bug src,待更改

if __name__ == "__main__":
    # test start
    a = Server()
    try:
        asyncio.run(a.main())
    except KeyboardInterrupt:
        Logger.write("Server stops.")
    # test end

Logger.write("")


