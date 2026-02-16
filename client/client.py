"""
客户端程序，包含了：
+ 各个界面的pygame func
+ UI/Sock双线程
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
from typing import Tuple, Callable, Optional, List
from socket import IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_KEEPALIVE
import os
import sys
import asyncio
import pygame
import json
from cards_identifier import Identifier
from cards_judger import Judger
from ui_component import *

from logger import Logger

# -*- encoding: utf-8 -*-

# TODO: interface with server
# TODO: design the game_surface

ID = 0
IDENTITY = 0
CARD_QUEUE : List[Optional[Tuple[int, int]]] = []
LORD_QUEUE : List[Optional[Tuple[int, int]]] = []

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

# UI界面设计
def welcome_screen(surface: pygame.Surface, ui_main : "UIMain", sk_main : "SocketMain") -> None:
    """
    欢迎界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param sk_main: 异步通信类
    :type sk_main: SocketMain
    """
    def start_buttons_job(_button : InteractorArea):
        """
        start_button绑定的方法
        """
        asyncio.create_task(sk_main.send("1")) # -> server.server._client_run
        ui_main.switch_surfunc(waiting_screen)

    if ui_main.interactors_emp:# 交互组件事件注册
        # 主Frame按钮注册
        start_button = BUTTONFACTORY.construct((520, 360),
                                            (240, 60),
                                            Text("开始",
                                                    "src\\fonts\\MicrosoftYaHei.ttf",
                                                    18
                                                    ),
                                            border = Border(Color(0, 0, 0), 1)
                                            )
        start_button.bind(start_buttons_job)
        ui_main.add_interactors(start_button)
    # 窗口背景载入
    welcome_bg = pygame.image.load("src\\bg\\welcome_bg.jpg")
    surface.blit(welcome_bg, (0, 0))
    # 主Frame背景载入
    BOARDFACTORY.construct(Coord(360, 150),
                                         Size(560, 420),
                                         Color(255, 255, 255),
                                         apparency = 240,
                                         border = Border(
                                             Color(0, 0, 0),
                                             0
                                             )
                                         ).draw(surface)
    # 主Frame标题载入
    LABELFACTORY.construct(Text("斗地主",
                                             "src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf",
                                             70
                                             ),
                                       (400, 200),
                                       (480, 120),
                                       bg_apparent = True
                                       ).draw(surface)

def waiting_screen(surface : pygame.Surface, _ui_main : "UIMain", _sk_main: "SocketMain") -> None:
    """
    等待连接界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param sk_main: 异步通信类
    :type sk_main: SocketMain
    """
    # 窗口背景载入
    waiting_bg = pygame.image.load("src\\bg\\welcome_bg.jpg")
    surface.blit(waiting_bg, (0, 0))
    # 主Frame背景载入
    BOARDFACTORY.construct(Coord(360, 150),
                                           Size(560, 420),
                                           Color(255, 255, 255),
                                           apparency = 240,
                                           border = Border(
                                               Color(0,0,0),
                                               0
                                               )
                                           ).draw(surface)
    # 主Farme说明文本载入
    LABELFACTORY.construct(Text("等待其他玩家...",
                                               "src\\fonts\\MicrosoftYaHei.ttf",
                                               70
                                               ),
                                          (400, 200),
                                          (480, 120),
                                          bg_apparent = True,
                                          border = Border(Color(255, 255, 255), 1)
                                          ).draw(surface)

def game_screen(surface: pygame.Surface, ui_main : "UIMain", sk_main : "SocketMain") -> None:
    """
    游戏界面 待添加

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param sk_main: 异步通信类
    :type sk_main: SocketMain
    """

    global CARD_QUEUE
    Logger.write("Rendering game_screen.", t = "TRACE", thread = "game_screen/self._surfunc")

    game_bg = pygame.image.load("src\\bg\\game_bg.jpg")
    surface.blit(game_bg, (0, 0))

    while not CARD_QUEUE:
        waiting_text = LABELFACTORY.construct(
            Text("等待发牌...", "src\\fonts\\MicrosoftYaHei.ttf", 36),
            (500, 300),
            (280, 50),
            bg_apparent=True
        )
        waiting_text.draw(surface)
        return

# 客户端主程序
TESTADDR = ("127.0.0.1", 8888)

class UIMain():
    """
    ui主程序，主管ui绘制
    """
    _screen : pygame.Surface
    _interactors : List[Optional[InteractorArea]] = []
    def __init__(self,
                 start_surfunc : Callable[[pygame.Surface, "UIMain", "SocketMain"], None],
                 socket_main : "SocketMain"
                 ):
        """
        用一个界面方法初始化一个UIMain对象

        :param start_surfunc: 初始界面((pygame.Surface) -> None)
        :type start_surfunc: Callable[[pygame.Surface], None]
        """
        self._socket_main : Optional[SocketMain] = socket_main
        self._surfunc : Callable[[pygame.Surface, UIMain, SocketMain], None] = start_surfunc

    @property
    def interactors_emp(self) -> bool:
        """
        返回注册的交互事件是否为空

        :return: 注册的交互事件是否为空
        :rtype: bool
        """
        return len(self._interactors) == 0

    def add_interactors(self, interactor : InteractorArea) -> None:
        """
        注册新的交互事件

        :param interactor: 交互事件所属的交互组件
        :type interactor: InteractorArea
        """
        self._interactors.append(interactor)

    def clear_interactors(self) -> None:
        """
        清除不再需要的交互事件

        """
        self._interactors.clear()

    def switch_surfunc(self, new_surfunc : Callable[[pygame.Surface, "UIMain", "SocketMain"], None]) -> None:
        """
        切换界面方法

        :param new_surfunc: 新的界面((pygame.Surface) -> None)
        :type new_surfunc: Callable[[pygame.Surface], None]
        """
        self.clear_interactors()
        self._surfunc : Callable[[pygame.Surface, UIMain, SocketMain], None] = new_surfunc

    async def _run(self) -> None:
        """
        UIMain主要运行逻辑

        """
        pygame.font.init()
        pygame.init()
        self._screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("斗地主")
        Logger.write("Entering render loop", thread = "UI_MAIN")
        try:
            while True:
                events = pygame.event.get()
                for e in events:
                    if e.type == pygame.QUIT:
                        Logger.write("Client quit.", t = "TRACE", thread = "UI_MAIN")
                        return
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            Logger.write("Client quit.", t = "TRACE", thread = "UI_MAIN")
                            return

                    for itactor in self._interactors:
                        if itactor and itactor.handle_events(e):
                            break

                self._screen.fill((255, 255, 255))
                # ui 绘制 start
                if self._surfunc and self._socket_main:
                    self._surfunc(self._screen, self, self._socket_main)
                # ui 绘制 end

                for itactor in self._interactors:
                    if itactor:
                        itactor.draw(self._screen)

                pygame.display.flip()

                await asyncio.sleep(1/60)

        except KeyboardInterrupt as e:
            Logger.write(f"Exception occurred: {e}", t = "ERROR", thread = "UI_MAIN")
            print(f"程序异常: {e}")
        finally:
            # 确保资源被正确释放
            pygame.quit()

    async def start(self) -> None:
        """
        转入self._run运行

        """
        Logger.write("UI starts", t = "INFO", thread = "UI_MAIN")
        await self._run()



class SocketMain():
    """
    线程socket_thread负责的socket主程序，负责与server交换数据
    """
    id = "0"
    _ui_main : Optional[UIMain]

    def __init__(self, addr : Tuple[str, int]):
        self._addr = addr
        self._listenmsg = asyncio.Queue()
        self._sendmsg = asyncio.Queue()
        self._reader : Optional[asyncio.StreamReader] = None
        self._writer : Optional[asyncio.StreamWriter] = None
        self._connected : bool = False

    def set_ui(self, ui_main : UIMain) -> None:
        """
        延迟引用ui_main

        :param ui_main: 渲染类对象
        :type ui_main: UIMain
        """
        self._ui_main = ui_main

    async def _connect(self, timeout: float = 5.0) -> bool:
        """
        异步连接

        :param timeout: 超时时限
        :type timeout: float
        :return: 连接状态
        :rtype: bool
        """
        Logger.write("Start connect tasks.", thread="lambda/self._connect")

        try:
            Logger.write("Connecting...", thread="lambda/self._connect")
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host = self._addr[0],
                    port = self._addr[1]
                    ),
                timeout = timeout
            )

            peername = self._writer.get_extra_info('peername')
            if peername:
                Logger.write(f'Connection ready, server at {peername}', thread = 'lambda/self._connect')

            sock = self._writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1) # 禁用Nagle
                sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1) # 启用保活

            return True

        except (ConnectionError, OSError, asyncio.TimeoutError) as e:
            Logger.write(f"Connection failed: {e}", thread="lambda/self._connect")
            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:
                    pass
                finally:
                    self._writer = None
                    self._reader = None
            return False

        except Exception as e:
            Logger.write(f"Unexpected error during connection: {e}",
                   t="ERROR",
                   thread="lambda/self._connect")

            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass
                self._writer = None
                self._reader = None
            return False

    async def _send(self) -> None:
        """
        发送协程

        """
        Logger.write("Send tasks loops.", thread = "send_task/self._send")

        while True:
            try:
                msg = await self._sendmsg.get()
                Logger.write(f"Message '{msg}' ready to be sent.", t = "TRACE", thread = "send_task/self._send")

                if self._writer and not self._writer.is_closing():
                    self._writer.write(msg.encode('utf-8'))
                    await self._writer.drain()
                    Logger.write(f"Message {msg} has been sent.", t = "TRACE", thread = "send_task/self._send")
                else:
                    Logger.write(f'Writer failed, plz check the status of self._writer.', t = "WARN", thread = "send_task/self._send")

                self._sendmsg.task_done()

            except (ConnectionError, OSError, BrokenPipeError) as e:
                Logger.write(str(e), t = "ERROR", thread = "send_task/self._send")
                raise
            except asyncio.CancelledError as e:
                Logger.write(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                raise

    async def _listen(self) -> None:
        """
        监听协程

        """
        Logger.write("Listen task loops", thread = "listen_task/self._listen")

        while True:
            try:
                data = b''
                if self._reader:
                    data = await self._reader.readuntil(b'\n')

                msg = data.decode("utf-8").strip()

                if msg == "":
                    await asyncio.sleep(0.1)
                    continue
                Logger.write(f'msg : "{msg}" received',
                             t = "TRACE",
                             thread = "listen_task/self._listen")

                await self._listenmsg.put(msg)

            except (asyncio.IncompleteReadError, ConnectionError, OSError) as e:
                Logger.write(str(e), t = "ERROR", thread = "listen_task/self._listen")
                raise
            except asyncio.CancelledError as e:
                Logger.write(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                raise

    async def recv(self, t: int = 1) -> str:
        """
        从接受消息队列读取消息

        :param t: 接受时限(默认1s)
        :type t: int
        :return: 接受到的消息
        :rtype: str
        """
        try:
            msg = await asyncio.wait_for(
                self._listenmsg.get(),
                timeout = t
            )
            return msg

        except asyncio.TimeoutError:
            return ""

    async def send(self, msg : str) -> None:
        """
        发送消息，
        将消息送入发送序列

        :param msg: 要发送的消息
        :type msg: str
        """
        await self._sendmsg.put(str(self.id) + " " + msg + '\n')

    async def _run(self) -> None:
        """
        客户端游戏逻辑的socket逻辑 待完善

        """
        global CARD_QUEUE, LORD_QUEUE, IDENTITY, ID
        Logger.write("Game task starts.", thread = "game_task/self._run")

        connect_status = await self.recv() # <- server.server._handle_client
        if connect_status == "":
            Logger.write("Connection timeout.", t = "WARN", thread = "game_task/self._run")
            return
        if connect_status == "f":
            Logger.write("Connection already full.", t = "WARN", thread = "game_task/self._run")
            return
        ID = int(connect_status)
        self.id = connect_status
        Logger.write(f"Connected successfully, id is {id}.", thread = "game_task/self._run")

        ifbegin = await self.recv() # <- server.server._game_run

        if ifbegin:
            if ifbegin != "b":
                return

        Logger.write("Game started.", t = "TRACE", thread = "game_task/self._run")
        if self._ui_main:
            self._ui_main.switch_surfunc(game_screen)

        LORD_QUEUE = json.loads(await self.recv()) # <- server.server._client_run
        IDENTITY = int(await self.recv()) # <- serevr.Server._client_run
        CARD_QUEUE = json.loads(await self.recv()) # <- server.server._client_run

    async def start(self) -> None:
        """
        socket总逻辑管理

        """
        send_task = listen_task = game_task = None
        try:
            Logger.write("Socket starts", thread = "SOCKET_MAIN")

            result = await self._connect()
            if not result:
                raise TimeoutError("Connection timeout.")
            Logger.write("Connection established.", thread = "SOCKET_MAIN")

            send_task = asyncio.create_task(self._send())
            listen_task = asyncio.create_task(self._listen())
            game_task = asyncio.create_task(self._run())

            Logger.write("All socket tasks started.", thread = "SOCKET_MAIN")
            await asyncio.gather(send_task, listen_task, game_task)

        except asyncio.CancelledError as e:
            Logger.write(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            raise

        except TimeoutError as e:
            Logger.write(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            raise

        except Exception as e:
            Logger.write(str(e), t = "ERROR", thread = "SOVKET_MAIN")
            raise

        finally:
            for task in (send_task, listen_task, game_task):
                if task and not task.done():
                    task.cancel()

            if self._writer and not self._writer.is_closing():
                try:
                    self._writer.close()
                except Exception:
                    pass


            Logger.write("Socket close, SOCKET_MAIN finished!", thread = "SOCKET_MAIN")

async def main():
    """
    主函数
    """
    socket_main = SocketMain(TESTADDR)
    ui_main = UIMain(welcome_screen, socket_main)
    socket_main.set_ui(ui_main)
    ui_task = asyncio.create_task(ui_main.start(), name = "UI")
    socket_task = asyncio.create_task(socket_main.start(), name = "Socket")

    done, pending = await asyncio.wait(
        [ui_task, socket_task],
        return_when = asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    for task in done:
        try:
            task.result()
        except Exception as e:
            Logger.write(f"Task {task.get_name} failed: {e}", t = "ERROR", thread = "Moudel/main")

asyncio.run(main())

Logger.write("")
