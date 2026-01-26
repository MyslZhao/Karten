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
from datetime import datetime

def logger(msg : str, level : str = "log"):
    """
    服务器控制台日志接口

    :param msg: 消息内容
    :level msg: str
    :param level: 消息等级(规定为log, note, warn三种等级)
    :type level: str
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp + f" [{level}] {msg}")

class Server:
    """
    异步服务器类
    """
    _max_connections = 3
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
        self._max_connections = max_connection

    @property
    def current_clients(self) -> int:
        """
        当前客户端的数量

        :return: 当前客户端的数量
        :rtype: int
        """
        return len(self._clients)

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
                client.write(message.encode("utf-8"))
                await client.drain()

    async def _handle_client(self,
                             reader : asyncio.StreamReader,
                             writer : asyncio.StreamWriter
                             ) -> None:
        """
        处理客户端的请求(eq session)

        :param reader: 网络输入流(通常无需手动指定)
        :type reader: asyncio.StreamReader
        :param writer: 网络输出流(通常无需手动指定)
        :type writer: asyncio.StreamWriter
        """
        addr = writer.get_extra_info("peername")

        async with self._counter_lock:
            if self._current_connections >= self._max_connections:
                logger(f"Connection is full, refuse {addr}.", level = "warn")
                writer.write(b"Connection refused: server is full\r\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

            # 接受连接
            self._current_connections += 1
            self._clients.add(writer)

        try:
            writer.write(f"welcome:{len(self._clients)}\r\n".encode("utf-8"))
            logger(f'user "{addr}" has joined.')
            await writer.drain()

            await self.broadcast(f"user:{addr} has joined\r\n", writer)

            while True:
                data = await reader.readline()
                if not data:
                    break

                msg = data.decode("utf-8").strip()
                if msg:
                    logger(f"{addr}:{msg}")
                    await self.broadcast(f"{addr}:{msg}\r\n", writer)

        except Exception as e:
            logger(f"Connection exception: {e}", level = "warn")
        finally:

            self._clients.remove(writer)
            if not writer.is_closing():
                writer.close()
            try:
                await writer.wait_closed()
            except BaseException:
                pass
            logger(f'user "{addr}" exits.')
            async with self._counter_lock:
                self._current_connections -= 1
            await self.broadcast(f"user {addr} left chat.\r\n")

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
        logger(f"Server starts at {addrs}.")

        # 运行服务器
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    # test start
    a = Server()
    try:
        asyncio.run(a.main())
    except KeyboardInterrupt:
        logger("Server stops.")
    # test end
